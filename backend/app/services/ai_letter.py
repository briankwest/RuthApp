"""
AI Letter Writer Service
Adapted from the original ai_writer.py for web API usage
"""
import os
import logging
import json
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import uuid
import httpx
import trafilatura
from bs4 import BeautifulSoup
from newspaper import Article
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.letter import (
    Letter, LetterRecipient, NewsArticle, UserWritingProfile,
    LetterStatus, DeliveryMethod
)
from app.models.user import User
from app.models.geocoding import Representative

logger = logging.getLogger(__name__)


class NewsArticleFetcher:
    """Fetches and extracts content from news articles"""

    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            },
            timeout=30.0
        )

    async def fetch_article(self, url: str, db: Optional[AsyncSession] = None) -> Dict[str, str]:
        """Fetch and extract article content from a URL"""
        try:
            # Check cache first if database is available
            if db:
                result = await db.execute(
                    select(NewsArticle).where(NewsArticle.url == url)
                )
                cached_article = result.scalar_one_or_none()

                if cached_article and not cached_article.is_expired():
                    logger.info(f"Using cached article for: {url}")
                    return {
                        'url': cached_article.url,
                        'title': cached_article.title,
                        'text': cached_article.content,
                        'authors': cached_article.authors or 'Unknown',
                        'publish_date': str(cached_article.publish_date) if cached_article.publish_date else 'Unknown',
                        'summary': cached_article.summary or '',
                        'source': cached_article.source or self._extract_source(url)
                    }

            logger.info(f"Fetching article from: {url}")

            # Method 1: Try newspaper3k first
            try:
                article = Article(url)
                article.download()
                article.parse()

                if article.text:
                    article_data = {
                        'url': url,
                        'title': article.title or 'Untitled',
                        'text': article.text,
                        'authors': ', '.join(article.authors) if article.authors else 'Unknown',
                        'publish_date': str(article.publish_date) if article.publish_date else 'Unknown',
                        'summary': article.summary if hasattr(article, 'summary') else article.text[:500],
                        'source': self._extract_source(url)
                    }

                    # Cache the article
                    if db:
                        await self._cache_article(db, article_data, 'newspaper3k')

                    return article_data
            except:
                pass

            # Method 2: Fallback to trafilatura
            response = await self.client.get(url)
            response.raise_for_status()

            extracted = trafilatura.extract(
                response.text,
                include_comments=False,
                include_tables=False,
                deduplicate=True
            )

            if extracted:
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.find('title').text.strip() if soup.find('title') else 'Untitled'

                article_data = {
                    'url': url,
                    'title': title,
                    'text': extracted,
                    'authors': 'Unknown',
                    'publish_date': 'Unknown',
                    'summary': extracted[:500] + '...' if len(extracted) > 500 else extracted,
                    'source': self._extract_source(url)
                }

                # Cache the article
                if db:
                    await self._cache_article(db, article_data, 'trafilatura')

                return article_data

            # Method 3: Basic HTML extraction
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for element in soup(['script', 'style']):
                element.decompose()

            # Get text
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            title = soup.find('title').text.strip() if soup.find('title') else 'Untitled'

            article_data = {
                'url': url,
                'title': title,
                'text': text[:5000],  # Limit to first 5000 chars
                'authors': 'Unknown',
                'publish_date': 'Unknown',
                'summary': text[:500] + '...' if len(text) > 500 else text,
                'source': self._extract_source(url)
            }

            # Cache the article
            if db:
                await self._cache_article(db, article_data, 'beautifulsoup')

            return article_data

        except Exception as e:
            logger.error(f"Error fetching article from {url}: {e}")
            return {
                'url': url,
                'title': 'Error fetching article',
                'text': f'Could not fetch article: {str(e)}',
                'authors': 'Unknown',
                'publish_date': 'Unknown',
                'summary': '',
                'source': self._extract_source(url)
            }

    async def _cache_article(self, db: AsyncSession, article_data: Dict, method: str):
        """Cache an article in the database"""
        try:
            from datetime import timedelta

            article = NewsArticle(
                id=uuid.uuid4(),
                url=article_data['url'],
                title=article_data['title'],
                content=article_data['text'],
                authors=article_data.get('authors'),
                publish_date=datetime.utcnow() if article_data['publish_date'] == 'Unknown' else None,
                summary=article_data.get('summary'),
                source=article_data.get('source'),
                extraction_method=method,
                extracted_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=7)  # Cache for 7 days
            )
            db.add(article)
            await db.commit()
            logger.info(f"Cached article: {article_data['url']}")
        except Exception as e:
            logger.warning(f"Could not cache article: {e}")
            await db.rollback()

    def _extract_source(self, url: str) -> str:
        """Extract source domain from URL"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            return domain.replace('www.', '')
        except:
            return 'Unknown'

    async def fetch_multiple_articles(self, urls: List[str], db: Optional[AsyncSession] = None) -> List[Dict[str, str]]:
        """Fetch multiple articles concurrently"""
        import asyncio
        tasks = [self.fetch_article(url, db) for url in urls]
        articles = await asyncio.gather(*tasks)
        return articles

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class VoiceAnalyzer:
    """Analyzes user writing samples to create a voice profile"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def analyze_writing_samples(self, samples: List[str]) -> Dict[str, Any]:
        """Analyze writing samples to extract voice characteristics"""
        try:
            combined_samples = "\n\n---\n\n".join(samples[:5])  # Limit to 5 samples

            prompt = """Analyze these writing samples and extract the author's voice characteristics:

Writing Samples:
{samples}

Please provide:
1. Tone attributes (e.g., formal, casual, urgent, passionate)
2. Style attributes (e.g., direct, diplomatic, emotional, analytical)
3. Vocabulary level (simple, standard, advanced)
4. Common phrases or patterns
5. Key themes or issues they care about
6. Overall writing personality description

Format as JSON with keys: tone_attributes, style_attributes, vocabulary_level, signature_phrases, key_themes, personality_description"""

            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an expert writing analyst."},
                    {"role": "user", "content": prompt.format(samples=combined_samples)}
                ],
                "temperature": 0.3
            }

            # Only add response_format if model supports it (not o1 models)
            if not self.model.startswith("o1"):
                request_params["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(**request_params)

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Error analyzing writing samples: {e}")
            return {
                "tone_attributes": {"professional": 0.8, "formal": 0.6},
                "style_attributes": {"balanced": 0.8, "clear": 0.7},
                "vocabulary_level": "standard",
                "signature_phrases": [],
                "key_themes": [],
                "personality_description": "Standard professional voice"
            }

    async def generate_voice_prompt(self,
                                   writing_profile: UserWritingProfile,
                                   analysis: Optional[Dict] = None) -> str:
        """Generate a comprehensive system prompt for AI based on voice profile"""

        # If no analysis provided, use stored attributes
        if not analysis:
            analysis = {
                "tone_attributes": writing_profile.tone_attributes or {"professional": 0.8},
                "style_attributes": writing_profile.style_attributes or {"balanced": 0.8},
                "vocabulary_level": writing_profile.vocabulary_level or "standard",
                "signature_phrases": writing_profile.signature_phrases or [],
                "personality_description": writing_profile.description or "Professional voice"
            }

        # Convert tone and style attributes to strings (handle both dict and legacy list format)
        tone_attrs = analysis.get('tone_attributes', {})
        if isinstance(tone_attrs, dict):
            tone_str = ', '.join(tone_attrs.keys())
        else:
            # Legacy list format
            tone_str = ', '.join(tone_attrs) if tone_attrs else 'professional'

        style_attrs = analysis.get('style_attributes', {})
        if isinstance(style_attrs, dict):
            style_str = ', '.join(style_attrs.keys())
        else:
            # Legacy list format
            style_str = ', '.join(style_attrs) if style_attrs else 'balanced'

        # Build the comprehensive voice prompt
        prompt_parts = [
            f"You are writing as {writing_profile.name}, with the following comprehensive voice profile:",
            f"\n=== PERSONALITY & STYLE ===",
            f"Description: {analysis.get('personality_description', writing_profile.description)}",
            f"Tone: {tone_str}",
            f"Style: {style_str}",
            f"Vocabulary: {analysis.get('vocabulary_level', 'standard')} level"
        ]

        # Writing samples - provide actual examples of the user's writing
        if writing_profile.writing_samples and len(writing_profile.writing_samples) > 0:
            prompt_parts.append(f"\n=== WRITING SAMPLES (Your Voice Examples) ===")
            prompt_parts.append("Study these examples of your past writing to match the voice, tone, and style:")
            for idx, sample in enumerate(writing_profile.writing_samples[:3], 1):  # Limit to first 3 to avoid token overload
                # Truncate very long samples
                truncated_sample = sample[:500] + "..." if len(sample) > 500 else sample
                prompt_parts.append(f"\nExample {idx}:")
                prompt_parts.append(f'"{truncated_sample}"')
            prompt_parts.append("\nMimic the writing style, sentence structure, and vocabulary patterns from these examples.")

        # Political leaning
        if writing_profile.political_leaning:
            prompt_parts.append(f"\nPolitical Perspective: {writing_profile.political_leaning}")

        # Core values
        if writing_profile.core_values and len(writing_profile.core_values) > 0:
            prompt_parts.append(f"\n=== CORE VALUES ===")
            prompt_parts.append(f"Your advocacy is guided by these principles: {', '.join(writing_profile.core_values)}")
            prompt_parts.append("Let these values subtly inform your arguments and perspective.")

        # Issue positions - organize by priority
        if writing_profile.issue_positions and len(writing_profile.issue_positions) > 0:
            prompt_parts.append(f"\n=== ISSUE POSITIONS ===")

            # Separate by priority
            critical_issues = []
            high_issues = []
            other_issues = []

            for issue_key, issue_data in writing_profile.issue_positions.items():
                priority = issue_data.get('priority', 'medium')
                position = issue_data.get('position', '').replace('_', ' ')
                personal = issue_data.get('personal_connection', '')

                issue_name = issue_key.replace('_', ' ').title()
                issue_line = f"- {issue_name}: {position}"
                if personal:
                    issue_line += f" (Personal: {personal})"

                if priority == 'critical':
                    critical_issues.append(issue_line)
                elif priority == 'high':
                    high_issues.append(issue_line)
                else:
                    other_issues.append(issue_line)

            if critical_issues:
                prompt_parts.append("Critical Priority Issues:")
                prompt_parts.extend(critical_issues)
            if high_issues:
                prompt_parts.append("High Priority Issues:")
                prompt_parts.extend(high_issues)
            if other_issues:
                prompt_parts.append("Other Important Issues:")
                prompt_parts.extend(other_issues)

        # Abortion position (if specified)
        if writing_profile.abortion_position:
            prompt_parts.append(f"\nAbortion Rights Position: {writing_profile.abortion_position.replace('_', ' ')}")

        # Argumentative frameworks
        if writing_profile.argumentative_frameworks:
            active_frameworks = [k.replace('_', ' ').title() for k, v in writing_profile.argumentative_frameworks.items() if v]
            if active_frameworks:
                prompt_parts.append(f"\n=== ARGUMENTATIVE APPROACH ===")
                prompt_parts.append(f"Build your arguments using these frameworks: {', '.join(active_frameworks)}")

                # Detailed instructions per framework
                framework_details = []
                if writing_profile.argumentative_frameworks.get('constitutional'):
                    framework_details.append("- Reference constitutional principles, rights, and legal precedents")
                if writing_profile.argumentative_frameworks.get('moral_ethical'):
                    framework_details.append("- Appeal to moral values, ethics, and what is right")
                if writing_profile.argumentative_frameworks.get('economic'):
                    framework_details.append("- Emphasize fiscal impact, economic benefits/costs, and financial responsibility")
                if writing_profile.argumentative_frameworks.get('future_generations'):
                    framework_details.append("- Consider long-term consequences and impact on future generations")
                if writing_profile.argumentative_frameworks.get('practical_evidence'):
                    framework_details.append("- Use data, research, and real-world evidence")
                if writing_profile.argumentative_frameworks.get('personal_stories'):
                    framework_details.append("- Include personal anecdotes and human impact stories")

                if framework_details:
                    prompt_parts.extend(framework_details)

        # Content preferences
        content_prefs = []
        if writing_profile.include_personal_stories:
            content_prefs.append("Include relevant personal anecdotes when appropriate")
        if writing_profile.include_data_statistics:
            content_prefs.append("Support arguments with data and statistics")
        if writing_profile.include_emotional_appeals:
            content_prefs.append("Include emotional appeals to connect with the reader")
        if writing_profile.include_constitutional_arguments:
            content_prefs.append("Reference constitutional principles when relevant")

        if content_prefs:
            prompt_parts.append(f"\n=== CONTENT PREFERENCES ===")
            for pref in content_prefs:
                prompt_parts.append(f"- {pref}")

        # Regional context
        if writing_profile.regional_context:
            community_type = writing_profile.regional_context.get('community_type', '')
            state_concerns = writing_profile.regional_context.get('state_concerns', '')

            if community_type or state_concerns:
                prompt_parts.append(f"\n=== REGIONAL CONTEXT ===")
                if community_type:
                    prompt_parts.append(f"Community Type: {community_type}")
                    prompt_parts.append(f"Frame issues in terms relevant to {community_type} communities")
                if state_concerns:
                    prompt_parts.append(f"State/Local Concerns: {state_concerns}")

        # Representative engagement strategy (to be applied dynamically based on recipient)
        if writing_profile.representative_engagement:
            prompt_parts.append(f"\n=== ENGAGEMENT STRATEGY ===")
            aligned = writing_profile.representative_engagement.get('aligned_approach', '')
            opposing = writing_profile.representative_engagement.get('opposing_approach', '')
            bipartisan = writing_profile.representative_engagement.get('bipartisan_framing', '')

            if aligned:
                prompt_parts.append(f"With aligned representatives: {aligned.replace('_', ' ')}")
            if opposing:
                prompt_parts.append(f"With opposing representatives: {opposing.replace('_', ' ')}")
            if bipartisan:
                prompt_parts.append(f"Bipartisan framing: {bipartisan.replace('_', ' ')}")

        # Compromise positioning
        if writing_profile.compromise_positioning:
            incremental = writing_profile.compromise_positioning.get('incremental_progress', '')
            bipartisan_pref = writing_profile.compromise_positioning.get('bipartisan_preference', '')

            if incremental or bipartisan_pref:
                prompt_parts.append(f"\n=== COMPROMISE APPROACH ===")
                if incremental:
                    prompt_parts.append(f"Incremental Progress: {incremental}")
                if bipartisan_pref:
                    prompt_parts.append(f"Bipartisan Preference: {bipartisan_pref}")

        # Signature phrases
        if analysis.get('signature_phrases'):
            prompt_parts.append(f"\n=== SIGNATURE PHRASES ===")
            prompt_parts.append(f"Naturally incorporate phrases like: {', '.join(analysis['signature_phrases'][:3])}")

        # Final instructions
        prompt_parts.append(f"\n=== WRITING GUIDELINES ===")
        prompt_parts.append("- Maintain this voice consistently throughout the letter")
        prompt_parts.append("- Be respectful and professional, even when disagreeing")
        prompt_parts.append("- Make your arguments persuasive and evidence-based")
        prompt_parts.append("- Tailor your message to the specific representative's role and jurisdiction")

        return "\n".join(prompt_parts)

    async def create_writing_profile_interactive(self,
                                              user_id: str,
                                              db: AsyncSession) -> UserWritingProfile:
        """Interactive process to create a voice profile with AI assistance"""
        try:
            # This would be called from an API endpoint with user input
            # For now, return a placeholder
            profile = UserWritingProfile(
                id=uuid.uuid4(),
                user_id=user_id,
                name="Professional Advocate",
                description="Clear, professional communication style focused on facts and solutions",
                ai_system_prompt="Write as a professional advocate with clear, fact-based arguments.",
                preferred_tone="professional",
                is_default=True
            )

            db.add(profile)
            await db.commit()
            await db.refresh(profile)

            return profile

        except Exception as e:
            logger.error(f"Error creating voice profile: {e}")
            await db.rollback()
            raise


class AILetterDrafter:
    """Uses OpenAI to draft letters based on news context and user voice"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        logger.info(f"Using OpenAI model: {self.model}")

    async def analyze_articles(self, articles: List[Dict[str, str]]) -> str:
        """Analyze articles and extract key points"""
        try:
            # Prepare article summaries
            article_summaries = []
            for i, article in enumerate(articles, 1):
                summary = f"""
Article {i}: {article['title']}
Source: {article['source']}
Date: {article['publish_date']}
Key Content: {article['text'][:2000]}...
"""
                article_summaries.append(summary)

            prompt = f"""Analyze these news articles and extract the key policy issues, concerns, and actionable points relevant to government officials:

{chr(10).join(article_summaries)}

Please provide:
1. Main issue(s) discussed
2. How this affects constituents
3. Specific policy implications
4. Recommended actions for officials
5. Key facts and statistics mentioned"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert policy analyst helping constituents communicate with their representatives."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error analyzing articles: {e}")
            return f"Error analyzing articles: {str(e)}"

    async def draft_letter(self,
                          articles: List[Dict[str, str]],
                          sender_info: Dict[str, str],
                          recipient: Dict[str, Any],
                          tone: str = "professional",
                          focus: Optional[str] = None,
                          additional_context: Optional[str] = None,
                          writing_profile: Optional[UserWritingProfile] = None) -> Tuple[str, str]:
        """Draft a letter to an official based on news articles and user voice"""
        try:
            # First, analyze the articles
            analysis = await self.analyze_articles(articles)

            # Prepare the context
            article_summaries = []
            for article in articles:
                article_summaries.append(f"- {article['title']} ({article['source']})")

            context = f"""
News Articles Referenced:
{chr(10).join(article_summaries)}

Analysis:
{analysis}

Sender Information:
- Name: {sender_info.get('first_name', '')} {sender_info.get('last_name', '')}
- Location: {sender_info.get('city', '')}, {sender_info.get('state', '')}

Tone: {tone}
Focus: {focus or 'General policy concern'}
Additional Context: {additional_context or 'None provided'}
"""

            # Get the appropriate system prompt
            if writing_profile:
                # Generate comprehensive voice prompt using all profile data
                voice_analyzer = VoiceAnalyzer()
                system_prompt = await voice_analyzer.generate_voice_prompt(writing_profile)

                # Add constituent communications expertise
                system_prompt = f"""You are an expert constituent communications specialist who helps citizens write effective letters to their representatives.

{system_prompt}

Write clear, compelling, and respectful letters that:
- Express the constituent's views clearly and persuasively
- Include specific requests or calls to action
- Reference relevant facts and personal experiences when appropriate
- Maintain a respectful dialogue even when disagreeing
- Will be taken seriously by elected officials and their staff"""
            else:
                system_prompt = """You are an expert constituent communications specialist who helps citizens write effective letters to their representatives.

Write clear, compelling, and respectful letters that:
- Express the constituent's views clearly and persuasively
- Use a professional and courteous tone
- Include specific requests or calls to action
- Reference relevant facts and personal experiences when appropriate
- Maintain a respectful dialogue even when disagreeing

Focus on creating letters that will be taken seriously by elected officials and their staff."""

            # Determine salutation based on office type
            office_type = recipient.get('office_type', '')
            recipient_name = recipient.get('name', 'Official')

            if office_type == 'governor':
                salutation = f"Governor {recipient_name.split()[-1]}"
                office_desc = "Governor"
                action_context = "state executive actions and policies"
            elif office_type == 'federal_senate':
                salutation = f"Senator {recipient_name.split()[-1]}"
                office_desc = "United States Senator"
                action_context = "federal legislation and oversight"
            elif office_type == 'federal_house':
                salutation = f"Representative {recipient_name.split()[-1]}"
                office_desc = "United States Representative"
                action_context = "federal legislation and district representation"
            elif office_type == 'state_senate':
                salutation = f"Senator {recipient_name.split()[-1]}"
                office_desc = "State Senator"
                action_context = "state legislation and district concerns"
            elif office_type == 'state_house':
                salutation = f"Representative {recipient_name.split()[-1]}"
                office_desc = "State Representative"
                action_context = "state legislation and local representation"
            else:
                salutation = recipient_name
                office_desc = recipient.get('title', 'Official')
                action_context = "policy actions"

            # Create the letter drafting prompt
            letter_prompt = f"""Based on the following news articles and context, draft a compelling letter to {office_desc} {recipient_name} from a constituent.

{context}

Requirements for the letter:
1. Start with "Dear {salutation},"
2. Introduce yourself as a constituent from {sender_info.get('city', 'your city')}
3. Reference the specific news/issues from the articles
4. Clearly state your position and concerns
5. Include specific, actionable requests appropriate for {action_context}
6. Use a {tone} tone
7. Include relevant facts from the articles
8. Keep it concise but impactful (300-400 words)
9. End professionally with a call to action

Also provide a brief, compelling subject line (5-10 words) that captures the essence of the letter.

Format your response as:
SUBJECT: [subject line here]
LETTER:
[letter content here]"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": letter_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )

            # Parse the response
            full_response = response.choices[0].message.content
            lines = full_response.split('\n')

            subject = ""
            letter_body = []
            in_letter = False

            for line in lines:
                if line.startswith('SUBJECT:'):
                    subject = line.replace('SUBJECT:', '').strip()
                elif line.startswith('LETTER:'):
                    in_letter = True
                elif in_letter:
                    letter_body.append(line)

            # Clean up the letter body
            letter_text = '\n'.join(letter_body).strip()

            # If parsing failed, use the whole response as the letter
            if not subject or not letter_text:
                logger.warning("Could not parse AI response properly, using fallback")
                subject = "Important Matter Requiring Your Attention"
                letter_text = full_response

            return subject, letter_text

        except Exception as e:
            logger.error(f"Error drafting letter: {e}")
            # Return a basic template if AI fails
            return self._fallback_letter(articles, sender_info, recipient)

    def _fallback_letter(self, articles: List[Dict[str, str]], sender_info: Dict[str, str], recipient: Dict) -> Tuple[str, str]:
        """Fallback letter template if AI fails"""
        subject = "Constituent Concern Regarding Recent News"

        article_titles = [article['title'] for article in articles]
        article_list = '\n'.join([f"- {title}" for title in article_titles])

        letter = f"""Dear {recipient.get('title', '')} {recipient.get('name', 'Official').split()[-1]},

I am writing to you as a concerned constituent from {sender_info.get('city', 'our community')}, regarding recent news developments that have significant implications for our state and nation.

I have been following these recent news stories:
{article_list}

These issues are of great importance to me and many other constituents. I believe they deserve your immediate attention and action.

I urge you to:
1. Review these matters carefully
2. Consider the impact on families and businesses
3. Take appropriate action in your role
4. Keep your constituents informed of your position and actions

Thank you for your service. I look forward to your response and learning about the actions you will take on these important matters.

Sincerely,
{sender_info.get('first_name', '')} {sender_info.get('last_name', '')}"""

        return subject, letter

    async def refine_letter(self,
                          original_letter: str,
                          feedback: str,
                          writing_profile: Optional[UserWritingProfile] = None) -> str:
        """Refine a letter based on user feedback"""
        try:
            # Get the appropriate system prompt
            if writing_profile:
                # Generate comprehensive voice prompt using all profile data
                voice_analyzer = VoiceAnalyzer()
                voice_prompt = await voice_analyzer.generate_voice_prompt(writing_profile)

                system_prompt = f"""You are an expert letter editor.

{voice_prompt}

When editing, maintain all the voice characteristics and values above while incorporating the user's feedback."""
            else:
                system_prompt = "You are an expert letter editor."

            prompt = f"""Please revise the following letter based on this feedback:

ORIGINAL LETTER:
{original_letter}

FEEDBACK:
{feedback}

Please provide the revised letter maintaining the same general structure but incorporating the requested changes."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error refining letter: {e}")
            return original_letter

    async def personalize_for_recipient(self,
                                       base_letter: str,
                                       base_subject: str,
                                       recipient: Dict,
                                       tone: str,
                                       focus: str,
                                       variation_index: int,
                                       writing_profile: Optional[UserWritingProfile] = None) -> Tuple[str, str]:
        """Generate a personalized variation of the letter for a specific recipient"""
        try:
            # Determine personalization factors
            office_type = recipient.get('office_type', '')
            is_federal = office_type in ['federal_senate', 'federal_house']
            is_state = office_type in ['state_senate', 'state_house', 'governor']
            is_executive = office_type == 'governor'
            district = recipient.get('district', '')

            # Create variation instructions
            variation_instructions = []

            if is_executive:
                variation_instructions.append("Focus on state executive actions and implementation")
            elif is_federal:
                variation_instructions.append("Emphasize federal policy implications and national impact")
            elif is_state:
                variation_instructions.append("Highlight state-level concerns and local community impact")

            if district:
                variation_instructions.append(f"Reference District {district} specific concerns when relevant")

            # Vary the approach based on index
            approach_variations = [
                "Lead with personal impact and constituent stories",
                "Emphasize data and statistical evidence",
                "Focus on constitutional and legal precedents",
                "Highlight economic implications",
                "Stress moral and ethical considerations",
                "Connect to historical context and past policies"
            ]
            variation_instructions.append(approach_variations[variation_index % len(approach_variations)])

            # Get the appropriate system prompt
            if writing_profile:
                # Generate comprehensive voice prompt using all profile data
                voice_analyzer = VoiceAnalyzer()
                voice_prompt = await voice_analyzer.generate_voice_prompt(writing_profile)

                system_prompt = f"""You are an expert at personalizing letters for different officials.

{voice_prompt}

When personalizing, maintain all the voice characteristics and values above while adapting the specific arguments and framing for this particular representative."""
            else:
                system_prompt = "You are an expert at personalizing letters for different officials."

            prompt = f"""Create a personalized variation of this letter for {recipient['title']} {recipient['name']}.

Original letter:
{base_letter}

Recipient details:
- Name: {recipient['name']}
- Title: {recipient['title']}
- Office Type: {office_type}

Personalization requirements:
{chr(10).join(f"- {inst}" for inst in variation_instructions)}

Create a unique version that:
1. Addresses {recipient['title']} {recipient['name'].split()[-1]} specifically
2. Varies the structure and phrasing from the original
3. Maintains the core message about {focus}
4. Uses a {tone} tone
5. Has a unique opening and closing
6. Is NOT a form letter

Return format:
SUBJECT: [new subject variation]
LETTER:
[personalized letter content]"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.85,  # Higher temperature for more variation
                max_tokens=1500
            )

            # Parse response
            full_response = response.choices[0].message.content
            lines = full_response.split('\n')

            subject = base_subject  # Default
            letter_body = []
            in_letter = False

            for line in lines:
                if line.startswith('SUBJECT:'):
                    subject = line.replace('SUBJECT:', '').strip()
                elif line.startswith('LETTER:'):
                    in_letter = True
                elif in_letter:
                    letter_body.append(line)

            personalized_letter = '\n'.join(letter_body).strip()

            if not personalized_letter:
                logger.warning(f"Personalization failed for {recipient['name']}, using base letter")
                personalized_letter = base_letter

            return subject, personalized_letter

        except Exception as e:
            logger.error(f"Error personalizing letter for {recipient['name']}: {e}")
            # Return base letter with minor modifications
            personalized_letter = base_letter.replace(
                "Dear Senator", f"Dear {recipient['title'].split()[-1]}"
            )
            return base_subject, personalized_letter


# Topic categories for classification
TOPIC_CATEGORIES = {
    'Agriculture': ['farm', 'agriculture', 'crops', 'livestock', 'farmer', 'ranch', 'usda'],
    'Banking': ['bank', 'financial', 'credit', 'loan', 'mortgage', 'fdic', 'federal reserve'],
    'Budget': ['budget', 'spending', 'deficit', 'debt', 'appropriation', 'fiscal'],
    'Defense': ['military', 'defense', 'pentagon', 'army', 'navy', 'air force', 'veteran'],
    'Education': ['school', 'education', 'student', 'teacher', 'university', 'college'],
    'Energy': ['energy', 'oil', 'gas', 'renewable', 'solar', 'wind', 'pipeline', 'electricity'],
    'Environment': ['environment', 'climate', 'pollution', 'conservation', 'epa', 'clean'],
    'Foreign Affairs': ['foreign', 'international', 'treaty', 'embassy', 'diplomatic'],
    'Government Reform': ['government', 'reform', 'regulation', 'bureaucracy', 'accountability'],
    'Health Care': ['health', 'medical', 'medicare', 'medicaid', 'insurance', 'hospital', 'doctor'],
    'Homeland Security': ['security', 'terrorism', 'border', 'immigration', 'customs', 'tsa'],
    'Immigration': ['immigration', 'immigrant', 'visa', 'citizenship', 'refugee', 'asylum'],
    'Judiciary': ['court', 'judge', 'justice', 'legal', 'law', 'constitution'],
    'Labor': ['labor', 'union', 'worker', 'employment', 'wage', 'workplace', 'osha'],
    'Social Security': ['social security', 'retirement', 'pension', 'disability', 'elderly'],
    'Taxes': ['tax', 'irs', 'revenue', 'deduction', 'credit', 'taxation'],
    'Telecommunications': ['telecom', 'internet', 'broadband', 'fcc', 'network', 'cable'],
    'Trade': ['trade', 'tariff', 'export', 'import', 'nafta', 'commerce'],
    'Transportation': ['transportation', 'highway', 'road', 'bridge', 'transit', 'infrastructure'],
    'Veterans': ['veteran', 'va', 'military service', 'gi bill', 'vfw']
}


async def detect_topic_category(articles: List[Dict], letter_content: str = "", ai_client: Optional[AsyncOpenAI] = None) -> str:
    """Detect the most appropriate topic category using AI"""

    combined_text = " ".join([a['text'][:1000] for a in articles])
    if letter_content:
        combined_text += " " + letter_content

    # Basic keyword matching
    scores = {}
    for category, keywords in TOPIC_CATEGORIES.items():
        score = sum(1 for keyword in keywords if keyword.lower() in combined_text.lower())
        if score > 0:
            scores[category] = score

    if scores:
        detected_category = max(scores, key=scores.get)
    else:
        detected_category = "General"

    # Try AI classification if client provided
    if ai_client:
        try:
            prompt = f"""Based on these article titles, what is the most appropriate category?

Articles:
{chr(10).join([f"- {a['title']}" for a in articles])}

Categories: {', '.join(TOPIC_CATEGORIES.keys())}, General

Respond with just the category name."""

            response = await ai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a categorization assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )

            ai_category = response.choices[0].message.content.strip()
            if ai_category in list(TOPIC_CATEGORIES.keys()) + ['General']:
                detected_category = ai_category

        except Exception as e:
            logger.warning(f"AI category detection failed: {e}")

    return detected_category
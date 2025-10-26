"""
Letter generation and management API endpoints
"""
import uuid
import json
import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from pydantic import BaseModel, HttpUrl, Field

from app.core.database import get_db
from app.core.config import settings
from app.api.dependencies import get_current_active_user as get_current_user
from app.models.user import User
from app.models.letter import (
    Letter, LetterRecipient, UserWritingProfile, NewsArticle,
    LetterStatus, DeliveryMethod
)
from app.models.geocoding import Representative
from app.services.ai_letter import (
    NewsArticleFetcher, AILetterDrafter, VoiceAnalyzer,
    detect_topic_category
)
from app.services.pdf_generator import PDFService

router = APIRouter(prefix="/api/letters", tags=["letters"])
logger = logging.getLogger(__name__)


# ==================== Request/Response Models ====================

class VoiceProfileCreate(BaseModel):
    """Request model for creating a writing profile"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    writing_samples: Optional[List[str]] = Field(default_factory=list)
    preferred_tone: str = Field(default="professional")
    preferred_length: str = Field(default="medium")
    include_personal_stories: bool = Field(default=True)
    include_data_statistics: bool = Field(default=True)
    include_emotional_appeals: bool = Field(default=False)
    include_constitutional_arguments: bool = Field(default=True)
    political_leaning: Optional[str] = None
    key_issues: Optional[List[str]] = Field(default_factory=list)
    signature_phrases: Optional[List[str]] = Field(default_factory=list)
    avoid_phrases: Optional[List[str]] = Field(default_factory=list)
    is_default: bool = Field(default=False)

    # Enhanced fields
    issue_positions: Optional[Dict[str, Any]] = Field(default_factory=dict)
    abortion_position: Optional[str] = None
    core_values: Optional[List[str]] = Field(default_factory=list)
    argumentative_frameworks: Optional[Dict[str, Any]] = Field(default_factory=dict)
    representative_engagement: Optional[Dict[str, Any]] = Field(default_factory=dict)
    regional_context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    compromise_positioning: Optional[Dict[str, Any]] = Field(default_factory=dict)


class VoiceProfileUpdate(BaseModel):
    """Request model for updating a writing profile"""
    name: Optional[str] = None
    description: Optional[str] = None
    writing_samples: Optional[List[str]] = None
    preferred_tone: Optional[str] = None
    preferred_length: Optional[str] = None
    include_personal_stories: Optional[bool] = None
    include_data_statistics: Optional[bool] = None
    include_emotional_appeals: Optional[bool] = None
    include_constitutional_arguments: Optional[bool] = None
    political_leaning: Optional[str] = None
    key_issues: Optional[List[str]] = None
    signature_phrases: Optional[List[str]] = None
    avoid_phrases: Optional[List[str]] = None
    is_default: Optional[bool] = None

    # Enhanced fields
    issue_positions: Optional[Dict[str, Any]] = None
    abortion_position: Optional[str] = None
    core_values: Optional[List[str]] = None
    argumentative_frameworks: Optional[Dict[str, Any]] = None
    representative_engagement: Optional[Dict[str, Any]] = None
    regional_context: Optional[Dict[str, Any]] = None
    compromise_positioning: Optional[Dict[str, Any]] = None


class VoiceProfileResponse(BaseModel):
    """Response model for writing profile"""
    id: str
    name: str
    description: Optional[str]
    is_default: bool
    is_active: bool
    tone_attributes: Dict[str, Any]
    style_attributes: Dict[str, Any]
    vocabulary_level: str
    preferred_tone: str
    preferred_length: str
    include_personal_stories: bool
    include_data_statistics: bool
    include_emotional_appeals: bool
    include_constitutional_arguments: bool
    political_leaning: Optional[str]
    key_issues: List[str]
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]

    # Enhanced fields
    issue_positions: Optional[Dict[str, Any]] = None
    abortion_position: Optional[str] = None
    core_values: Optional[List[str]] = None
    argumentative_frameworks: Optional[Dict[str, Any]] = None
    representative_engagement: Optional[Dict[str, Any]] = None
    regional_context: Optional[Dict[str, Any]] = None
    compromise_positioning: Optional[Dict[str, Any]] = None


class AnalyzeVoiceRequest(BaseModel):
    """Request to analyze writing samples"""
    writing_samples: List[str] = Field(..., min_items=1, max_items=10)


class ArticleFetchRequest(BaseModel):
    """Request to fetch news articles"""
    urls: List[HttpUrl] = Field(..., min_items=1, max_items=10)


class ArticleResponse(BaseModel):
    """Response model for fetched article"""
    url: str
    title: str
    text: str
    authors: str
    publish_date: str
    summary: str
    source: str


class GenerateLetterRequest(BaseModel):
    """Request to generate a letter"""
    article_urls: List[HttpUrl] = Field(default_factory=list, max_items=10)
    recipient_ids: List[str] = Field(..., min_items=1, description="Representative IDs from geocoding")
    writing_profile_id: Optional[str] = None
    topic: str = Field(..., min_length=1, description="Letter topic/subject")
    tone: str = Field(default="professional")
    focus: Optional[str] = None
    custom_context: Optional[str] = Field(None, alias="additional_context")
    same_letter_for_all: bool = Field(True, alias="personalize_for_each")

    class Config:
        populate_by_name = True  # Allow both aliases


class RefineLetterRequest(BaseModel):
    """Request to refine a letter"""
    letter_id: str
    feedback: str = Field(..., min_length=1)
    writing_profile_id: Optional[str] = None


class LetterResponse(BaseModel):
    """Response model for letter"""
    id: str
    subject: str
    base_content: str
    status: str
    tone: Optional[str]
    focus: Optional[str]
    category: Optional[str]
    writing_profile_id: Optional[str]
    writing_profile_name: Optional[str]
    recipients_count: int
    recipients: List[Dict[str, Any]]
    word_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    finalized_at: Optional[datetime]


class LetterDetailResponse(BaseModel):
    """Detailed response model for letter"""
    id: str
    subject: str
    base_content: str
    status: str
    tone: Optional[str]
    focus: Optional[str]
    additional_context: Optional[str]
    news_articles: List[Dict[str, Any]]
    ai_model_used: Optional[str]
    ai_analysis: Optional[str]
    category: Optional[str]
    writing_profile_id: Optional[str]
    writing_profile_name: Optional[str]
    recipients: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    finalized_at: Optional[datetime]


class GenerateFocusOptionsRequest(BaseModel):
    """Request to generate focus options based on articles"""
    article_urls: List[HttpUrl] = Field(..., min_items=1, max_items=10)


# ==================== Writing Profile Endpoints ====================

@router.post("/writing-profiles", response_model=VoiceProfileResponse)
async def create_writing_profile(
    profile_data: VoiceProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new writing profile for the user"""
    try:
        # If setting as default, unset other defaults
        if profile_data.is_default:
            result = await db.execute(
                select(UserWritingProfile).where(
                    and_(
                        UserWritingProfile.user_id == current_user.id,
                        UserWritingProfile.is_default == True
                    )
                )
            )
            existing_defaults = result.scalars().all()
            for profile in existing_defaults:
                profile.is_default = False

        # Analyze writing samples if provided
        voice_analyzer = VoiceAnalyzer()
        analysis = {}
        ai_prompt = None

        if profile_data.writing_samples:
            analysis = await voice_analyzer.analyze_writing_samples(profile_data.writing_samples)

        # Create the profile
        profile = UserWritingProfile(
            id=uuid.uuid4(),
            user_id=current_user.id,
            name=profile_data.name,
            description=profile_data.description,
            is_default=profile_data.is_default,
            is_active=True,
            tone_attributes=analysis.get('tone_attributes', {}),
            style_attributes=analysis.get('style_attributes', {}),
            vocabulary_level=analysis.get('vocabulary_level', 'standard'),
            writing_samples=profile_data.writing_samples or [],
            preferred_tone=profile_data.preferred_tone,
            preferred_length=profile_data.preferred_length,
            include_personal_stories=profile_data.include_personal_stories,
            include_data_statistics=profile_data.include_data_statistics,
            include_emotional_appeals=profile_data.include_emotional_appeals,
            include_constitutional_arguments=profile_data.include_constitutional_arguments,
            political_leaning=profile_data.political_leaning,
            key_issues=profile_data.key_issues or [],
            signature_phrases=profile_data.signature_phrases or analysis.get('signature_phrases', []),
            avoid_phrases=profile_data.avoid_phrases or [],
            # Enhanced fields
            issue_positions=profile_data.issue_positions or {},
            abortion_position=profile_data.abortion_position,
            core_values=profile_data.core_values or [],
            argumentative_frameworks=profile_data.argumentative_frameworks or {},
            representative_engagement=profile_data.representative_engagement or {},
            regional_context=profile_data.regional_context or {},
            compromise_positioning=profile_data.compromise_positioning or {}
        )

        # Generate AI system prompt
        if analysis:
            profile.ai_system_prompt = await voice_analyzer.generate_voice_prompt(profile, analysis)

        db.add(profile)
        await db.commit()
        await db.refresh(profile)

        return VoiceProfileResponse(
            id=str(profile.id),
            name=profile.name,
            description=profile.description,
            is_default=profile.is_default,
            is_active=profile.is_active,
            tone_attributes=profile.tone_attributes,
            style_attributes=profile.style_attributes,
            vocabulary_level=profile.vocabulary_level,
            preferred_tone=profile.preferred_tone,
            preferred_length=profile.preferred_length,
            include_personal_stories=profile.include_personal_stories,
            include_data_statistics=profile.include_data_statistics,
            include_emotional_appeals=profile.include_emotional_appeals,
            include_constitutional_arguments=profile.include_constitutional_arguments,
            political_leaning=profile.political_leaning,
            key_issues=profile.key_issues,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            last_used_at=profile.last_used_at,
            # Enhanced fields
            issue_positions=profile.issue_positions,
            abortion_position=profile.abortion_position,
            core_values=profile.core_values,
            argumentative_frameworks=profile.argumentative_frameworks,
            representative_engagement=profile.representative_engagement,
            regional_context=profile.regional_context,
            compromise_positioning=profile.compromise_positioning
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create writing profile: {str(e)}"
        )


@router.get("/writing-profiles", response_model=List[VoiceProfileResponse])
async def list_writing_profiles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all writing profiles for the current user"""
    result = await db.execute(
        select(UserWritingProfile)
        .where(UserWritingProfile.user_id == current_user.id)
        .order_by(UserWritingProfile.is_default.desc(), UserWritingProfile.created_at.desc())
    )
    profiles = result.scalars().all()

    return [
        VoiceProfileResponse(
            id=str(profile.id),
            name=profile.name,
            description=profile.description,
            is_default=profile.is_default,
            is_active=profile.is_active,
            tone_attributes=profile.tone_attributes or {},
            style_attributes=profile.style_attributes or {},
            vocabulary_level=profile.vocabulary_level,
            preferred_tone=profile.preferred_tone,
            preferred_length=profile.preferred_length,
            include_personal_stories=profile.include_personal_stories,
            include_data_statistics=profile.include_data_statistics,
            include_emotional_appeals=profile.include_emotional_appeals,
            include_constitutional_arguments=profile.include_constitutional_arguments,
            political_leaning=profile.political_leaning,
            key_issues=profile.key_issues or [],
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            last_used_at=profile.last_used_at,
            # Enhanced fields
            issue_positions=profile.issue_positions or {},
            abortion_position=profile.abortion_position,
            core_values=profile.core_values or [],
            argumentative_frameworks=profile.argumentative_frameworks or {},
            representative_engagement=profile.representative_engagement or {},
            regional_context=profile.regional_context or {},
            compromise_positioning=profile.compromise_positioning or {}
        )
        for profile in profiles
    ]


@router.get("/writing-profiles/{profile_id}", response_model=VoiceProfileResponse)
async def get_writing_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific writing profile"""
    result = await db.execute(
        select(UserWritingProfile).where(
            and_(
                UserWritingProfile.id == uuid.UUID(profile_id),
                UserWritingProfile.user_id == current_user.id
            )
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Writing profile not found"
        )

    return VoiceProfileResponse(
        id=str(profile.id),
        name=profile.name,
        description=profile.description,
        is_default=profile.is_default,
        is_active=profile.is_active,
        tone_attributes=profile.tone_attributes or {},
        style_attributes=profile.style_attributes or {},
        vocabulary_level=profile.vocabulary_level,
        preferred_tone=profile.preferred_tone,
        preferred_length=profile.preferred_length,
        include_personal_stories=profile.include_personal_stories,
        include_data_statistics=profile.include_data_statistics,
        include_emotional_appeals=profile.include_emotional_appeals,
        include_constitutional_arguments=profile.include_constitutional_arguments,
        political_leaning=profile.political_leaning,
        key_issues=profile.key_issues or [],
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        last_used_at=profile.last_used_at,
        # Enhanced fields
        issue_positions=profile.issue_positions or {},
        abortion_position=profile.abortion_position,
        core_values=profile.core_values or [],
        argumentative_frameworks=profile.argumentative_frameworks or {},
        representative_engagement=profile.representative_engagement or {},
        regional_context=profile.regional_context or {},
        compromise_positioning=profile.compromise_positioning or {}
    )


@router.put("/writing-profiles/{profile_id}", response_model=VoiceProfileResponse)
async def update_writing_profile(
    profile_id: str,
    profile_data: VoiceProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a writing profile"""
    result = await db.execute(
        select(UserWritingProfile).where(
            and_(
                UserWritingProfile.id == uuid.UUID(profile_id),
                UserWritingProfile.user_id == current_user.id
            )
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Writing profile not found"
        )

    # Update fields if provided
    update_data = profile_data.dict(exclude_unset=True)

    # If setting as default, unset other defaults
    if update_data.get('is_default'):
        result = await db.execute(
            select(UserWritingProfile).where(
                and_(
                    UserWritingProfile.user_id == current_user.id,
                    UserWritingProfile.is_default == True,
                    UserWritingProfile.id != uuid.UUID(profile_id)
                )
            )
        )
        other_defaults = result.scalars().all()
        for other in other_defaults:
            other.is_default = False

    # Re-analyze if new writing samples provided
    if update_data.get('writing_samples'):
        voice_analyzer = VoiceAnalyzer()
        analysis = await voice_analyzer.analyze_writing_samples(update_data['writing_samples'])
        profile.tone_attributes = analysis.get('tone_attributes', {})
        profile.style_attributes = analysis.get('style_attributes', {})
        profile.vocabulary_level = analysis.get('vocabulary_level', 'standard')
        profile.signature_phrases = analysis.get('signature_phrases', [])
        profile.ai_system_prompt = await voice_analyzer.generate_voice_prompt(profile, analysis)

    # Apply updates
    for field, value in update_data.items():
        if hasattr(profile, field) and field not in ['tone_attributes', 'style_attributes', 'vocabulary_level', 'signature_phrases']:
            setattr(profile, field, value)

    profile.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(profile)

    return VoiceProfileResponse(
        id=str(profile.id),
        name=profile.name,
        description=profile.description,
        is_default=profile.is_default,
        is_active=profile.is_active,
        tone_attributes=profile.tone_attributes or {},
        style_attributes=profile.style_attributes or {},
        vocabulary_level=profile.vocabulary_level,
        preferred_tone=profile.preferred_tone,
        preferred_length=profile.preferred_length,
        include_personal_stories=profile.include_personal_stories,
        include_data_statistics=profile.include_data_statistics,
        include_emotional_appeals=profile.include_emotional_appeals,
        include_constitutional_arguments=profile.include_constitutional_arguments,
        political_leaning=profile.political_leaning,
        key_issues=profile.key_issues or [],
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        last_used_at=profile.last_used_at,
        # Enhanced fields
        issue_positions=profile.issue_positions or {},
        abortion_position=profile.abortion_position,
        core_values=profile.core_values or [],
        argumentative_frameworks=profile.argumentative_frameworks or {},
        representative_engagement=profile.representative_engagement or {},
        regional_context=profile.regional_context or {},
        compromise_positioning=profile.compromise_positioning or {}
    )


@router.delete("/writing-profiles/{profile_id}")
async def delete_writing_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a writing profile"""
    result = await db.execute(
        select(UserWritingProfile).where(
            and_(
                UserWritingProfile.id == uuid.UUID(profile_id),
                UserWritingProfile.user_id == current_user.id
            )
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Writing profile not found"
        )

    await db.delete(profile)
    await db.commit()

    return {"message": "Writing profile deleted successfully"}


@router.post("/writing-profiles/analyze")
async def analyze_voice(
    request: AnalyzeVoiceRequest,
    current_user: User = Depends(get_current_user)
):
    """Analyze writing samples to extract voice characteristics"""
    try:
        voice_analyzer = VoiceAnalyzer()
        analysis = await voice_analyzer.analyze_writing_samples(request.writing_samples)

        return {
            "analysis": analysis,
            "message": "Writing samples analyzed successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze writing samples: {str(e)}"
        )


class EnhancedIssueData(BaseModel):
    """Enhanced issue data with position, priority, and personal connection"""
    issue: str
    position: Optional[str] = None
    priority: Optional[str] = None
    personal_connection: Optional[str] = None


class GenerateDescriptionRequest(BaseModel):
    """Request to generate AI-assisted profile descriptions"""
    user_name: str
    user_city: Optional[str] = None
    user_state: Optional[str] = None
    selected_issues: Union[List[str], List[EnhancedIssueData]] = Field(default_factory=list)
    custom_issues: Optional[str] = None
    political_leaning: Optional[str] = None
    abortion_position: Optional[str] = None
    core_values: List[str] = Field(default_factory=list)
    tone: str = "Professional & Diplomatic"
    argumentative_frameworks: Dict[str, bool] = Field(default_factory=dict)
    representative_engagement: Dict[str, str] = Field(default_factory=dict)
    additional_context: Optional[str] = None


@router.post("/writing-profiles/generate-description")
async def generate_profile_description(
    request: GenerateDescriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate AI-assisted writing profile descriptions"""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        # Build enhanced context for AI
        context_parts = [f"Name: {request.user_name}"]
        if request.user_city and request.user_state:
            context_parts.append(f"Location: {request.user_city}, {request.user_state}")

        if request.political_leaning:
            context_parts.append(f"Political Leaning: {request.political_leaning}")

        # Handle enhanced issue format
        if request.selected_issues:
            if len(request.selected_issues) > 0:
                # Check if it's enhanced format (list of objects) or simple format (list of strings)
                first_issue = request.selected_issues[0]
                if isinstance(first_issue, dict) or hasattr(first_issue, 'issue'):
                    # Enhanced format
                    issue_lines = ["Key Issues with Positions:"]
                    for issue_data in request.selected_issues:
                        if isinstance(issue_data, dict):
                            issue = issue_data.get('issue', '')
                            position = issue_data.get('position', '')
                            priority = issue_data.get('priority', '')
                            personal = issue_data.get('personal_connection', '')
                        else:
                            issue = issue_data.issue
                            position = issue_data.position
                            priority = issue_data.priority
                            personal = issue_data.personal_connection

                        issue_line = f"  - {issue}"
                        if position:
                            issue_line += f" ({position.replace('_', ' ')})"
                        if priority:
                            issue_line += f" [Priority: {priority}]"
                        issue_lines.append(issue_line)
                        if personal:
                            issue_lines.append(f"    Personal Connection: {personal}")
                    context_parts.append("\n".join(issue_lines))
                else:
                    # Simple format (backward compatibility)
                    context_parts.append(f"Key Issues: {', '.join(request.selected_issues)}")

        if request.custom_issues:
            context_parts.append(f"Additional Issues: {request.custom_issues}")

        if request.abortion_position:
            context_parts.append(f"Abortion Position: {request.abortion_position.replace('_', ' ')}")

        if request.core_values:
            context_parts.append(f"Core Values: {', '.join([v.replace('_', ' ').title() for v in request.core_values])}")

        context_parts.append(f"Preferred Tone: {request.tone}")

        if request.argumentative_frameworks:
            selected_frameworks = [k.replace('_', ' ').title() for k, v in request.argumentative_frameworks.items() if v]
            if selected_frameworks:
                context_parts.append(f"Argumentative Frameworks: {', '.join(selected_frameworks)}")

        if request.representative_engagement:
            eng = request.representative_engagement
            if eng.get('aligned_approach') or eng.get('opposing_approach'):
                engagement_parts = []
                if eng.get('aligned_approach'):
                    engagement_parts.append(f"Aligned Reps: {eng['aligned_approach']}")
                if eng.get('opposing_approach'):
                    engagement_parts.append(f"Opposing Reps: {eng['opposing_approach']}")
                if eng.get('bipartisan_framing'):
                    engagement_parts.append(f"Bipartisan Framing: {eng['bipartisan_framing']}")
                context_parts.append(f"Engagement Strategy: {', '.join(engagement_parts)}")

        if request.additional_context:
            context_parts.append(f"Additional Context: {request.additional_context}")

        context = "\n".join(context_parts)

        prompt = f"""Based on this information about a civic advocate, generate 3 different writing profile descriptions that capture their political values and writing style. Each description should be 2-3 sentences that will guide AI letter generation.

{context}

Generate 3 variations:
1. A formal, professional version
2. A passionate, personal version
3. A balanced, persuasive version

IMPORTANT: Return ONLY valid JSON with no additional text. Use this exact format:
{{
  "formal": "description here",
  "passionate": "description here",
  "balanced": "description here"
}}"""

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are an expert at crafting writing profiles for civic advocacy letters. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()

        # Try to extract JSON if there's extra text
        if not content.startswith('{'):
            # Find first { and last }
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx != -1 and end_idx != -1:
                content = content[start_idx:end_idx+1]

        descriptions = json.loads(content)

        return {
            "descriptions": descriptions,
            "message": "Profile descriptions generated successfully"
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Response content: {response.choices[0].message.content}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse AI response. Please try again."
        )
    except Exception as e:
        logger.error(f"Error generating profile description: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate descriptions: {str(e)}"
        )


@router.post("/writing-profiles/{profile_id}/preview")
async def preview_writing_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a sample letter excerpt using the writing profile"""
    try:
        # Get the writing profile
        result = await db.execute(
            select(UserWritingProfile).where(
                and_(
                    UserWritingProfile.id == uuid.UUID(profile_id),
                    UserWritingProfile.user_id == current_user.id
                )
            )
        )
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Writing profile not found"
            )

        # Generate voice prompt
        voice_analyzer = VoiceAnalyzer()
        voice_prompt = await voice_analyzer.generate_voice_prompt(profile)

        # Generate sample letter excerpt
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        sample_topic = profile.key_issues[0] if profile.key_issues else "education funding"

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": voice_prompt},
                {"role": "user", "content": f"Write a brief opening paragraph for a letter to a representative about {sample_topic}. Keep it to 3-4 sentences."}
            ],
            temperature=0.8,
            max_tokens=200
        )

        sample_text = response.choices[0].message.content

        return {
            "sample_text": sample_text,
            "topic": sample_topic,
            "voice_prompt": voice_prompt,
            "message": "Sample generated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )


@router.get("/political-issues")
async def get_political_issues():
    """Get curated list of common political issues and positions with enhanced options"""
    return {
        "issues": [
            {"value": "healthcare_access", "label": "Healthcare Access", "description": "Universal healthcare, Medicare expansion, prescription drug costs"},
            {"value": "climate_change", "label": "Climate Change", "description": "Climate action, renewable energy, environmental protection"},
            {"value": "education_funding", "label": "Education Funding", "description": "Public school funding, teacher pay, student resources"},
            {"value": "economic_justice", "label": "Economic Justice", "description": "Living wages, worker rights, income inequality"},
            {"value": "civil_rights", "label": "Civil Rights", "description": "Voting rights, racial justice, equality"},
            {"value": "gun_reform", "label": "Gun Reform", "description": "Background checks, assault weapons ban, gun safety"},
            {"value": "immigration", "label": "Immigration Reform", "description": "Path to citizenship, DACA, border policy"},
            {"value": "voting_rights", "label": "Voting Rights", "description": "Voter access, election security, gerrymandering"},
            {"value": "criminal_justice", "label": "Criminal Justice Reform", "description": "Police reform, mass incarceration, sentencing"},
            {"value": "lgbtq_rights", "label": "LGBTQ+ Rights", "description": "Marriage equality, transgender rights, discrimination protection"},
            {"value": "reproductive_rights", "label": "Reproductive Rights", "description": "Abortion access, family planning, bodily autonomy"},
            {"value": "housing_affordability", "label": "Housing Affordability", "description": "Affordable housing, rent control, homelessness"},
            {"value": "infrastructure", "label": "Infrastructure", "description": "Roads, bridges, broadband, public transit"},
            {"value": "veterans_affairs", "label": "Veterans Affairs", "description": "VA healthcare, benefits, military support"}
        ],
        "position_options": [
            {"value": "strongly_support", "label": "Strongly Support"},
            {"value": "support", "label": "Support"},
            {"value": "neutral", "label": "Neutral / It Depends"},
            {"value": "oppose", "label": "Oppose"},
            {"value": "strongly_oppose", "label": "Strongly Oppose"}
        ],
        "priority_options": [
            {"value": "critical", "label": "Critical Priority", "description": "Top concern, most important to me"},
            {"value": "high", "label": "High Priority", "description": "Very important"},
            {"value": "medium", "label": "Medium Priority", "description": "Important but not urgent"},
            {"value": "low", "label": "Low Priority", "description": "Care about it, but less urgent"}
        ],
        "political_leanings": [
            {"value": "progressive", "label": "Progressive"},
            {"value": "liberal", "label": "Liberal"},
            {"value": "moderate", "label": "Moderate"},
            {"value": "conservative", "label": "Conservative"},
            {"value": "libertarian", "label": "Libertarian"},
            {"value": "independent", "label": "Independent"},
            {"value": "prefer_not_say", "label": "Prefer not to say"}
        ],
        "tones": [
            {"value": "professional", "label": "Professional & Diplomatic", "description": "Formal, respectful, evidence-based"},
            {"value": "passionate", "label": "Passionate & Urgent", "description": "Emotional, compelling, action-oriented"},
            {"value": "calm", "label": "Calm & Reasoned", "description": "Measured, logical, thoughtful"},
            {"value": "personal", "label": "Personal & Storytelling", "description": "Anecdotal, relatable, human-centered"},
            {"value": "analytical", "label": "Data-Driven & Analytical", "description": "Statistical, research-based, objective"}
        ],
        "core_values": [
            {"value": "personal_freedom", "label": "Personal Freedom & Liberty", "description": "Individual rights and freedoms"},
            {"value": "social_equality", "label": "Social Equality & Justice", "description": "Equal opportunity and treatment for all"},
            {"value": "community_responsibility", "label": "Community & Collective Responsibility", "description": "Working together for common good"},
            {"value": "fiscal_responsibility", "label": "Fiscal Responsibility", "description": "Balanced budgets and responsible spending"},
            {"value": "traditional_values", "label": "Traditional Values & Institutions", "description": "Preserving established norms and structures"},
            {"value": "innovation_progress", "label": "Innovation & Progress", "description": "Embracing change and new solutions"},
            {"value": "national_security", "label": "National Security", "description": "Strong defense and safety"},
            {"value": "environmental_stewardship", "label": "Environmental Stewardship", "description": "Protecting nature for future generations"},
            {"value": "individual_rights", "label": "Individual Rights", "description": "Protecting personal autonomy and choice"},
            {"value": "public_safety", "label": "Public Safety", "description": "Community security and wellbeing"}
        ],
        "argumentative_frameworks": [
            {"value": "constitutional", "label": "Constitutional & Legal Arguments", "description": "Based on law and constitutional principles"},
            {"value": "economic", "label": "Economic Impact & Data", "description": "Financial costs, benefits, and economic analysis"},
            {"value": "personal_stories", "label": "Personal Stories & Experiences", "description": "Real human impact and anecdotes"},
            {"value": "moral_ethical", "label": "Moral & Ethical Frameworks", "description": "What's right, fair, and just"},
            {"value": "scientific", "label": "Scientific Research & Studies", "description": "Evidence-based research and data"},
            {"value": "local_impact", "label": "Local Community Impact", "description": "How it affects our community specifically"},
            {"value": "national_security", "label": "National Security Concerns", "description": "Safety and defense implications"},
            {"value": "future_generations", "label": "Future Generations Impact", "description": "Long-term consequences for our children"}
        ],
        "abortion_positions": [
            {"value": "always_legal", "label": "Should Always Be Legal", "description": "Support full reproductive freedom at all stages"},
            {"value": "legal_with_limits", "label": "Legal With Some Restrictions", "description": "Support access with reasonable limitations"},
            {"value": "trimester_approach", "label": "Varies By Trimester", "description": "Different rules for different stages of pregnancy"},
            {"value": "exceptions_only", "label": "Only in Cases of Exception", "description": "Support only for rape, incest, or health risks"},
            {"value": "always_oppose", "label": "Should Always Be Illegal", "description": "Oppose except when mother's life is at risk"},
            {"value": "states_decide", "label": "Let States Decide", "description": "Should be determined at state level"},
            {"value": "prefer_not_say", "label": "Prefer Not to Say", "description": "Personal decision"}
        ],
        "engagement_approaches": {
            "aligned": [
                {"value": "partner", "label": "Partner", "description": "Work collaboratively on shared goals"},
                {"value": "encourage", "label": "Encourage", "description": "Support and motivate their efforts"},
                {"value": "reinforce", "label": "Reinforce", "description": "Express gratitude and appreciation"}
            ],
            "opposing": [
                {"value": "persuade", "label": "Persuade", "description": "Use facts and reason to change minds"},
                {"value": "challenge", "label": "Challenge", "description": "Push back on their positions"},
                {"value": "appeal_to_values", "label": "Appeal to Shared Values", "description": "Find common ground"}
            ],
            "bipartisan": [
                {"value": "always", "label": "Always Emphasize", "description": "Stress bipartisan cooperation in all letters"},
                {"value": "when_appropriate", "label": "When Appropriate", "description": "Use when issue has bipartisan support"},
                {"value": "rarely", "label": "Rarely", "description": "Focus on clear partisan position"}
            ]
        },
        "community_types": [
            {"value": "urban", "label": "Urban"},
            {"value": "suburban", "label": "Suburban"},
            {"value": "rural", "label": "Rural"}
        ],
        "compromise_stances": [
            {"value": "yes", "label": "Yes, Progress is Progress", "description": "Support incremental improvements"},
            {"value": "depends", "label": "Depends on the Issue", "description": "Some issues allow compromise, others don't"},
            {"value": "no", "label": "No, Hold the Line", "description": "Prefer to maintain principles over compromise"}
        ]
    }


# ==================== Article Fetching Endpoints ====================

@router.post("/fetch-articles", response_model=List[ArticleResponse])
async def fetch_articles(
    request: ArticleFetchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch and analyze news articles"""
    fetcher = NewsArticleFetcher()
    try:
        articles = await fetcher.fetch_multiple_articles(
            [str(url) for url in request.urls],
            db
        )

        return [
            ArticleResponse(
                url=article['url'],
                title=article['title'],
                text=article['text'],
                authors=article['authors'],
                publish_date=article['publish_date'],
                summary=article['summary'],
                source=article['source']
            )
            for article in articles
        ]

    finally:
        await fetcher.close()


@router.post("/generate-focus-options")
async def generate_focus_options(
    request: GenerateFocusOptionsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate AI-powered focus options based on articles"""
    fetcher = NewsArticleFetcher()
    drafter = AILetterDrafter()

    try:
        # Fetch the articles
        articles = await fetcher.fetch_multiple_articles(
            [str(url) for url in request.article_urls],
            db
        )

        # Generate focus options using AI
        article_summaries = []
        for article in articles[:3]:  # Use first 3 articles
            summary = f"Title: {article['title']}\nKey points: {article['text'][:500]}"
            article_summaries.append(summary)

        prompt = f"""Based on these news articles, generate 6 specific focus areas for a constituent letter:

{chr(10).join(article_summaries)}

Generate 6 focus options that are:
1. Specific to these articles
2. Relevant to constituents
3. Actionable for government officials
4. Clear and concise (10-15 words each)

Format as a numbered list."""

        response = await drafter.client.chat.completions.create(
            model=drafter.model,
            messages=[
                {"role": "system", "content": "You are a policy analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )

        focus_text = response.choices[0].message.content.strip()
        focus_options = []

        for line in focus_text.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                cleaned = line.lstrip('0123456789.-• ').strip()
                if cleaned:
                    focus_options.append(cleaned)

        # Add defaults if needed
        default_options = [
            "Impact on local communities",
            "Economic effects on families",
            "Constitutional implications",
            "Healthcare access and costs",
            "Education and workforce",
            "Infrastructure needs"
        ]

        while len(focus_options) < 6:
            if default_options:
                focus_options.append(default_options.pop(0))

        return {
            "focus_options": focus_options[:6],
            "category": await detect_topic_category(articles)
        }

    finally:
        await fetcher.close()


@router.post("/generate-topic-suggestions")
async def generate_topic_suggestions(
    request: GenerateFocusOptionsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate AI-powered topic/subject suggestions based on articles"""
    fetcher = NewsArticleFetcher()

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        # Fetch the articles
        articles = await fetcher.fetch_multiple_articles(
            [str(url) for url in request.article_urls],
            db
        )

        # Build article context
        article_summaries = []
        for article in articles[:5]:  # Use first 5 articles
            summary = f"Title: {article['title']}\nSummary: {article['text'][:400]}"
            article_summaries.append(summary)

        prompt = f"""Based on these news articles, generate 10 specific letter topics/subjects that a constituent could write to their representative about:

{chr(10).join(article_summaries)}

Generate 10 letter topics that are:
1. Specific and actionable
2. Relevant to constituent advocacy
3. Clear and concise (5-10 words each)
4. Varied in approach and focus

IMPORTANT: Return ONLY valid JSON with no additional text. Use this exact format:
{{
  "topics": ["topic 1", "topic 2", "topic 3", ...]
}}"""

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a policy analyst helping constituents advocate to their representatives. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=500
        )

        content = response.choices[0].message.content.strip()

        # Try to extract JSON if there's extra text
        if not content.startswith('{'):
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx != -1 and end_idx != -1:
                content = content[start_idx:end_idx+1]

        result = json.loads(content)
        topics = result.get('topics', [])

        # Add default topics if needed
        default_topics = [
            "Support for Climate Change Legislation",
            "Healthcare Access and Affordability",
            "Education Funding and Teacher Support",
            "Infrastructure Investment in Our Community",
            "Voting Rights Protection",
            "Gun Safety Measures",
            "Immigration Reform",
            "Economic Justice and Fair Wages",
            "Criminal Justice Reform",
            "Veterans Affairs Support"
        ]

        while len(topics) < 10:
            if default_topics:
                topics.append(default_topics.pop(0))

        return {
            "topics": topics[:10],
            "message": "Topic suggestions generated successfully"
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Response content: {response.choices[0].message.content}")
        # Return default topics on error
        return {
            "topics": [
                "Support for Climate Change Legislation",
                "Healthcare Access and Affordability",
                "Education Funding and Teacher Support",
                "Infrastructure Investment in Our Community",
                "Voting Rights Protection",
                "Gun Safety Measures",
                "Immigration Reform",
                "Economic Justice and Fair Wages",
                "Criminal Justice Reform",
                "Veterans Affairs Support"
            ],
            "message": "Using default topics (AI generation failed)"
        }
    except Exception as e:
        logger.error(f"Error generating topic suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate topic suggestions: {str(e)}"
        )
    finally:
        await fetcher.close()


# ==================== Letter Generation Endpoints ====================

@router.post("/generate", response_model=LetterDetailResponse)
async def generate_letter(
    request: GenerateLetterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a letter based on news articles and recipients"""
    fetcher = NewsArticleFetcher()
    drafter = AILetterDrafter()

    try:
        # Get writing profile if specified
        writing_profile = None
        if request.writing_profile_id:
            result = await db.execute(
                select(UserWritingProfile).where(
                    and_(
                        UserWritingProfile.id == uuid.UUID(request.writing_profile_id),
                        UserWritingProfile.user_id == current_user.id
                    )
                )
            )
            writing_profile = result.scalar_one_or_none()
        else:
            # Try to get default profile
            result = await db.execute(
                select(UserWritingProfile).where(
                    and_(
                        UserWritingProfile.user_id == current_user.id,
                        UserWritingProfile.is_default == True
                    )
                )
            )
            writing_profile = result.scalar_one_or_none()

        # Update last used timestamp if writing profile used
        if writing_profile:
            writing_profile.last_used_at = datetime.utcnow()

        # Fetch articles if provided
        articles = []
        if request.article_urls:
            articles = await fetcher.fetch_multiple_articles(
                [str(url) for url in request.article_urls],
                db
            )

        # Get representatives
        result = await db.execute(
            select(Representative).where(
                Representative.id.in_([uuid.UUID(rid) for rid in request.recipient_ids])
            )
        )
        representatives = result.scalars().all()

        if not representatives:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No valid representatives found"
            )

        # Prepare sender info
        sender_info = {
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'city': 'Your City',  # Would come from user's primary address
            'state': 'Your State'
        }

        # Get primary address if exists
        from app.models.user import UserAddress
        address_result = await db.execute(
            select(UserAddress)
            .where(UserAddress.user_id == current_user.id)
            .order_by(UserAddress.is_primary.desc(), UserAddress.created_at.desc())
        )
        addresses = address_result.scalars().all()

        if addresses:
            primary_address = addresses[0]
            sender_info['city'] = primary_address.city
            sender_info['state'] = primary_address.state

        # Generate base letter for first representative
        first_rep = representatives[0]
        recipient_dict = {
            'name': first_rep.name,
            'title': first_rep.title,
            'office_type': first_rep.office_type,
            'district': first_rep.district
        }

        subject, base_content = await drafter.draft_letter(
            articles=articles,
            sender_info=sender_info,
            recipient=recipient_dict,
            tone=request.tone,
            focus=request.topic,  # Use topic as the focus
            additional_context=request.custom_context or "",
            writing_profile=writing_profile
        )

        # Detect category
        category = await detect_topic_category(articles, base_content, drafter.client)

        # Build comprehensive context data for future AI-assisted edits
        context_data = {
            # Full article data including content
            'articles': [
                {
                    'url': a['url'],
                    'title': a['title'],
                    'content': a['text'][:5000],  # First 5000 chars
                    'summary': a.get('summary', ''),
                    'source': a.get('source', ''),
                    'authors': a.get('authors', 'Unknown'),
                    'publish_date': a.get('publish_date', 'Unknown')
                }
                for a in articles
            ] if articles else [],

            # Writing profile snapshot at time of generation
            'writing_profile_snapshot': {
                'name': writing_profile.name if writing_profile else None,
                'description': writing_profile.description if writing_profile else None,
                'preferred_tone': writing_profile.preferred_tone if writing_profile else None,
                'preferred_length': writing_profile.preferred_length if writing_profile else None,
                'political_leaning': writing_profile.political_leaning if writing_profile else None,
                'core_values': writing_profile.core_values if writing_profile else [],
                'issue_positions': writing_profile.issue_positions if writing_profile else {},
                'argumentative_frameworks': writing_profile.argumentative_frameworks if writing_profile else {},
                'representative_engagement': writing_profile.representative_engagement if writing_profile else {},
                'include_personal_stories': writing_profile.include_personal_stories if writing_profile else False,
                'include_data_statistics': writing_profile.include_data_statistics if writing_profile else False,
                'include_emotional_appeals': writing_profile.include_emotional_appeals if writing_profile else False,
                'include_constitutional_arguments': writing_profile.include_constitutional_arguments if writing_profile else False
            } if writing_profile else None,

            # Generation parameters
            'generation_params': {
                'tone': request.tone,
                'topic': request.topic,
                'focus': request.focus or "",
                'custom_context': request.custom_context or "",
                'same_letter_for_all': request.same_letter_for_all,
                'ai_model': drafter.model
            }
        }

        # Create letter record
        letter = Letter(
            id=uuid.uuid4(),
            user_id=current_user.id,
            writing_profile_id=writing_profile.id if writing_profile else None,
            subject=subject,
            status=LetterStatus.DRAFT,
            tone=request.tone,
            focus=request.topic,  # Use topic as the focus
            additional_context=request.custom_context or "",
            news_articles=[{'url': a['url'], 'title': a['title']} for a in articles] if articles else [],
            ai_model_used=drafter.model,
            ai_analysis=await drafter.analyze_articles(articles) if articles else "",
            context_data=context_data,
            base_content=base_content,
            category=category,
            reference_id=f"LTR_{current_user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )

        db.add(letter)

        # Create recipient records
        for i, rep in enumerate(representatives):
            # Always personalize for each recipient to ensure correct name/title
            # For the first recipient (i == 0), we can use the already-generated base_content if same_letter_for_all is True
            # For all other recipients, we must personalize
            recipient_dict = {
                'name': rep.name,
                'title': rep.title,
                'office_type': rep.office_type,
                'district': rep.district
            }

            # Always personalize to get correct recipient name, except for first recipient when same_letter_for_all is True
            if i == 0 and request.same_letter_for_all:
                # First recipient and same letter for all: use base content (already personalized for this recipient)
                personalized_subject = subject
                personalized_content = base_content
            else:
                # All other cases: personalize for this specific recipient
                personalized_subject, personalized_content = await drafter.personalize_for_recipient(
                    base_letter=base_content,
                    base_subject=subject,
                    recipient=recipient_dict,
                    tone=request.tone,
                    focus=request.focus or "",
                    variation_index=i,
                    writing_profile=writing_profile
                )

            recipient = LetterRecipient(
                id=uuid.uuid4(),
                letter_id=letter.id,
                recipient_name=rep.name,
                recipient_title=rep.title,
                recipient_office_type=rep.office_type,
                recipient_address={
                    'street_1': rep.address.get('street_1', ''),
                    'street_2': rep.address.get('street_2', ''),
                    'city': rep.address.get('city', ''),
                    'state': rep.address.get('state', ''),
                    'zip': rep.address.get('zip', ''),
                    'website': rep.website or ''
                },
                personalized_subject=personalized_subject,
                personalized_content=personalized_content,
                personalization_metadata={
                    'variation_index': i,
                    'personalized': not (i == 0 and request.same_letter_for_all)
                }
            )

            db.add(recipient)

        await db.commit()
        await db.refresh(letter)

        # Get the created recipients
        result = await db.execute(
            select(LetterRecipient).where(LetterRecipient.letter_id == letter.id)
        )
        recipients = result.scalars().all()

        return LetterDetailResponse(
            id=str(letter.id),
            subject=letter.subject,
            base_content=letter.base_content,
            status=letter.status.value,
            tone=letter.tone,
            focus=letter.focus,
            additional_context=letter.additional_context,
            news_articles=letter.news_articles or [],
            ai_model_used=letter.ai_model_used,
            ai_analysis=letter.ai_analysis,
            category=letter.category,
            writing_profile_id=str(letter.writing_profile_id) if letter.writing_profile_id else None,
            writing_profile_name=writing_profile.name if writing_profile else None,
            recipients=[
                {
                    'id': str(r.id),
                    'name': r.recipient_name,
                    'title': r.recipient_title,
                    'office_type': r.recipient_office_type,
                    'personalized_subject': r.personalized_subject,
                    'personalized_content': r.personalized_content
                }
                for r in recipients
            ],
            created_at=letter.created_at,
            updated_at=letter.updated_at,
            finalized_at=letter.finalized_at
        )

    finally:
        await fetcher.close()


@router.post("/{letter_id}/refine")
async def refine_letter(
    letter_id: str,
    request: RefineLetterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Refine a letter based on user feedback"""
    # Get the letter
    result = await db.execute(
        select(Letter).where(
            and_(
                Letter.id == uuid.UUID(letter_id),
                Letter.user_id == current_user.id
            )
        )
    )
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Get writing profile
    writing_profile = None
    if request.writing_profile_id:
        result = await db.execute(
            select(UserWritingProfile).where(
                and_(
                    UserWritingProfile.id == uuid.UUID(request.writing_profile_id),
                    UserWritingProfile.user_id == current_user.id
                )
            )
        )
        writing_profile = result.scalar_one_or_none()
    elif letter.writing_profile_id:
        result = await db.execute(
            select(UserWritingProfile).where(UserWritingProfile.id == letter.writing_profile_id)
        )
        writing_profile = result.scalar_one_or_none()

    # Refine the letter
    drafter = AILetterDrafter()
    refined_content = await drafter.refine_letter(
        original_letter=letter.base_content,
        feedback=request.feedback,
        writing_profile=writing_profile
    )

    # Update the letter
    letter.base_content = refined_content
    letter.updated_at = datetime.utcnow()

    # Update all recipients with refined content (they can be re-personalized later)
    result = await db.execute(
        select(LetterRecipient).where(LetterRecipient.letter_id == letter.id)
    )
    recipients = result.scalars().all()

    for recipient in recipients:
        recipient.personalized_content = refined_content
        recipient.updated_at = datetime.utcnow()

    await db.commit()

    return {
        "message": "Letter refined successfully",
        "refined_content": refined_content
    }


@router.patch("/{letter_id}/recipients/{recipient_id}")
async def update_recipient_content(
    letter_id: str,
    recipient_id: str,
    content: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update the personalized content for a specific recipient"""
    # Get the letter to verify ownership
    result = await db.execute(
        select(Letter).where(
            and_(
                Letter.id == uuid.UUID(letter_id),
                Letter.user_id == current_user.id
            )
        )
    )
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Get the recipient
    result = await db.execute(
        select(LetterRecipient).where(
            and_(
                LetterRecipient.id == uuid.UUID(recipient_id),
                LetterRecipient.letter_id == letter.id
            )
        )
    )
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )

    # Update the recipient's content
    recipient.personalized_content = content
    recipient.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(recipient)

    return {
        "message": "Recipient content updated successfully",
        "recipient_id": str(recipient.id),
        "content": recipient.personalized_content
    }


@router.post("/improve-text")
async def improve_text(
    text: str = Body(..., embed=True),
    improvement_type: str = Body(..., embed=True),
    custom_prompt: Optional[str] = Body(None, embed=True),
    current_user: User = Depends(get_current_user)
):
    """
    Improve text using AI based on improvement type
    Types: grammar, persuasive, shorten, expand, custom
    For custom type, provide custom_prompt parameter
    """
    from app.services.ai_letter import AILetterDrafter

    drafter = AILetterDrafter()

    prompts = {
        "grammar": "Fix grammar, spelling, and punctuation errors in the following text. Maintain the original tone and meaning. Return only the corrected text:\n\n",
        "persuasive": "Make the following text more persuasive and compelling while keeping it professional. Maintain the core message. Return only the improved text:\n\n",
        "shorten": "Make the following text more concise while preserving all key points and maintaining professionalism. Return only the shortened text:\n\n",
        "expand": "Expand the following text with more detail and supporting points while maintaining professionalism. Return only the expanded text:\n\n"
    }

    # Handle custom improvement type
    if improvement_type == "custom":
        if not custom_prompt or not custom_prompt.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="custom_prompt is required when improvement_type is 'custom'"
            )
        prompt = f"{custom_prompt.strip()}\n\n{text}"
    elif improvement_type not in prompts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid improvement type. Must be: grammar, persuasive, shorten, expand, or custom"
        )
    else:
        prompt = prompts[improvement_type] + text

    try:
        # Use OpenAI to improve the text

        improved_text = await drafter.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional writing assistant helping to improve civic engagement letters to representatives."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        return {
            "original": text,
            "improved": improved_text.choices[0].message.content.strip(),
            "improvement_type": improvement_type
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to improve text: {str(e)}"
        )


@router.get("/", response_model=List[LetterResponse])
async def list_letters(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    recipient_name: Optional[str] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's letters grouped by parent letter"""
    # Query Letters with WritingProfile (to avoid N+1 queries)
    query = (
        select(Letter, UserWritingProfile.name)
        .outerjoin(UserWritingProfile, Letter.writing_profile_id == UserWritingProfile.id)
        .where(Letter.user_id == current_user.id)
    )

    if status:
        query = query.where(Letter.status == status)
    if category:
        query = query.where(Letter.category == category)

    # If filtering by recipient name, join with recipients
    if recipient_name:
        query = (
            query
            .join(LetterRecipient, LetterRecipient.letter_id == Letter.id)
            .where(LetterRecipient.recipient_name.contains(recipient_name))
        )

    query = query.order_by(Letter.created_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    rows = result.all()

    # Build response - one item per letter with all recipients
    response_letters = []
    for letter, writing_profile_name in rows:
        # Get all recipients for this letter
        recipients_result = await db.execute(
            select(LetterRecipient)
            .where(LetterRecipient.letter_id == letter.id)
            .order_by(LetterRecipient.recipient_name)
        )
        recipients = recipients_result.scalars().all()

        # Use base_content from letter, or first recipient's content if available
        base_content = letter.base_content
        if not base_content and recipients:
            base_content = recipients[0].personalized_content

        # Calculate word count
        word_count = len(base_content.split()) if base_content else 0

        response_letters.append(
            LetterResponse(
                id=str(letter.id),
                subject=letter.subject,
                base_content=base_content,
                status=letter.status.value,
                tone=letter.tone,
                focus=letter.focus,
                category=letter.category,
                writing_profile_id=str(letter.writing_profile_id) if letter.writing_profile_id else None,
                writing_profile_name=writing_profile_name,
                recipients_count=len(recipients),
                recipients=[
                    {
                        'id': str(recipient.id),
                        'name': recipient.recipient_name,
                        'title': recipient.recipient_title,
                        'office_type': recipient.recipient_office_type,
                        'subject': recipient.personalized_subject or letter.subject,
                        'content': recipient.personalized_content,
                        'email': recipient.recipient_address.get('email', '') if recipient.recipient_address else '',
                        'website': recipient.recipient_address.get('website', '') if recipient.recipient_address else ''
                    }
                    for recipient in recipients
                ],
                word_count=word_count,
                created_at=letter.created_at,
                updated_at=letter.updated_at,
                finalized_at=letter.finalized_at
            )
        )

    return response_letters


@router.get("/{letter_id}", response_model=LetterDetailResponse)
async def get_letter(
    letter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed letter information"""
    result = await db.execute(
        select(Letter).where(
            and_(
                Letter.id == uuid.UUID(letter_id),
                Letter.user_id == current_user.id
            )
        )
    )
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Get recipients
    result = await db.execute(
        select(LetterRecipient).where(LetterRecipient.letter_id == letter.id)
    )
    recipients = result.scalars().all()

    # Get writing profile name
    writing_profile_name = None
    if letter.writing_profile_id:
        result = await db.execute(
            select(UserWritingProfile.name)
            .where(UserWritingProfile.id == letter.writing_profile_id)
        )
        writing_profile_name = result.scalar()

    return LetterDetailResponse(
        id=str(letter.id),
        subject=letter.subject,
        base_content=letter.base_content,
        status=letter.status.value,
        tone=letter.tone,
        focus=letter.focus,
        additional_context=letter.additional_context,
        news_articles=letter.news_articles or [],
        ai_model_used=letter.ai_model_used,
        ai_analysis=letter.ai_analysis,
        category=letter.category,
        writing_profile_id=str(letter.writing_profile_id) if letter.writing_profile_id else None,
        writing_profile_name=writing_profile_name,
        recipients=[
            {
                'id': str(r.id),
                'name': r.recipient_name,
                'title': r.recipient_title,
                'office_type': r.recipient_office_type,
                'personalized_subject': r.personalized_subject,
                'personalized_content': r.personalized_content,
                'delivery_status': r.delivery_status.value if r.delivery_status else None
            }
            for r in recipients
        ],
        created_at=letter.created_at,
        updated_at=letter.updated_at,
        finalized_at=letter.finalized_at
    )


@router.put("/{letter_id}/finalize")
async def finalize_letter(
    letter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Finalize a letter for sending"""
    result = await db.execute(
        select(Letter).where(
            and_(
                Letter.id == uuid.UUID(letter_id),
                Letter.user_id == current_user.id
            )
        )
    )
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    if letter.status != LetterStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft letters can be finalized"
        )

    letter.status = LetterStatus.FINALIZED
    letter.finalized_at = datetime.utcnow()
    letter.updated_at = datetime.utcnow()

    await db.commit()

    return {"message": "Letter finalized successfully"}


@router.patch("/{letter_id}/status")
async def update_letter_status(
    letter_id: str,
    status_update: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update letter status (toggle between draft and finalized)"""
    result = await db.execute(
        select(Letter).where(
            and_(
                Letter.id == uuid.UUID(letter_id),
                Letter.user_id == current_user.id
            )
        )
    )
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    new_status = status_update.get('status', '').lower()

    if new_status == 'finalized':
        letter.status = LetterStatus.FINALIZED
        if not letter.finalized_at:
            letter.finalized_at = datetime.utcnow()
    elif new_status == 'draft':
        letter.status = LetterStatus.DRAFT
        # Optionally clear finalized_at when moving back to draft
        # letter.finalized_at = None
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be 'draft' or 'finalized'"
        )

    letter.updated_at = datetime.utcnow()
    await db.commit()

    return {"message": f"Letter status updated to {new_status}"}


@router.delete("/{letter_id}")
async def delete_letter(
    letter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a letter"""
    result = await db.execute(
        select(Letter).where(
            and_(
                Letter.id == uuid.UUID(letter_id),
                Letter.user_id == current_user.id
            )
        )
    )
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    if letter.status == LetterStatus.SENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete sent letters"
        )

    await db.delete(letter)
    await db.commit()

    return {"message": "Letter deleted successfully"}


# ==================== PDF Generation Endpoints ====================

@router.post("/{letter_id}/recipients/{recipient_id}/generate-pdf")
async def generate_pdf(
    letter_id: str,
    recipient_id: str,
    include_email: bool = Body(False, embed=True),
    include_phone: bool = Body(False, embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate PDF for a specific letter recipient"""
    # Get the letter
    result = await db.execute(
        select(Letter).where(
            and_(
                Letter.id == uuid.UUID(letter_id),
                Letter.user_id == current_user.id
            )
        )
    )
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Get the recipient
    result = await db.execute(
        select(LetterRecipient).where(
            and_(
                LetterRecipient.id == uuid.UUID(recipient_id),
                LetterRecipient.letter_id == letter.id
            )
        )
    )
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )

    # Get sender information from user's primary address
    sender_street_1 = ""
    sender_street_2 = None
    sender_city = ""
    sender_state = ""
    sender_zip = ""

    # Load user addresses explicitly (async)
    from app.models.user import UserAddress
    address_result = await db.execute(
        select(UserAddress).where(UserAddress.user_id == current_user.id)
    )
    addresses = address_result.scalars().all()

    if addresses:
        primary_address = next((a for a in addresses if a.is_primary), addresses[0])
        sender_street_1 = primary_address.street_1
        sender_street_2 = primary_address.street_2
        sender_city = primary_address.city
        sender_state = primary_address.state
        sender_zip = primary_address.zip_code

    # Generate PDF
    pdf_service = PDFService()
    result = await pdf_service.generate_pdf_for_recipient(
        letter_recipient=recipient,
        sender_name=current_user.full_name,
        sender_street_1=sender_street_1,
        sender_street_2=sender_street_2,
        sender_city=sender_city,
        sender_state=sender_state,
        sender_zip=sender_zip,
        sender_email=current_user.email,
        sender_phone=current_user.phone,
        include_email=include_email,
        include_phone=include_phone
    )

    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {result.get('error')}"
        )

    # Update recipient record
    recipient.pdf_generated = True
    recipient.pdf_path = result['pdf_path']
    recipient.pdf_generated_at = datetime.utcnow()

    await db.commit()

    return {
        "message": "PDF generated successfully",
        "pdf_path": result['pdf_path'],
        "pdf_size": result['pdf_size'],
        "filename": result['filename']
    }


@router.post("/{letter_id}/generate-all-pdfs")
async def generate_all_pdfs(
    letter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate PDFs for all recipients of a letter"""
    # Get the letter
    result = await db.execute(
        select(Letter).where(
            and_(
                Letter.id == uuid.UUID(letter_id),
                Letter.user_id == current_user.id
            )
        )
    )
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Get all recipients
    result = await db.execute(
        select(LetterRecipient).where(LetterRecipient.letter_id == letter.id)
    )
    recipients = result.scalars().all()

    if not recipients:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recipients found for this letter"
        )

    # Get sender information
    sender_street_1 = ""
    sender_street_2 = None
    sender_city = ""
    sender_state = ""
    sender_zip = ""

    if current_user.addresses:
        primary_address = next((a for a in current_user.addresses if a.is_primary), current_user.addresses[0])
        sender_street_1 = primary_address.street_1
        sender_street_2 = primary_address.street_2
        sender_city = primary_address.city
        sender_state = primary_address.state
        sender_zip = primary_address.zip_code

    # Generate PDFs for all recipients
    pdf_service = PDFService()
    results = []

    for recipient in recipients:
        result = await pdf_service.generate_pdf_for_recipient(
            letter_recipient=recipient,
            sender_name=current_user.full_name,
            sender_street_1=sender_street_1,
            sender_street_2=sender_street_2,
            sender_city=sender_city,
            sender_state=sender_state,
            sender_zip=sender_zip
        )

        if result['success']:
            recipient.pdf_generated = True
            recipient.pdf_path = result['pdf_path']
            recipient.pdf_generated_at = datetime.utcnow()

            results.append({
                'recipient_id': str(recipient.id),
                'recipient_name': recipient.recipient_name,
                'success': True,
                'pdf_path': result['pdf_path'],
                'filename': result['filename']
            })
        else:
            results.append({
                'recipient_id': str(recipient.id),
                'recipient_name': recipient.recipient_name,
                'success': False,
                'error': result.get('error')
            })

    await db.commit()

    success_count = sum(1 for r in results if r['success'])

    return {
        "message": f"Generated {success_count} of {len(recipients)} PDFs",
        "total_recipients": len(recipients),
        "successful": success_count,
        "failed": len(recipients) - success_count,
        "results": results
    }


@router.get("/{letter_id}/recipients/{recipient_id}/pdf")
async def get_pdf_info(
    letter_id: str,
    recipient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get PDF information for a recipient"""
    # Get the letter
    result = await db.execute(
        select(Letter).where(
            and_(
                Letter.id == uuid.UUID(letter_id),
                Letter.user_id == current_user.id
            )
        )
    )
    letter = result.scalar_one_or_none()

    if not letter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter not found"
        )

    # Get the recipient
    result = await db.execute(
        select(LetterRecipient).where(
            and_(
                LetterRecipient.id == uuid.UUID(recipient_id),
                LetterRecipient.letter_id == letter.id
            )
        )
    )
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )

    if not recipient.pdf_generated or not recipient.pdf_path:
        return {
            "generated": False,
            "message": "PDF has not been generated yet"
        }

    # Check if PDF file exists
    pdf_service = PDFService()
    pdf_path = await pdf_service.get_pdf_path(str(recipient.id))

    if not pdf_path:
        return {
            "generated": False,
            "message": "PDF file not found on disk"
        }

    return {
        "generated": True,
        "pdf_path": recipient.pdf_path,
        "generated_at": recipient.pdf_generated_at,
        "recipient_name": recipient.recipient_name
    }
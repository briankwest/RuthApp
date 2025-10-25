"""
Letter and delivery related models
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Enum as SQLAlchemyEnum, Boolean, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class LetterStatus(str, Enum):
    """Letter status enumeration"""
    DRAFT = "draft"
    FINALIZED = "finalized"
    SENT = "sent"
    ARCHIVED = "archived"


class DeliveryMethod(str, Enum):
    """Delivery method enumeration"""
    PRINT = "print"
    FAX = "fax"
    EMAIL = "email"


class DeliveryStatus(str, Enum):
    """Delivery status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UserWritingProfile(Base):
    """User's writing voice/style profile for personalized letter generation"""
    __tablename__ = "user_writing_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Profile identification
    name = Column(String(100), nullable=False)  # e.g., "Professional Advocate", "Concerned Citizen"
    description = Column(Text, nullable=True)  # User's description of their voice
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # AI-generated voice prompt based on user's examples and preferences
    ai_system_prompt = Column(Text, nullable=True)

    # Voice characteristics (analyzed from samples)
    tone_attributes = Column(JSON, default=dict)  # formal, casual, urgent, passionate
    style_attributes = Column(JSON, default=dict)  # direct, diplomatic, emotional, analytical
    vocabulary_level = Column(String(50), default="standard")  # simple, standard, advanced

    # Writing samples provided by user
    writing_samples = Column(JSON, default=list)  # List of text samples with metadata

    # User preferences
    preferred_tone = Column(String(50), default="professional")
    preferred_length = Column(String(20), default="medium")  # short, medium, long
    include_personal_stories = Column(Boolean, default=True)
    include_data_statistics = Column(Boolean, default=True)
    include_emotional_appeals = Column(Boolean, default=False)
    include_constitutional_arguments = Column(Boolean, default=True)

    # Political stance indicators (optional)
    political_leaning = Column(String(50), nullable=True)  # progressive, conservative, moderate, etc.
    key_issues = Column(JSON, default=list)  # List of issues user cares about (legacy - kept for compatibility)

    # Enhanced issue positions (NEW) - detailed per-issue positions
    # Structure: {issue_key: {position: str, priority: str, personal_connection: str}}
    issue_positions = Column(JSON, default=dict)

    # Core values that guide user's decisions (NEW)
    # Array of values: ["personal_freedom", "social_equality", "fiscal_responsibility", etc.]
    core_values = Column(JSON, default=list)

    # Enhanced argumentative frameworks (NEW)
    # Structure: {framework_key: bool} - e.g., {"constitutional": true, "economic": true, etc.}
    argumentative_frameworks = Column(JSON, default=dict)

    # Representative engagement strategy (NEW)
    # Structure: {
    #   "aligned_approach": str,  # partner, encourage, reinforce
    #   "opposing_approach": str,  # persuade, challenge, appeal_to_values
    #   "bipartisan_framing": str  # always, when_appropriate, rarely
    # }
    representative_engagement = Column(JSON, default=dict)

    # Specific abortion position (NEW)
    abortion_position = Column(String(100), nullable=True)

    # Regional context (NEW)
    # Structure: {"state_concerns": str, "community_type": str}
    regional_context = Column(JSON, default=dict)

    # Compromise positioning (NEW)
    # Structure: {"incremental_progress": str, "bipartisan_preference": str}
    compromise_positioning = Column(JSON, default=dict)

    # Example phrases and keywords to use
    signature_phrases = Column(JSON, default=list)  # Phrases the user commonly uses
    avoid_phrases = Column(JSON, default=list)  # Phrases to avoid

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="writing_profiles")
    letters = relationship("Letter", back_populates="writing_profile")

    # Indexes
    __table_args__ = (
        Index("ix_user_writing_profiles_user_id", "user_id"),
        Index("ix_user_writing_profiles_is_default", "is_default"),
    )

    def __repr__(self):
        return f"<UserWritingProfile {self.name}>"


class Letter(Base):
    """Letter model"""
    __tablename__ = "letters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    writing_profile_id = Column(UUID(as_uuid=True), ForeignKey("user_writing_profiles.id"), nullable=True)

    # Letter metadata
    subject = Column(String(500), nullable=False)
    status = Column(SQLAlchemyEnum(LetterStatus), default=LetterStatus.DRAFT)

    # Generation parameters
    tone = Column(String(50), nullable=True)
    focus = Column(String(500), nullable=True)
    additional_context = Column(Text, nullable=True)
    news_articles = Column(JSON, nullable=True)  # List of article URLs and metadata
    ai_model_used = Column(String(100), nullable=True)
    ai_prompt_used = Column(Text, nullable=True)  # Track the actual prompt sent to AI
    ai_analysis = Column(Text, nullable=True)  # AI's analysis of the articles

    # Full context data for AI-assisted edits
    context_data = Column(JSON, nullable=True)  # Complete context including stories, stats, arguments used

    # Base letter content (template)
    base_content = Column(Text, nullable=False)

    # Letter metadata
    category = Column(String(100), nullable=True)  # Agriculture, Healthcare, etc.
    reference_id = Column(String(100), unique=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    finalized_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="letters")
    writing_profile = relationship("UserWritingProfile", back_populates="letters")
    recipients = relationship("LetterRecipient", back_populates="letter", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_letters_user_id_status", "user_id", "status"),
        Index("ix_letters_reference_id", "reference_id"),
    )

    def __repr__(self):
        return f"<Letter {self.subject}>"


class LetterRecipient(Base):
    """Letter recipient model - personalized version for each recipient"""
    __tablename__ = "letter_recipients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    letter_id = Column(UUID(as_uuid=True), ForeignKey("letters.id"), nullable=False)

    # Recipient information
    recipient_name = Column(String(255), nullable=False)
    recipient_title = Column(String(100), nullable=False)
    recipient_office_type = Column(String(50), nullable=False)
    recipient_address = Column(JSON, nullable=False)  # Full address object

    # Personalized content
    personalized_subject = Column(String(500), nullable=True)
    personalized_content = Column(Text, nullable=False)
    personalization_metadata = Column(JSON, nullable=True)  # Track what was personalized

    # PDF generation
    pdf_generated = Column(Boolean, default=False)
    pdf_path = Column(String(500), nullable=True)
    pdf_generated_at = Column(DateTime, nullable=True)
    mailer_json = Column(JSON, nullable=True)  # Complete mailer configuration

    # Delivery tracking
    delivery_method = Column(SQLAlchemyEnum(DeliveryMethod), nullable=True)
    delivery_status = Column(SQLAlchemyEnum(DeliveryStatus), default=DeliveryStatus.PENDING)
    delivery_attempts = Column(JSON, nullable=True, default=list)  # List of delivery attempts

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    letter = relationship("Letter", back_populates="recipients")
    delivery_logs = relationship("DeliveryLog", back_populates="recipient", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_letter_recipients_letter_id", "letter_id"),
        Index("ix_letter_recipients_delivery_status", "delivery_status"),
    )

    def __repr__(self):
        return f"<LetterRecipient to {self.recipient_name}>"


class DeliveryLog(Base):
    """Delivery log model - tracks each delivery attempt"""
    __tablename__ = "delivery_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    letter_recipient_id = Column(UUID(as_uuid=True), ForeignKey("letter_recipients.id"), nullable=False)

    # Delivery details
    delivery_method = Column(SQLAlchemyEnum(DeliveryMethod), nullable=False)
    delivery_status = Column(SQLAlchemyEnum(DeliveryStatus), nullable=False)

    # Method-specific details
    delivery_details = Column(JSON, nullable=True)  # API responses, tracking info, etc.

    # For fax
    fax_number = Column(String(20), nullable=True)
    fax_sid = Column(String(100), nullable=True)  # SignalWire SID
    pages_sent = Column(String(10), nullable=True)

    # For email
    email_address = Column(String(255), nullable=True)
    email_message_id = Column(String(255), nullable=True)  # Mailgun message ID

    # Status and tracking
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(String(10), default="0")

    # Cost tracking (if applicable)
    cost_amount = Column(String(20), nullable=True)
    cost_currency = Column(String(3), default="USD")

    # Relationships
    recipient = relationship("LetterRecipient", back_populates="delivery_logs")

    # Indexes
    __table_args__ = (
        Index("ix_delivery_logs_recipient_id", "letter_recipient_id"),
        Index("ix_delivery_logs_method_status", "delivery_method", "delivery_status"),
        Index("ix_delivery_logs_started_at", "started_at"),
    )

    def __repr__(self):
        return f"<DeliveryLog {self.delivery_method} - {self.delivery_status}>"


class NewsArticle(Base):
    """Cached news article model"""
    __tablename__ = "news_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(1000), unique=True, nullable=False, index=True)

    # Article metadata
    title = Column(String(500), nullable=False)
    source = Column(String(255), nullable=True)
    authors = Column(String(500), nullable=True)
    publish_date = Column(DateTime, nullable=True)

    # Content
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)

    # Extraction metadata
    extracted_at = Column(DateTime, default=datetime.utcnow)
    extraction_method = Column(String(50), nullable=True)  # newspaper3k, trafilatura, etc.

    # Cache expiry
    expires_at = Column(DateTime, nullable=False)

    def is_expired(self) -> bool:
        """Check if article cache has expired"""
        return datetime.utcnow() > self.expires_at
"""
User and authentication related models
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Index, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


# Association table for user saved representatives
user_representatives = Table(
    'user_representatives',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('representative_id', UUID(as_uuid=True), ForeignKey('representatives.id'), primary_key=True),
    Column('saved_at', DateTime, default=datetime.utcnow)
)


class User(Base):
    """User account model"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)

    email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Email verification tokens
    email_verification_token = Column(String(255), nullable=True, index=True)
    email_verification_token_expires = Column(DateTime, nullable=True)

    # Password reset tokens
    password_reset_token = Column(String(255), nullable=True, index=True)
    password_reset_token_expires = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    addresses = relationship("UserAddress", back_populates="user", cascade="all, delete-orphan")
    letters = relationship("Letter", back_populates="user", cascade="all, delete-orphan")
    writing_profiles = relationship("UserWritingProfile", back_populates="user", cascade="all, delete-orphan")
    saved_representatives = relationship(
        "Representative",
        secondary=user_representatives,
        backref="saved_by_users"
    )

    def __repr__(self):
        return f"<User {self.email}>"

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"


class UserAddress(Base):
    """User address model"""
    __tablename__ = "user_addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    street_1 = Column(String(255), nullable=False)
    street_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)
    zip_code = Column(String(10), nullable=False)

    is_primary = Column(Boolean, default=False)
    label = Column(String(50), nullable=True)  # e.g., "Home", "Work"

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="addresses")

    # Indexes
    __table_args__ = (
        Index("ix_user_addresses_user_id_is_primary", "user_id", "is_primary"),
    )

    def __repr__(self):
        return f"<UserAddress {self.street_1}, {self.city}, {self.state}>"

    @property
    def full_address(self) -> str:
        """Get full formatted address"""
        lines = [self.street_1]
        if self.street_2:
            lines.append(self.street_2)
        lines.append(f"{self.city}, {self.state} {self.zip_code}")
        return ", ".join(lines)

    @property
    def address_line_1(self) -> str:
        """Get first line of address"""
        return self.street_1

    @property
    def address_line_2(self) -> str:
        """Get second line of address (city, state, zip)"""
        return f"{self.city}, {self.state} {self.zip_code}"


class PasswordResetToken(Base):
    """Password reset token model"""
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def is_valid(self) -> bool:
        """Check if token is still valid"""
        if self.used_at:
            return False
        return datetime.utcnow() < self.expires_at


class EmailVerificationToken(Base):
    """Email verification token model"""
    __tablename__ = "email_verification_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def is_valid(self) -> bool:
        """Check if token is still valid"""
        if self.verified_at:
            return False
        return datetime.utcnow() < self.expires_at
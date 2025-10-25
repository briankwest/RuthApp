"""
Geocoding and representative cache models
"""
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Float, DateTime, JSON, Index, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.core.config import settings


class GeocodingCache(Base):
    """Cache for Geocod.io API responses"""
    __tablename__ = "geocoding_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    address_hash = Column(String(64), unique=True, nullable=False, index=True)
    full_address = Column(Text, nullable=False)

    # Geocoding results
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    formatted_address = Column(String(500), nullable=True)
    accuracy = Column(Float, nullable=True)
    accuracy_type = Column(String(50), nullable=True)

    # Raw API response
    geocodio_response = Column(JSON, nullable=False)

    # Congressional districts
    congressional_district = Column(String(10), nullable=True)
    state_legislative_districts = Column(JSON, nullable=True)  # {"house": "1", "senate": "2"}

    # Cached representatives
    representatives = Column(JSON, nullable=True)  # Full representative data

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    # Indexes for efficient querying
    __table_args__ = (
        Index("ix_geocoding_cache_expires_at", "expires_at"),
        Index("ix_geocoding_cache_lat_lng", "latitude", "longitude"),
    )

    def __init__(self, **kwargs):
        """Initialize with default expiration"""
        super().__init__(**kwargs)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(seconds=settings.geocoding_cache_ttl)

    @classmethod
    def generate_address_hash(cls, street: str, city: str, state: str, zip_code: str) -> str:
        """Generate hash for address lookup"""
        # Normalize address components
        normalized = f"{street.lower().strip()},{city.lower().strip()},{state.upper().strip()},{zip_code.strip()}"
        return hashlib.sha256(normalized.encode()).hexdigest()

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.utcnow() > self.expires_at

    def get_representatives(self) -> Optional[Dict[str, Any]]:
        """Get representatives data if not expired"""
        if self.is_expired():
            return None
        return self.representatives


class Representative(Base):
    """Cached representative information"""
    __tablename__ = "representatives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identification
    bioguide_id = Column(String(10), nullable=True, index=True)  # Federal officials
    state_id = Column(String(50), nullable=True, index=True)  # State officials

    # Basic info
    full_name = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    suffix = Column(String(10), nullable=True)

    # Position
    title = Column(String(100), nullable=False)  # Senator, Representative, etc.
    office_type = Column(String(50), nullable=False)  # federal_senate, federal_house, state_senate, etc.
    state = Column(String(2), nullable=False)
    district = Column(String(10), nullable=True)  # For house members
    party = Column(String(50), nullable=True)

    # Contact information (can have multiple offices)
    offices = Column(JSON, nullable=False)  # List of office addresses
    phone = Column(String(20), nullable=True)
    fax = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)

    # Social media
    twitter = Column(String(100), nullable=True)
    facebook = Column(String(100), nullable=True)
    youtube = Column(String(100), nullable=True)

    # Additional data
    photo_url = Column(String(500), nullable=True)
    biography = Column(Text, nullable=True)
    committees = Column(JSON, nullable=True)

    # Metadata
    data_source = Column(String(50), nullable=False)  # geocodio, manual, etc.
    last_updated = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("ix_representatives_office_type_state", "office_type", "state"),
        Index("ix_representatives_state_district", "state", "district"),
        Index("ix_representatives_expires_at", "expires_at"),
    )

    def __init__(self, **kwargs):
        """Initialize with default expiration"""
        super().__init__(**kwargs)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(seconds=settings.representative_cache_ttl)

    def is_expired(self) -> bool:
        """Check if representative data has expired"""
        return datetime.utcnow() > self.expires_at

    @property
    def display_name(self) -> str:
        """Get formatted display name"""
        return f"{self.title} {self.full_name}"

    @property
    def primary_office(self) -> Optional[Dict[str, Any]]:
        """Get primary office address"""
        if self.offices and len(self.offices) > 0:
            # Prefer DC office for federal, capitol for state
            for office in self.offices:
                if self.office_type.startswith("federal") and office.get("city") == "Washington":
                    return office
                if self.office_type.startswith("state") and office.get("is_capitol"):
                    return office
            # Return first office if no preference matched
            return self.offices[0]
        return None

    @property
    def name(self) -> str:
        """Alias for full_name for compatibility"""
        return self.full_name

    @property
    def address(self) -> Dict[str, Any]:
        """Get primary office address in standard format"""
        office = self.primary_office
        if office:
            return {
                'street_1': office.get('street_1', office.get('address', '')),
                'street_2': office.get('street_2', office.get('address_2')),
                'city': office.get('city', ''),
                'state': office.get('state', self.state),
                'zip': office.get('zip', ''),
                'organization': office.get('name')
            }
        return {
            'street_1': '',
            'city': '',
            'state': self.state,
            'zip': ''
        }

    def get_available_delivery_methods(self) -> Dict[str, Any]:
        """
        Check which delivery methods are available for this representative

        Returns:
            Dictionary with available methods and contact info
        """
        methods = {
            'print': True,  # Always available
            'fax': False,
            'email': False,
            'fax_number': None,
            'email_address': None
        }

        # Check for fax number
        if self.fax:
            # Basic validation - has digits
            fax_cleaned = self.fax.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if fax_cleaned and any(c.isdigit() for c in fax_cleaned):
                methods['fax'] = True
                methods['fax_number'] = self.fax

        # Check for email
        if self.email:
            # Basic validation - contains @
            if '@' in self.email and '.' in self.email:
                methods['email'] = True
                methods['email_address'] = self.email

        return methods
"""
Configuration management for the Ruth application
"""
import os
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = Field(default="Ruth - Civic Letter Platform")
    app_version: str = Field(default="1.0.2")
    debug: bool = Field(default=False)
    secret_key: str = Field(..., min_length=32)
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"])
    cors_origins: List[str] = Field(default=["http://localhost:3000"])

    # Database
    database_url: str = Field(...)
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=40)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_prefix: str = Field(default="ruth:")

    # JWT
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)

    # OpenAI
    openai_api_key: str = Field(...)
    openai_model: str = Field(default="gpt-4-turbo-preview")

    # Geocod.io
    geocodio_api_key: str = Field(...)
    geocodio_version: str = Field(default="1.7")

    # Google Maps API
    google_maps_api_key: Optional[str] = Field(default=None)

    # Amazon Web Services
    aws_access_key_id: Optional[str] = Field(default=None)
    aws_secret_access_key: Optional[str] = Field(default=None)
    aws_region: str = Field(default="us-east-1")

    # Amazon SES
    ses_from_email: Optional[str] = Field(default=None)
    ses_from_name: str = Field(default="Ruth Platform")
    ses_configuration_set: Optional[str] = Field(default=None)
    ses_verified_domain: Optional[str] = Field(default=None)

    # Amazon S3
    s3_bucket_name: Optional[str] = Field(default=None)
    s3_bucket_region: str = Field(default="us-east-1")
    s3_public_url: Optional[str] = Field(default=None)

    # SignalWire
    signalwire_project_id: Optional[str] = Field(default=None)
    signalwire_token: Optional[str] = Field(default=None)
    signalwire_space_url: Optional[str] = Field(default=None)
    signalwire_fax_from: Optional[str] = Field(default=None)

    # File Storage
    upload_dir: str = Field(default="./uploads")
    max_upload_size: int = Field(default=10485760)  # 10MB
    allowed_extensions: List[str] = Field(default=["pdf", "png", "jpg", "jpeg"])

    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    # Security
    bcrypt_rounds: int = Field(default=12)
    rate_limit_per_minute: int = Field(default=60)

    # Email (SMTP for notifications via SES)
    smtp_host: Optional[str] = Field(default=None)
    smtp_port: int = Field(default=587)
    smtp_username: Optional[str] = Field(default=None)
    smtp_password: Optional[str] = Field(default=None)
    smtp_from_email: Optional[str] = Field(default=None)

    # Sentry
    sentry_dsn: Optional[str] = Field(default=None)

    # Feature Flags
    enable_registration: bool = Field(default=True)
    enable_fax_delivery: bool = Field(default=True)
    enable_email_delivery: bool = Field(default=True)
    require_email_verification: bool = Field(default=True)

    # Cache TTL (in seconds)
    geocoding_cache_ttl: int = Field(default=2592000)  # 30 days
    representative_cache_ttl: int = Field(default=604800)  # 7 days
    session_cache_ttl: int = Field(default=3600)  # 1 hour

    @validator("allowed_hosts", "cors_origins", pre=True)
    def parse_comma_separated_list(cls, v):
        """Parse comma-separated strings into lists"""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v

    @validator("database_url")
    def validate_database_url(cls, v):
        """Ensure database URL is properly formatted"""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("Database URL must be a PostgreSQL URL")
        return v

    @property
    def async_database_url(self) -> str:
        """Convert sync database URL to async"""
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        return self.database_url

    class Config:
        env_file = ".env"
        case_sensitive = False


# Create global settings instance
settings = Settings()


# Derived settings
class DerivedSettings:
    """Settings derived from base configuration"""

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not settings.debug

    @property
    def enable_fax(self) -> bool:
        """Check if fax delivery is enabled and configured"""
        return (
            settings.enable_fax_delivery
            and settings.signalwire_project_id
            and settings.signalwire_token
            and settings.signalwire_space_url
            and settings.signalwire_fax_from
        )

    @property
    def enable_email(self) -> bool:
        """Check if email delivery is enabled and configured with Amazon SES"""
        return (
            settings.enable_email_delivery
            and settings.aws_access_key_id
            and settings.aws_secret_access_key
            and settings.ses_from_email
        )

    @property
    def enable_s3(self) -> bool:
        """Check if S3 storage is configured"""
        return (
            settings.aws_access_key_id
            and settings.aws_secret_access_key
            and settings.s3_bucket_name
        )

    @property
    def uploads_path(self) -> str:
        """Get absolute path for uploads directory"""
        return os.path.abspath(settings.upload_dir)


derived_settings = DerivedSettings()


# Export commonly used settings
__all__ = ["settings", "derived_settings"]
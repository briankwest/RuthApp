"""
Security utilities for authentication and authorization
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.bcrypt_rounds)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT token
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def generate_token() -> str:
    """
    Generate a random secure token for email verification, password reset, etc.
    """
    return secrets.token_urlsafe(32)


def generate_password(length: int = 16) -> str:
    """
    Generate a random password
    """
    return secrets.token_urlsafe(length)


def is_token_expired(token_data: Dict[str, Any]) -> bool:
    """
    Check if a token has expired
    """
    exp = token_data.get("exp")
    if not exp:
        return True

    return datetime.utcnow() > datetime.fromtimestamp(exp)


def create_email_verification_token(user_id: str) -> str:
    """
    Create a token for email verification
    """
    data = {"user_id": user_id, "purpose": "email_verification"}
    token = create_access_token(data, expires_delta=timedelta(days=7))
    return token


def create_password_reset_token(user_id: str) -> str:
    """
    Create a token for password reset
    """
    data = {"user_id": user_id, "purpose": "password_reset"}
    token = create_access_token(data, expires_delta=timedelta(hours=24))
    return token


def validate_token_purpose(token_data: Dict[str, Any], expected_purpose: str) -> bool:
    """
    Validate that a token has the expected purpose
    """
    return token_data.get("purpose") == expected_purpose
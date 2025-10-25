"""
Common dependencies for API endpoints
"""
import uuid
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import decode_token
from app.models.user import User
from app.services.auth import AuthService


# Security scheme for JWT Bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Get current authenticated user from JWT token
    """
    token = credentials.credentials

    # Decode and validate token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    try:
        user = await AuthService.get_current_user(db, uuid.UUID(user_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user with verified email
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_async_session)
) -> Optional[User]:
    """
    Get current user if token is provided (optional authentication)
    """
    if not credentials:
        return None

    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None


# Pagination dependencies
class PaginationParams:
    """Common pagination parameters"""
    def __init__(
        self,
        skip: int = 0,
        limit: int = 20,
        sort_by: Optional[str] = None,
        sort_desc: bool = False
    ):
        self.skip = skip
        self.limit = min(limit, 100)  # Maximum 100 items per page
        self.sort_by = sort_by
        self.sort_desc = sort_desc


# Rate limiting dependency (to be implemented with Redis)
async def rate_limit_check(
    request_ip: str,
    endpoint: str,
    db: AsyncSession = Depends(get_async_session)
) -> bool:
    """
    Check rate limiting for API endpoints
    """
    # TODO: Implement rate limiting with Redis
    return True
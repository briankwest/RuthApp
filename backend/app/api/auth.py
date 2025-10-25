"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.config import settings
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenRefresh,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordChange,
    Token,
    AuthResponse,
    UserResponse,
    MessageResponse,
)
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.services.auth import AuthService
from app.api.dependencies import get_current_active_user
from app.models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Register a new user account

    Requirements:
    - Email must be unique
    - Password must be at least 8 characters
    - Password must contain uppercase, lowercase, and numbers
    """
    if not settings.enable_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is currently disabled"
        )

    return await AuthService.register_user(db, user_data)


@router.post("/login", response_model=AuthResponse)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Login with email and password

    Returns access and refresh tokens
    """
    return await AuthService.login_user(db, login_data)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Refresh access token using refresh token
    """
    return await AuthService.refresh_tokens(db, token_data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout current user

    Note: Since we use stateless JWT, this endpoint is mainly
    for client-side token removal. Consider implementing token
    blacklisting for enhanced security.
    """
    # TODO: Implement token blacklisting in Redis
    return MessageResponse(
        message="Logged out successfully",
        success=True
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information
    """
    return UserResponse.from_orm(current_user)


@router.post("/password/reset-request", response_model=MessageResponse)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Request password reset email

    Note: For security, always returns success even if email doesn't exist
    """
    result = await AuthService.request_password_reset(db, reset_data.email)
    return MessageResponse(
        message=result["message"],
        success=True
    )


@router.post("/password/reset-confirm", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Reset password using token from email
    """
    result = await AuthService.reset_password(
        db,
        reset_data.token,
        reset_data.new_password
    )
    return MessageResponse(
        message=result["message"],
        success=True
    )


@router.post("/password/change", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Change password for authenticated user
    """
    result = await AuthService.change_password(
        db,
        current_user.id,
        password_data.current_password,
        password_data.new_password
    )
    return MessageResponse(
        message=result["message"],
        success=True
    )


@router.get("/email/verify/{token}", response_model=MessageResponse)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Verify email address using token from email
    """
    result = await AuthService.verify_email(db, token)
    return MessageResponse(
        message=result["message"],
        success=True
    )


@router.post("/email/resend-verification", response_model=MessageResponse)
async def resend_verification_email(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Resend email verification link
    """
    if current_user.email_verified:
        return MessageResponse(
            message="Email already verified",
            success=True
        )

    # TODO: Implement resend verification email
    return MessageResponse(
        message="Verification email sent",
        success=True
    )


@router.get("/check-auth", response_model=dict)
async def check_authentication(
    current_user: User = Depends(get_current_active_user)
):
    """
    Check if user is authenticated

    Useful for frontend to verify token validity
    """
    return {
        "authenticated": True,
        "user_id": str(current_user.id),
        "email": current_user.email,
        "email_verified": current_user.email_verified
    }


class UpdateProfileRequest(BaseModel):
    """Update user profile request"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Update user profile information
    """
    from sqlalchemy import select

    # Check if email is being changed and is already in use
    if profile_data.email and profile_data.email != current_user.email:
        result = await db.execute(
            select(User).where(User.email == profile_data.email)
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        current_user.email = profile_data.email
        current_user.email_verified = False  # Require re-verification

    # Update other fields if provided
    if profile_data.first_name is not None:
        current_user.first_name = profile_data.first_name
    if profile_data.last_name is not None:
        current_user.last_name = profile_data.last_name
    if profile_data.phone is not None:
        current_user.phone = profile_data.phone

    await db.commit()
    await db.refresh(current_user)

    return UserResponse.from_orm(current_user)
"""
Authentication API endpoints
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
    DeleteAccountRequest,
    DeletionSummary,
)
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.services.auth import AuthService
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.core.security import decode_token, blacklist_token


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
    current_user: User = Depends(get_current_active_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout current user

    Blacklists the current access token in Redis so it cannot be reused.
    The token will remain blacklisted until its natural expiration.
    """
    # Get the token and decode it to extract JTI and expiration
    token = credentials.credentials
    payload = decode_token(token)

    if payload:
        jti = payload.get("jti")
        exp = payload.get("exp")

        if jti and exp:
            # Calculate remaining time until token expiration
            expires_at = datetime.fromtimestamp(exp)
            now = datetime.utcnow()
            remaining_seconds = int((expires_at - now).total_seconds())

            # Only blacklist if token hasn't expired yet
            if remaining_seconds > 0:
                await blacklist_token(jti, remaining_seconds)

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


@router.get("/me/deletion-summary", response_model=DeletionSummary)
async def get_deletion_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get a summary of data that will be deleted with account

    Returns counts of all user-related data:
    - Writing profiles
    - Letters (total, draft, finalized)
    - Saved representatives
    - Addresses
    """
    from sqlalchemy import select, func
    from app.models.letter import Letter, UserWritingProfile
    from app.models.user import UserAddress, user_representatives

    # Count writing profiles
    writing_profiles_result = await db.execute(
        select(func.count()).select_from(UserWritingProfile).where(UserWritingProfile.user_id == current_user.id)
    )
    writing_profiles_count = writing_profiles_result.scalar() or 0

    # Count total letters
    letters_result = await db.execute(
        select(func.count()).select_from(Letter).where(Letter.user_id == current_user.id)
    )
    letters_count = letters_result.scalar() or 0

    # Count draft letters
    draft_letters_result = await db.execute(
        select(func.count()).select_from(Letter).where(
            Letter.user_id == current_user.id,
            Letter.status == "draft"
        )
    )
    draft_letters_count = draft_letters_result.scalar() or 0

    # Count finalized letters
    finalized_letters_result = await db.execute(
        select(func.count()).select_from(Letter).where(
            Letter.user_id == current_user.id,
            Letter.status == "finalized"
        )
    )
    finalized_letters_count = finalized_letters_result.scalar() or 0

    # Count saved representatives
    representatives_result = await db.execute(
        select(func.count()).select_from(user_representatives).where(
            user_representatives.c.user_id == current_user.id
        )
    )
    representatives_count = representatives_result.scalar() or 0

    # Count addresses
    addresses_result = await db.execute(
        select(func.count()).select_from(UserAddress).where(UserAddress.user_id == current_user.id)
    )
    addresses_count = addresses_result.scalar() or 0

    return DeletionSummary(
        email=current_user.email,
        writing_profiles_count=writing_profiles_count,
        letters_count=letters_count,
        draft_letters_count=draft_letters_count,
        finalized_letters_count=finalized_letters_count,
        representatives_count=representatives_count,
        addresses_count=addresses_count
    )


@router.delete("/me", response_model=MessageResponse)
async def delete_account(
    request: DeleteAccountRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Permanently delete user account and all associated data

    This action is immediate and cannot be undone.
    Requires password confirmation for security.

    Deletes:
    - All letters and letter recipients
    - All writing profiles
    - All saved representatives associations
    - All user addresses
    - User account itself
    """
    from sqlalchemy import delete, select
    from app.models.letter import Letter, LetterRecipient, UserWritingProfile
    from app.models.user import UserAddress, user_representatives
    from app.core.security import verify_password
    import logging

    logger = logging.getLogger(__name__)

    # Verify password
    if not verify_password(request.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )

    try:
        # All deletions in a single transaction (session already has transaction from dependency)
        # 1. Delete letter recipients first (foreign key to letters)
        # Get all letter IDs for this user
        letters_subquery = select(Letter.id).where(Letter.user_id == current_user.id).scalar_subquery()

        await db.execute(
            delete(LetterRecipient).where(LetterRecipient.letter_id.in_(letters_subquery))
        )

        # 2. Delete letters
        await db.execute(delete(Letter).where(Letter.user_id == current_user.id))

        # 3. Delete saved representatives (junction table)
        await db.execute(delete(user_representatives).where(user_representatives.c.user_id == current_user.id))

        # 4. Delete user addresses
        await db.execute(delete(UserAddress).where(UserAddress.user_id == current_user.id))

        # 5. Delete writing profiles
        await db.execute(delete(UserWritingProfile).where(UserWritingProfile.user_id == current_user.id))

        # 6. Delete user account
        await db.execute(delete(User).where(User.id == current_user.id))

        # Commit all deletions
        await db.commit()

        # Log deletion (without PII) for audit trail
        logger.info(f"User account deleted: user_id={current_user.id}, email_domain={current_user.email.split('@')[1] if '@' in current_user.email else 'unknown'}")

        return MessageResponse(
            message="Account deleted successfully",
            success=True
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete account for user_id={current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account. Please try again later."
        )
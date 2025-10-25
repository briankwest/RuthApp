"""
Authentication service for user management
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.models.user import User, PasswordResetToken, EmailVerificationToken
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_token,
)
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    AuthResponse,
)
from app.core.config import settings


class AuthService:
    """Service for authentication operations"""

    @staticmethod
    async def register_user(
        db: AsyncSession,
        user_data: UserRegister
    ) -> AuthResponse:
        """
        Register a new user
        """
        # Check if user already exists
        stmt = select(User).where(User.email == user_data.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        hashed_password = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            email_verified=not settings.require_email_verification,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Create email verification token if required
        if settings.require_email_verification:
            verification_token = EmailVerificationToken(
                user_id=new_user.id,
                token=generate_token(),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.add(verification_token)
            await db.commit()

            # TODO: Send verification email via Celery task

        # Generate tokens
        access_token = create_access_token(
            data={"sub": str(new_user.id), "email": new_user.email}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(new_user.id), "email": new_user.email}
        )

        return AuthResponse(
            user=UserResponse.from_orm(new_user),
            tokens=Token(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=settings.access_token_expire_minutes * 60
            ),
            message="Registration successful. Please verify your email."
                    if settings.require_email_verification
                    else "Registration successful"
        )

    @staticmethod
    async def login_user(
        db: AsyncSession,
        login_data: UserLogin
    ) -> AuthResponse:
        """
        Authenticate user and return tokens
        """
        # Find user by email
        stmt = select(User).where(User.email == login_data.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        # Verify user exists and password is correct
        if not user or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )

        # Check email verification
        if settings.require_email_verification and not user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please check your email."
            )

        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()

        # Generate tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )

        return AuthResponse(
            user=UserResponse.from_orm(user),
            tokens=Token(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=settings.access_token_expire_minutes * 60
            ),
            message="Login successful"
        )

    @staticmethod
    async def refresh_tokens(
        db: AsyncSession,
        refresh_token: str
    ) -> Token:
        """
        Refresh access token using refresh token
        """
        # Decode refresh token
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        # Verify user exists and is active
        stmt = select(User).where(User.id == uuid.UUID(user_id))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Generate new tokens
        new_access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )

    @staticmethod
    async def request_password_reset(
        db: AsyncSession,
        email: str
    ) -> dict:
        """
        Create password reset token and send email
        """
        # Find user by email
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # Don't reveal if email exists
            return {
                "message": "If the email exists, a password reset link has been sent"
            }

        # Create reset token
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=generate_token(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(reset_token)
        await db.commit()

        # TODO: Send password reset email via Celery task

        return {
            "message": "If the email exists, a password reset link has been sent"
        }

    @staticmethod
    async def reset_password(
        db: AsyncSession,
        token: str,
        new_password: str
    ) -> dict:
        """
        Reset password using token
        """
        # Find valid token
        stmt = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token == token,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > datetime.utcnow()
            )
        )
        result = await db.execute(stmt)
        reset_token = result.scalar_one_or_none()

        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        # Find user
        stmt = select(User).where(User.id == reset_token.user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update password
        user.password_hash = hash_password(new_password)
        reset_token.used_at = datetime.utcnow()

        await db.commit()

        return {"message": "Password reset successful"}

    @staticmethod
    async def verify_email(
        db: AsyncSession,
        token: str
    ) -> dict:
        """
        Verify email using token
        """
        # Find valid token
        stmt = select(EmailVerificationToken).where(
            and_(
                EmailVerificationToken.token == token,
                EmailVerificationToken.verified_at.is_(None),
                EmailVerificationToken.expires_at > datetime.utcnow()
            )
        )
        result = await db.execute(stmt)
        verification_token = result.scalar_one_or_none()

        if not verification_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )

        # Find user
        stmt = select(User).where(User.id == verification_token.user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify email
        user.email_verified = True
        verification_token.verified_at = datetime.utcnow()

        await db.commit()

        return {"message": "Email verified successfully"}

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str
    ) -> dict:
        """
        Change user password
        """
        # Find user
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Update password
        user.password_hash = hash_password(new_password)
        await db.commit()

        return {"message": "Password changed successfully"}

    @staticmethod
    async def get_current_user(
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> User:
        """
        Get current user by ID
        """
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )

        return user
"""Add email verification and password reset tokens

Revision ID: 002
Revises: 001
Create Date: 2025-10-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add email verification and password reset token fields to users table"""

    # Add email verification token columns
    op.add_column('users', sa.Column('email_verification_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('email_verification_token_expires', sa.DateTime(), nullable=True))

    # Add password reset token columns
    op.add_column('users', sa.Column('password_reset_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('password_reset_token_expires', sa.DateTime(), nullable=True))

    # Add indexes for token lookups
    op.create_index('ix_users_email_verification_token', 'users', ['email_verification_token'])
    op.create_index('ix_users_password_reset_token', 'users', ['password_reset_token'])


def downgrade() -> None:
    """Remove email verification and password reset token fields from users table"""

    # Drop indexes
    op.drop_index('ix_users_password_reset_token', table_name='users')
    op.drop_index('ix_users_email_verification_token', table_name='users')

    # Drop columns
    op.drop_column('users', 'password_reset_token_expires')
    op.drop_column('users', 'password_reset_token')
    op.drop_column('users', 'email_verification_token_expires')
    op.drop_column('users', 'email_verification_token')

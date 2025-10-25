"""add enhanced political profile fields

Revision ID: 003
Revises: 002
Create Date: 2025-10-25 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new JSON columns for enhanced political profile data
    op.add_column('user_writing_profiles',
        sa.Column('issue_positions', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'))

    op.add_column('user_writing_profiles',
        sa.Column('core_values', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='[]'))

    op.add_column('user_writing_profiles',
        sa.Column('argumentative_frameworks', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'))

    op.add_column('user_writing_profiles',
        sa.Column('representative_engagement', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'))

    op.add_column('user_writing_profiles',
        sa.Column('regional_context', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'))

    op.add_column('user_writing_profiles',
        sa.Column('compromise_positioning', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'))

    # Add specific abortion position field
    op.add_column('user_writing_profiles',
        sa.Column('abortion_position', sa.String(length=100), nullable=True))


def downgrade() -> None:
    # Remove the columns in reverse order
    op.drop_column('user_writing_profiles', 'abortion_position')
    op.drop_column('user_writing_profiles', 'compromise_positioning')
    op.drop_column('user_writing_profiles', 'regional_context')
    op.drop_column('user_writing_profiles', 'representative_engagement')
    op.drop_column('user_writing_profiles', 'argumentative_frameworks')
    op.drop_column('user_writing_profiles', 'core_values')
    op.drop_column('user_writing_profiles', 'issue_positions')

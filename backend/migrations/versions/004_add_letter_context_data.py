"""add letter context_data field

Revision ID: 004
Revises: 003
Create Date: 2025-10-25 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add context_data column to letters table for storing full generation context
    op.add_column('letters',
        sa.Column('context_data', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    # Remove the column
    op.drop_column('letters', 'context_data')

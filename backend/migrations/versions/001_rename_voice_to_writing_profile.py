"""rename voice to writing profile

Revision ID: 001
Revises:
Create Date: 2025-10-25 14:13:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Rename table from user_voice_profiles to user_writing_profiles
    op.rename_table('user_voice_profiles', 'user_writing_profiles')

    # 2. Rename the foreign key column in letters table
    op.alter_column(
        'letters',
        'voice_profile_id',
        new_column_name='writing_profile_id',
        existing_type=sa.dialects.postgresql.UUID(),
        existing_nullable=True
    )

    # 3. Update index names
    # Drop old indexes
    op.drop_index('ix_user_voice_profiles_user_id', table_name='user_writing_profiles')
    op.drop_index('ix_user_voice_profiles_is_default', table_name='user_writing_profiles')

    # Create new indexes with updated names
    op.create_index('ix_user_writing_profiles_user_id', 'user_writing_profiles', ['user_id'])
    op.create_index('ix_user_writing_profiles_is_default', 'user_writing_profiles', ['is_default'])

    # 4. Drop and recreate the foreign key constraint with new name
    # PostgreSQL automatically updates FK constraint names when the table is renamed,
    # but we need to explicitly handle the column rename
    op.drop_constraint('fk_letters_voice_profile_id_user_voice_profiles', 'letters', type_='foreignkey')
    op.create_foreign_key(
        'fk_letters_writing_profile_id_user_writing_profiles',
        'letters', 'user_writing_profiles',
        ['writing_profile_id'], ['id']
    )


def downgrade() -> None:
    # Reverse the operations in reverse order

    # 1. Restore foreign key constraint
    op.drop_constraint('fk_letters_writing_profile_id_user_writing_profiles', 'letters', type_='foreignkey')
    op.create_foreign_key(
        'fk_letters_voice_profile_id_user_voice_profiles',
        'letters', 'user_voice_profiles',
        ['voice_profile_id'], ['id']
    )

    # 2. Restore index names
    op.drop_index('ix_user_writing_profiles_is_default', table_name='user_writing_profiles')
    op.drop_index('ix_user_writing_profiles_user_id', table_name='user_writing_profiles')

    op.create_index('ix_user_voice_profiles_is_default', 'user_voice_profiles', ['is_default'])
    op.create_index('ix_user_voice_profiles_user_id', 'user_voice_profiles', ['user_id'])

    # 3. Restore column name
    op.alter_column(
        'letters',
        'writing_profile_id',
        new_column_name='voice_profile_id',
        existing_type=sa.dialects.postgresql.UUID(),
        existing_nullable=True
    )

    # 4. Restore table name
    op.rename_table('user_writing_profiles', 'user_voice_profiles')

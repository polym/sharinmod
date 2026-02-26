"""Change provider column from enum to varchar for dynamic provider support

Revision ID: 20260226_change_provider_to_varchar
Revises: 20260213_add_error_details_to_usage_logs
Create Date: 2026-02-26

This migration changes the provider column from using the apikeyprovider enum
to a varchar type, enabling support for dynamically added providers from the
database without requiring schema migrations for each new provider.

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260226_change_provider_to_varchar'
down_revision: Union[str, None] = '20260213_add_error_details_to_usage_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change provider column from enum to varchar"""
    # Step 1: Add a new temporary varchar column
    op.add_column('shared_api_keys',
                  sa.Column('provider_new', sa.String(length=100), nullable=True))

    # Step 2: Copy data from old column to new column
    op.execute("UPDATE shared_api_keys SET provider_new = provider::text")

    # Step 3: Make the new column NOT NULL
    op.execute("UPDATE shared_api_keys SET provider_new = 'bigmodel' WHERE provider_new IS NULL")
    op.alter_column('shared_api_keys', 'provider_new',
                    existing_type=sa.String(length=100),
                    nullable=False)

    # Step 4: Drop the old enum column and rename the new one
    op.drop_column('shared_api_keys', 'provider')
    op.alter_column('shared_api_keys', 'provider_new',
                    existing_type=sa.String(length=100),
                    new_column_name='provider')


def downgrade() -> None:
    """Revert back to enum type"""
    # Step 1: Add a new enum column
    op.add_column('shared_api_keys',
                  sa.Column('provider_old',
                            sa.Enum('BIGMODEL', 'ZAI', 'VOLCENGINE', 'MOONSHOT', 'MINIMAX', 'OPENROUTER',
                                   name='apikeyprovider', schema='public'),
                            nullable=True))

    # Step 2: Copy data, filtering to valid enum values only
    op.execute("""
        UPDATE shared_api_keys
        SET provider_old = provider::apikeyprovider
        WHERE provider IN ('bigmodel', 'z.ai', 'volcengine', 'moonshot', 'minimax', 'openrouter')
    """)

    # Step 3: Make NOT NULL and drop the varchar column
    op.execute("UPDATE shared_api_keys SET provider_old = 'BIGMODEL' WHERE provider_old IS NULL")
    op.alter_column('shared_api_keys', 'provider_old', nullable=False)
    op.drop_column('shared_api_keys', 'provider')
    op.alter_column('shared_api_keys', 'provider_old', new_column_name='provider')

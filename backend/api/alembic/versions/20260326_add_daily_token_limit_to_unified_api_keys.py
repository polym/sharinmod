"""Add daily_token_limit fields to unified_api_keys table and add DAILY_LIMIT_EXCEEDED status

Revision ID: 20260326_add_daily_token_limit_to_unified_api_keys
Revises: 20260326_add_system_settings
Create Date: 2026-03-26

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260326_add_daily_token_limit_to_unified_api_keys'
down_revision: Union[str, None] = '20260326_add_system_settings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to unified_api_keys table
    op.add_column('unified_api_keys', sa.Column('daily_token_limit', sa.Integer(), nullable=True))
    op.add_column('unified_api_keys', sa.Column('daily_tokens_used', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('unified_api_keys', sa.Column('last_reset_date', sa.Date(), nullable=True))

    # Add DAILY_LIMIT_EXCEEDED to the apikeystatus enum type
    # Using IF NOT EXISTS to avoid errors if the value already exists
    op.execute("ALTER TYPE apikeystatus ADD VALUE IF NOT EXISTS 'daily_limit_exceeded'")


def downgrade() -> None:
    # Remove columns (note: we can't remove enum values in PostgreSQL)
    op.drop_column('unified_api_keys', 'last_reset_date')
    op.drop_column('unified_api_keys', 'daily_tokens_used')
    op.drop_column('unified_api_keys', 'daily_token_limit')

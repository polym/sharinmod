"""Add last_used_at column to unified_api_keys table

Revision ID: 20260204_add_last_used_at_to_unified_api_keys
Revises: 20260206_add_client_to_usage_logs
Create Date: 2026-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '20260204_add_last_used_at_to_unified_api_keys'
down_revision: Union[str, None] = '20260206_add_client_to_usage_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add last_used_at column (nullable)
    op.add_column('unified_api_keys', sa.Column('last_used_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Drop column
    op.drop_column('unified_api_keys', 'last_used_at')

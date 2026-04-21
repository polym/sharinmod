"""Add rate limit fields to shared_api_keys

Revision ID: 20260420_add_rate_limit_fields
Revises: 20260417_add_personal_org
Create Date: 2026-04-20

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260420_add_rate_limit_fields'
down_revision: Union[str, None] = '20260417_add_personal_org'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add rate limit reset time column (indexed for efficient queries)
    op.add_column('shared_api_keys', sa.Column('rate_limit_reset_at', sa.DateTime(timezone=True), nullable=True, index=True))
    # Add backup column for user-selected models (for auto-recovery)
    op.add_column('shared_api_keys', sa.Column('rate_limit_models_backup', sa.String(length=1000), nullable=True))


def downgrade() -> None:
    # Remove rate limit fields
    op.drop_column('shared_api_keys', 'rate_limit_models_backup')
    op.drop_column('shared_api_keys', 'rate_limit_reset_at')

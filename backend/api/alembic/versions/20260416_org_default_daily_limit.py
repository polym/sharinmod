"""Add default_daily_token_limit to organizations table

Revision ID: 20260416_org_default_daily_limit
Revises: 20260415_convert_timestamp_to_timestamptz
Create Date: 2026-04-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260416_org_default_daily_limit'
down_revision: Union[str, None] = '20260415_convert_timestamp_to_timestamptz'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add default_daily_token_limit column to organizations table
    op.add_column(
        'organizations',
        sa.Column('default_daily_token_limit', sa.BigInteger(), nullable=True)
    )


def downgrade() -> None:
    # Remove default_daily_token_limit column from organizations table
    op.drop_column('organizations', 'default_daily_token_limit')

"""Add system_settings table

Revision ID: 20260326_add_system_settings
Revises: 20260323_add_chat_tool_to_claws
Create Date: 2026-03-26

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import datetime, timezone

revision: str = '20260326_add_system_settings'
down_revision: Union[str, None] = '20260323_add_chat_tool_to_claws'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create system_settings table
    op.create_table(
        'system_settings',
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.String(length=1000), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('key')
    )

    # Insert default configuration
    system_settings_table = table('system_settings',
        column('key', sa.String),
        column('value', sa.String),
        column('description', sa.String),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime)
    )

    op.bulk_insert(system_settings_table, [
        {
            'key': 'default_daily_token_limit',
            'value': '100000',
            'description': 'Default daily token limit for new API keys',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
    ])


def downgrade() -> None:
    op.drop_table('system_settings')

"""Create api_key_limit_history table

Revision ID: 20260326_create_api_key_limit_history
Revises: 20260326_add_daily_token_limit_to_unified_api_keys
Create Date: 2026-03-26

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260326_create_api_key_limit_history'
down_revision: Union[str, None] = '20260326_add_daily_token_limit_to_unified_api_keys'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'api_key_limit_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('unified_api_key_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('token_limit', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['unified_api_key_id'], ['unified_api_keys.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_key_limit_history_unified_api_key_id'), 'api_key_limit_history', ['unified_api_key_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_api_key_limit_history_unified_api_key_id'), table_name='api_key_limit_history')
    op.drop_table('api_key_limit_history')

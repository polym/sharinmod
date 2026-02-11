"""Add trace_id and num_fails columns to usage_logs

Revision ID: 20260211_add_trace_and_num_fails
Revises: 20260210_openrouter
Create Date: 2026-02-11

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260211_add_trace_and_num_fails'
down_revision: Union[str, None] = '20260210_openrouter'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add trace_id column (optional, for linking retry attempts)
    op.add_column('usage_logs', sa.Column('trace_id', sa.String(length=255), nullable=True))
    # Create index on trace_id for better query performance
    op.create_index(op.f('ix_usage_logs_trace_id'), 'usage_logs', ['trace_id'], unique=False)

    # Add num_fails column (integer, defaults to 0)
    op.add_column('usage_logs', sa.Column('num_fails', sa.Integer(), nullable=False, server_default='0'))

def downgrade() -> None:
    # Drop index first
    op.drop_index(op.f('ix_usage_logs_trace_id'), table_name='usage_logs')
    # Drop columns
    op.drop_column('usage_logs', 'num_fails')
    op.drop_column('usage_logs', 'trace_id')

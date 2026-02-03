"""Add usage_logs table for tracking API call usage

Revision ID: 20260202_add_usage_logs
Revises: 20260201_add_subscription_token_stats
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '20260202_add_usage_logs'
down_revision: Union[str, None] = '20260201_add_subscription_token_stats'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create usage_logs table
    op.create_table(
        'usage_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('unified_api_key_id', sa.Integer(), nullable=True),
        sa.Column('unified_api_key_name', sa.String(length=255), nullable=True),
        sa.Column('model_id', sa.String(length=255), nullable=True),
        sa.Column('model_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('total_duration', sa.Float(), nullable=True),
        sa.Column('ttft', sa.Float(), nullable=True),
        sa.Column('subscription_id', sa.Integer(), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=False),
        sa.Column('output_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('request_time', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], name=op.f('fk_usage_logs_subscription_id_subscriptions')),
        sa.ForeignKeyConstraint(['unified_api_key_id'], ['unified_api_keys.id'], name=op.f('fk_usage_logs_unified_api_key_id_unified_api_keys')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_usage_logs_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_usage_logs'))
    )
    # Create indexes
    op.create_index(op.f('ix_usage_logs_user_id_request_time'), 'usage_logs', ['user_id', sa.text('request_time DESC')], unique=False)
    op.create_index(op.f('ix_usage_logs_user_id_status'), 'usage_logs', ['user_id', 'status'], unique=False)
    op.create_index(op.f('ix_usage_logs_request_time'), 'usage_logs', ['request_time'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_usage_logs_request_time'), table_name='usage_logs')
    op.drop_index(op.f('ix_usage_logs_user_id_status'), table_name='usage_logs')
    op.drop_index(op.f('ix_usage_logs_user_id_request_time'), table_name='usage_logs')

    # Drop table
    op.drop_table('usage_logs')

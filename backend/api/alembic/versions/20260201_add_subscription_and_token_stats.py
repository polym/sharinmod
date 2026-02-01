"""Add subscription table and token statistics fields

Revision ID: 20260201_add_subscription_token_stats
Revises: 20260201_add_model_ids
Create Date: 2026-02-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '20260201_add_subscription_token_stats'
down_revision: Union[str, None] = '20260201_add_model_ids'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.String(length=100), nullable=False),
        sa.Column('shared_api_key_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['shared_api_key_id'], ['shared_api_keys.id'], name=op.f('fk_subscriptions_shared_api_key_id_shared_api_keys')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_subscriptions_user_id_users')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_subscriptions')),
        sa.UniqueConstraint('model_id', name=op.f('uq_subscriptions_model_id'))
    )
    op.create_index(op.f('ix_subscriptions_model_id'), 'subscriptions', ['model_id'], unique=True)
    op.create_index(op.f('ix_subscriptions_shared_api_key_id'), 'subscriptions', ['shared_api_key_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'], unique=False)

    # Add consumed_tokens and contributed_tokens to users table
    op.add_column('users', sa.Column('consumed_tokens', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('contributed_tokens', sa.Integer(), nullable=False, server_default='0'))

    # Add api_key_hash, total_requests, total_tokens to shared_api_keys table
    op.add_column('shared_api_keys', sa.Column('api_key_hash', sa.String(length=255), nullable=True))
    op.add_column('shared_api_keys', sa.Column('total_requests', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('shared_api_keys', sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'))

    # Add api_key_hash to unified_api_keys table for callback matching
    op.add_column('unified_api_keys', sa.Column('api_key_hash', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_unified_api_keys_api_key_hash'), 'unified_api_keys', ['api_key_hash'], unique=False)


def downgrade() -> None:
    # Remove columns from shared_api_keys table
    op.drop_column('shared_api_keys', 'total_tokens')
    op.drop_column('shared_api_keys', 'total_requests')
    op.drop_column('shared_api_keys', 'api_key_hash')

    # Remove api_key_hash from unified_api_keys table
    op.drop_index(op.f('ix_unified_api_keys_api_key_hash'), table_name='unified_api_keys')
    op.drop_column('unified_api_keys', 'api_key_hash')

    # Remove columns from users table
    op.drop_column('users', 'contributed_tokens')
    op.drop_column('users', 'consumed_tokens')

    # Drop subscriptions table
    op.drop_index(op.f('ix_subscriptions_user_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_shared_api_key_id'), table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_model_id'), table_name='subscriptions')
    op.drop_table('subscriptions')

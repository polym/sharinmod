"""Add organization isolation to shared_api_keys and subscriptions

Revision ID: 20260407_add_organization_isolation
Revises: 20260407_add_organizations
Create Date: 2026-04-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260407_add_organization_isolation'
down_revision: Union[str, None] = '20260407_add_organizations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add organization_id column to shared_api_keys
    op.add_column('shared_api_keys', sa.Column('organization_id', sa.Integer(), nullable=True))

    # Add foreign key constraint for shared_api_keys.organization_id
    op.create_foreign_key(
        'fk_shared_api_keys_organization_id_organizations',
        'shared_api_keys', 'organizations',
        ['organization_id'], ['id'],
        ondelete='CASCADE'
    )

    # Add index on shared_api_keys.organization_id
    op.create_index('ix_shared_api_keys_organization_id', 'shared_api_keys', ['organization_id'])

    # Drop old unique index and create new one with organization_id
    op.drop_index('idx_user_provider_unique', table_name='shared_api_keys')
    op.create_index(
        'idx_user_provider_unique',
        'shared_api_keys',
        ['user_id', 'provider', 'organization_id'],
        unique=True
    )

    # Add organization_id column to subscriptions
    op.add_column('subscriptions', sa.Column('organization_id', sa.Integer(), nullable=True))

    # Add foreign key constraint for subscriptions.organization_id
    op.create_foreign_key(
        'fk_subscriptions_organization_id_organizations',
        'subscriptions', 'organizations',
        ['organization_id'], ['id'],
        ondelete='CASCADE'
    )

    # Add index on subscriptions.organization_id
    op.create_index('ix_subscriptions_organization_id', 'subscriptions', ['organization_id'])


def downgrade() -> None:
    # Remove organization_id from subscriptions
    op.drop_index('ix_subscriptions_organization_id', table_name='subscriptions')
    op.drop_constraint('fk_subscriptions_organization_id_organizations', 'subscriptions', type_='foreignkey')
    op.drop_column('subscriptions', 'organization_id')

    # Remove organization_id from shared_api_keys
    op.drop_index('idx_user_provider_unique', table_name='shared_api_keys')
    op.create_index(
        'idx_user_provider_unique',
        'shared_api_keys',
        ['user_id', 'provider'],
        unique=True
    )
    op.drop_index('ix_shared_api_keys_organization_id', table_name='shared_api_keys')
    op.drop_constraint('fk_shared_api_keys_organization_id_organizations', 'shared_api_keys', type_='foreignkey')
    op.drop_column('shared_api_keys', 'organization_id')

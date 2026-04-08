"""Add organization_id to shared_api_keys

Revision ID: 20260408_shared_keys_org
Revises: 20260408_merge_heads
Create Date: 2026-04-08

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260408_shared_keys_org'
down_revision: Union[str, None] = '20260408_merge_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('shared_api_keys', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_shared_api_keys_org_id',
        'shared_api_keys', 'organizations',
        ['organization_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_index('ix_shared_api_keys_org_id', 'shared_api_keys', ['organization_id'])
    # Recreate unique index to include organization_id
    op.drop_index('idx_user_provider_unique', table_name='shared_api_keys')
    op.create_index(
        'idx_user_provider_unique',
        'shared_api_keys',
        ['user_id', 'provider', 'organization_id'],
        unique=True
    )


def downgrade() -> None:
    op.drop_index('idx_user_provider_unique', table_name='shared_api_keys')
    op.create_index(
        'idx_user_provider_unique',
        'shared_api_keys',
        ['user_id', 'provider'],
        unique=True
    )
    op.drop_index('ix_shared_api_keys_org_id', table_name='shared_api_keys')
    op.drop_constraint('fk_shared_api_keys_org_id', 'shared_api_keys', type_='foreignkey')
    op.drop_column('shared_api_keys', 'organization_id')

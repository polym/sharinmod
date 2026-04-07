"""Add organization_id to unified_api_keys

Revision ID: 20260407_add_org_to_unified_api_keys
Revises: 20260407_add_organization_isolation
Create Date: 2026-04-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260407_add_org_to_unified_api_keys'
down_revision: Union[str, None] = '20260407_add_organization_isolation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('unified_api_keys', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_unified_api_keys_organization_id_organizations',
        'unified_api_keys', 'organizations',
        ['organization_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_index('ix_unified_api_keys_organization_id', 'unified_api_keys', ['organization_id'])


def downgrade() -> None:
    op.drop_index('ix_unified_api_keys_organization_id', table_name='unified_api_keys')
    op.drop_constraint('fk_unified_api_keys_organization_id_organizations', 'unified_api_keys', type_='foreignkey')
    op.drop_column('unified_api_keys', 'organization_id')

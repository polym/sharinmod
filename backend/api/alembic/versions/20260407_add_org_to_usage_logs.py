"""Add organization_id to usage_logs

Revision ID: 20260407_add_org_to_usage_logs
Revises: 20260407_add_org_to_unified_api_keys
Create Date: 2026-04-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260407_add_org_to_usage_logs'
down_revision: Union[str, None] = '20260407_add_org_to_unified_api_keys'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usage_logs', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_index('ix_usage_logs_organization_id', 'usage_logs', ['organization_id'])
    op.create_foreign_key(
        'fk_usage_logs_organization_id',
        'usage_logs', 'organizations',
        ['organization_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_usage_logs_organization_id', 'usage_logs', type_='foreignkey')
    op.drop_index('ix_usage_logs_organization_id', table_name='usage_logs')
    op.drop_column('usage_logs', 'organization_id')

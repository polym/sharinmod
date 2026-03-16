"""Add unified_api_key_id to claws

Revision ID: 20260316_add_unified_api_key_to_claw
Revises: 20260316_add_claw_table
Create Date: 2026-03-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260316_add_unified_api_key_to_claw'
down_revision: Union[str, None] = '20260316_add_claw_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('claws', sa.Column('unified_api_key_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_claws_unified_api_key_id', 'claws',
        'unified_api_keys', ['unified_api_key_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_claws_unified_api_key_id', 'claws', type_='foreignkey')
    op.drop_column('claws', 'unified_api_key_id')

"""Add base_url and custom_llm_provider to provider_configs

Revision ID: 20260226_add_base_url_provider_configs
Revises: 20260226_change_provider_to_varchar
Create Date: 2026-02-26

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260226_add_base_url_provider_configs'
down_revision: Union[str, None] = '20260226_change_provider_to_varchar'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('provider_configs', sa.Column('base_url', sa.String(500), nullable=True))
    op.add_column('provider_configs', sa.Column('custom_llm_provider', sa.String(50), nullable=False, server_default='openai'))


def downgrade() -> None:
    op.drop_column('provider_configs', 'custom_llm_provider')
    op.drop_column('provider_configs', 'base_url')

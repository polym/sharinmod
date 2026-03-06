"""Add real_model field to provider_models table

Revision ID: 20260307_add_real_model_to_provider_models
Revises: 20260306_add_provider_to_usage_logs
Create Date: 2026-03-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260307_add_real_model_to_provider_models'
down_revision: Union[str, None] = '20260306_add_provider_to_usage_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('provider_models', sa.Column('real_model', sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column('provider_models', 'real_model')
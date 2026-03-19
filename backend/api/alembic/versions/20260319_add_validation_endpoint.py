"""Add validation_endpoint to provider_configs

Revision ID: 20260319_add_validation_endpoint
Revises: 20260318_add_user_selected_models
Create Date: 2026-03-19

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260319_add_validation_endpoint'
down_revision: Union[str, None] = '20260318_add_user_selected_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('provider_configs', sa.Column('validation_endpoint', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('provider_configs', 'validation_endpoint')

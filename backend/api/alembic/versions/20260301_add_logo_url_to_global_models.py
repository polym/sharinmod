"""Add logo_url to global_models table

Revision ID: 20260301_add_logo_url_to_global_models
Revises: 20260227_add_global_models_table
Create Date: 2026-03-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260301_add_logo_url_to_global_models'
down_revision: Union[str, None] = '20260227_add_global_models_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('global_models', sa.Column('logo_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('global_models', 'logo_url')

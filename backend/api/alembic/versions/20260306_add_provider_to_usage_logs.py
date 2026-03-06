"""Add provider column to usage_logs table

Revision ID: 20260306_add_provider_to_usage_logs
Revises: 20260305_add_force_password_change
Create Date: 2026-03-06

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260306_add_provider_to_usage_logs'
down_revision: Union[str, None] = '20260305_add_force_password_change'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usage_logs', sa.Column('provider', sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column('usage_logs', 'provider')

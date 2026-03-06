"""Add force_password_change column to users table

Revision ID: 20260305_add_force_password_change
Revises: 20260301_add_logo_url_to_global_models
Create Date: 2026-03-05

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260305_add_force_password_change'
down_revision: Union[str, None] = '20260301_add_logo_url_to_global_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('force_password_change', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'force_password_change')
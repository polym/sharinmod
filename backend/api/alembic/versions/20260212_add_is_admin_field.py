"""Add is_admin field to users table

Revision ID: 20260212_add_is_admin
Revises: 20260211_add_oauth_columns
Create Date: 2026-02-12

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260212_add_is_admin'
down_revision: Union[str, None] = '20260211_add_oauth_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add is_admin column to users table for admin role management
    # Default value is false for existing users
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))

def downgrade() -> None:
    op.drop_column('users', 'is_admin')

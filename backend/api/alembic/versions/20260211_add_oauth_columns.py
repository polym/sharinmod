"""Add OAuth columns to users table

Revision ID: 20260211_add_oauth_columns
Revises: 20260211_add_trace_and_num_fails
Create Date: 2026-02-11

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260211_add_oauth_columns'
down_revision: Union[str, None] = '20260211_add_trace_and_num_fails'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add oauth_provider column (optional, for 'github', 'google', etc.)
    op.add_column('users', sa.Column('oauth_provider', sa.String(length=50), nullable=True))
    # Add oauth_provider_user_id column (optional, for GitHub user ID, etc.)
    op.add_column('users', sa.Column('oauth_provider_user_id', sa.String(length=255), nullable=True))

def downgrade() -> None:
    # Drop columns
    op.drop_column('users', 'oauth_provider_user_id')
    op.drop_column('users', 'oauth_provider')

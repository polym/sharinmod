"""Make hashed_password nullable to support OAuth users and admin-created users

Revision ID: 20260329_make_hashed_password_nullable
Revises: 598caf8a66fa
Create Date: 2026-03-29

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '20260329_make_hashed_password_nullable'
down_revision: Union[str, None] = '598caf8a66fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Allow NULL values for hashed_password to support:
    # 1. OAuth users (no password required)
    # 2. Admin-created users (password set via reset link)
    op.alter_column('users', 'hashed_password', nullable=True)


def downgrade() -> None:
    # Revert to NOT NULL constraint
    op.alter_column('users', 'hashed_password', nullable=False)

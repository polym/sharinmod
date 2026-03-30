"""Fix is_admin NULL values

Revision ID: 20260330_fix_is_admin_nullable
Revises: 20260329_make_hashed_password_nullable
Create Date: 2026-03-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260330_fix_is_admin_nullable'
down_revision: Union[str, None] = '20260329_make_hashed_password_nullable'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update any NULL is_admin values to False
    op.execute("UPDATE users SET is_admin = FALSE WHERE is_admin IS NULL")
    # Make the column non-nullable
    op.alter_column('users', 'is_admin', nullable=False)


def downgrade() -> None:
    # Revert to nullable (for rollback compatibility)
    op.alter_column('users', 'is_admin', nullable=True)

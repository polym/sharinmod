"""Add user status fields (is_disabled and deleted_at)

Revision ID: 20260326_add_user_status_fields
Revises: 20260326_add_password_reset_tokens
Create Date: 2026-03-26

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260326_add_user_status_fields'
down_revision: Union[str, None] = '20260326_add_password_reset_tokens'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_disabled', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'deleted_at')
    op.drop_column('users', 'is_disabled')

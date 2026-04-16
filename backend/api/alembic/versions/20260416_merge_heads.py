"""Merge head revisions for email registration and org default daily limit

Revision ID: 20260416_merge_heads
Revises:
Create Date: 2026-04-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260416_merge_heads'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = ['20260415_add_email_registration', '20260416_org_default_daily_limit']


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

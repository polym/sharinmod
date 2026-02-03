"""Add client column to usage_logs table

Revision ID: 20260206_add_client_to_usage_logs
Revises: 20260205_add_kind_to_usage_logs
Create Date: 2026-02-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '20260206_add_client_to_usage_logs'
down_revision: Union[str, None] = '20260205_add_kind_to_usage_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add client column (nullable)
    op.add_column('usage_logs', sa.Column('client', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Drop column
    op.drop_column('usage_logs', 'client')

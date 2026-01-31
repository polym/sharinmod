"""Add description field to unified_api_key

Revision ID: 20260131_add_desc
Revises: 0c84d79e5030
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '20260131_add_desc'
down_revision: Union[str, None] = '0c84d79e5030'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add description column to unified_api_keys table
    op.add_column('unified_api_keys', sa.Column('description', sa.String(length=500), nullable=True))


def downgrade() -> None:
    # Remove description column from unified_api_keys table
    op.drop_column('unified_api_keys', 'description')

"""Add volcengine provider

Revision ID: 20260204_add_volcengine_provider
Revises: 20260204_add_last_used_at_to_unified_api_keys
Create Date: 2026-02-04

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260204_add_volcengine_provider'
down_revision: Union[str, None] = '20260204_add_last_used_at_to_unified_api_keys'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add VOLCENGINE to the apikeyprovider enum
    op.execute("ALTER TYPE apikeyprovider ADD VALUE 'VOLCENGINE'")

def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # Would need to recreate the type without VOLCENGINE
    pass

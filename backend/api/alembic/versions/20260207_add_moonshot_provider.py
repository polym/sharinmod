"""Add moonshot provider

Revision ID: 20260207_add_moonshot_provider
Revises: 20260204_add_volcengine_provider
Create Date: 2026-02-05

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260207_add_moonshot_provider'
down_revision: Union[str, None] = '20260204_add_volcengine_provider'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add MOONSHOT to the apikeyprovider enum
    op.execute("ALTER TYPE apikeyprovider ADD VALUE 'MOONSHOT'")

def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # Would need to recreate the type without MOONSHOT
    pass

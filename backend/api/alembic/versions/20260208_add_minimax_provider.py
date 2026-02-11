"""Add minimax provider

Revision ID: 20260208_add_minimax_provider
Revises: 20260207_add_moonshot_provider
Create Date: 2026-02-08

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260208_add_minimax_provider'
down_revision: Union[str, None] = '20260207_add_moonshot_provider'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add MINIMAX to apikeyprovider enum
    op.execute("ALTER TYPE apikeyprovider ADD VALUE IF NOT EXISTS 'MINIMAX'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # Would need to recreate the type without MINIMAX
    pass

"""Add openrouter provider enum

Revision ID: 20260210_openrouter
Revises: 20260208_moonshot_fix
Create Date: 2026-02-10

"""
from typing import Sequence, Union
from alembic import op

revision: str = '20260210_openrouter'
down_revision: Union[str, None] = '20260208_moonshot_fix'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add OPENROUTER to the apikeyprovider enum
    op.execute("ALTER TYPE apikeyprovider ADD VALUE IF NOT EXISTS 'OPENROUTER'")

def downgrade() -> None:
    # No downgrade needed - PostgreSQL doesn't support removing enum values easily
    pass

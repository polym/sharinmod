"""Add moonshot provider fix

Revision ID: 20260208_moonshot_fix
Revises: 20260208_add_minimax_provider
Create Date: 2026-02-08

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260208_moonshot_fix'
down_revision: Union[str, None] = '20260208_add_minimax_provider'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add MOONSHOT to the apikeyprovider enum
    # This fixes the missing MOONSHOT enum value that should have been added earlier
    op.execute("ALTER TYPE apikeyprovider ADD VALUE 'MOONSHOT'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    pass

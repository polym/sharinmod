"""add_litellm_key_to_unified_tokens

Revision ID: af16b3589f13
Revises: d2a3b850dd04
Create Date: 2026-01-30 15:53:33.569117

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'af16b3589f13'
down_revision: Union[str, None] = 'd2a3b850dd04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the litellm_key column to unified_tokens table
    op.add_column('unified_tokens', sa.Column('litellm_key', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove the litellm_key column from unified_tokens table
    op.drop_column('unified_tokens', 'litellm_key')

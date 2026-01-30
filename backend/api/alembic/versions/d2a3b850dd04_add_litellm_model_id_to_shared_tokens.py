"""Add litellm_model_id to shared_tokens

Revision ID: d2a3b850dd04
Revises: 9ea5b0492874
Create Date: 2026-01-30 06:01:38.046619

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'd2a3b850dd04'
down_revision: Union[str, None] = '9ea5b0492874'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the litellm_model_id column to shared_tokens table
    op.add_column('shared_tokens', sa.Column('litellm_model_id', sa.String(length=100), nullable=True))


def downgrade() -> None:
    # Remove the litellm_model_id column from shared_tokens table
    op.drop_column('shared_tokens', 'litellm_model_id')

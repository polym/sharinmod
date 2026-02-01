"""Add litellm_model_ids field to shared_api_keys

Revision ID: 20260201_add_model_ids
Revises: 20260131_add_desc
Create Date: 2026-02-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '20260201_add_model_ids'
down_revision: Union[str, None] = '20260131_add_desc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add litellm_model_ids column to shared_api_keys table
    op.add_column('shared_api_keys', sa.Column('litellm_model_ids', sa.String(length=1000), nullable=True))


def downgrade() -> None:
    # Remove litellm_model_ids column from shared_api_keys table
    op.drop_column('shared_api_keys', 'litellm_model_ids')

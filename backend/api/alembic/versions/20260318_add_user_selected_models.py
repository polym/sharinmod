"""Add user_selected_models to shared_api_keys

Revision ID: 20260318_add_user_selected_models
Revises: 20260316_add_is_auto_created
Create Date: 2026-03-18

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260318_add_user_selected_models'
down_revision: Union[str, None] = '20260316_add_is_auto_created'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'shared_api_keys',
        sa.Column('user_selected_models', sa.String(1000), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('shared_api_keys', 'user_selected_models')

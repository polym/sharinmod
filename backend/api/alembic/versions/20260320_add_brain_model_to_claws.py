"""Add brain_model to claws

Revision ID: 20260320_add_brain_model_to_claws
Revises: 20260319_add_validation_endpoint
Create Date: 2026-03-20

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260320_add_brain_model_to_claws'
down_revision: Union[str, None] = '20260319_add_validation_endpoint'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('claws', sa.Column('brain_model', sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column('claws', 'brain_model')

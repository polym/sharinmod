"""Add k8s_namespace to claws

Revision ID: 20260320_add_k8s_namespace_to_claws
Revises: 20260320_add_brain_model_to_claws
Create Date: 2026-03-20

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260320_add_k8s_namespace_to_claws'
down_revision: Union[str, None] = '20260320_add_brain_model_to_claws'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('claws', sa.Column('k8s_namespace', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('claws', 'k8s_namespace')

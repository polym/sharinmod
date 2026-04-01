"""Add chat_tool column to claws table

Revision ID: 20260323_add_chat_tool_to_claws
Revises: 20260320_add_k8s_namespace_to_claws
Create Date: 2026-03-23

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260323_add_chat_tool_to_claws'
down_revision: Union[str, None] = '20260320_add_k8s_namespace_to_claws'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'claws',
        sa.Column('chat_tool', sa.String(50), nullable=True, server_default='WEIXIN'),
    )


def downgrade() -> None:
    op.drop_column('claws', 'chat_tool')

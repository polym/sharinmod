"""Add password reset tokens table

Revision ID: 20260326_add_password_reset_tokens
Revises: 20260323_add_chat_tool_to_claws
Create Date: 2026-03-26

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260326_add_password_reset_tokens'
down_revision: Union[str, None] = '20260323_add_chat_tool_to_claws'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index(op.f('ix_password_reset_tokens_token'), 'password_reset_tokens', ['token'])


def downgrade() -> None:
    op.drop_index(op.f('ix_password_reset_tokens_token'), table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
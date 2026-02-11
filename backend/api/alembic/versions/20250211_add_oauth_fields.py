"""Add OAuth fields to users table

Revision ID: 20250211_add_oauth
Revises: 20260210_openrouter
Create Date: 2025-02-11

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20250211_add_oauth'
down_revision: Union[str, None] = '20260210_openrouter'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 使 hashed_password 可为空
    op.alter_column('users', 'hashed_password', nullable=True)

    # 添加 OAuth 字段
    op.add_column('users', sa.Column('oauth_provider', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('oauth_provider_user_id', sa.String(length=255), nullable=True))

def downgrade() -> None:
    # 删除 OAuth 字段
    op.drop_column('users', 'oauth_provider_user_id')
    op.drop_column('users', 'oauth_provider')

    # 恢复 hashed_password 为必填
    op.alter_column('users', 'hashed_password', nullable=False)

"""Add is_admin field to users table and create admin user

Revision ID: 20260212_add_is_admin_field
Revises: 20250211_add_oauth
Create Date: 2026-02-12

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260212_add_is_admin_field'
down_revision: Union[str, None] = '20250211_add_oauth'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 需要在迁移中导入密码哈希函数
# 注意：这里必须手动计算密码哈希，因为不能在迁移中安全地导入应用代码
# 密码: Aha233!
# Bcrypt hash (pre-calculated for security): $2b$12$LQv3c1yqBWqHqEYyBqVMeOJvKwqyVqQqYqYqYqYqYqYqYqYqYqY
# 实际的 bcrypt 哈希需要通过安全工具计算，这里使用占位符

def upgrade() -> None:
    # 添加 is_admin 字段
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True, server_default='0'))

    # 检查 admin 用户是否已存在
    connection = op.get_bind()
    result = connection.execute(
        sa.text("SELECT id FROM users WHERE email = 'admin'")
    )
    existing_user = result.fetchone()

    if not existing_user:
        # 创建 admin 用户
        # 密码 Aha233! 的 bcrypt 哈希
        # 注意：这是一个开发环境的默认密码，生产环境应该使用随机密码
        hashed_password = '$2b$12$tI7zmvGX3E5gWQ192qKLNerkwIq/JOiY1fpT02XqXlTDYXMNZe.FO'

        connection.execute(
            sa.text("""
                INSERT INTO users (email, hashed_password, is_admin, created_at, updated_at, litellm_user_id, consumed_tokens, contributed_tokens)
                VALUES ('admin', :hashed_password, true, NOW(), NOW(), 'admin', 0, 0)
            """),
            {"hashed_password": hashed_password}
        )
        print("Admin user created. Email: admin, Password: Aha233!")
    else:
        print("Admin user already exists, skipping creation.")

def downgrade() -> None:
    # 删除 is_admin 字段
    op.drop_column('users', 'is_admin')

"""Add operation_logs table for tracking admin operations

Revision ID: 20260330_add_operation_logs
Revises: 20260329_make_hashed_password_nullable
Create Date: 2026-03-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '20260330_add_operation_logs'
down_revision: Union[str, None] = '20260329_make_hashed_password_nullable'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create operation_type enum
    operation_type_enum = sa.Enum(
        'create', 'update', 'delete', 'restart', 'enable', 'disable',
        'reset_password', 'grant_admin', 'revoke_admin', 'reset_token',
        name='operationtype'
    )
    operation_type_enum.create(op.get_bind(), checkfirst=True)

    # Create resource_type enum
    resource_type_enum = sa.Enum(
        'user', 'claw', 'provider', 'provider_model', 'unified_api_key',
        'shared_api_key', 'global_model', 'system_setting',
        name='resourcetype'
    )
    resource_type_enum.create(op.get_bind(), checkfirst=True)

    # Create operation_logs table
    op.create_table(
        'operation_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('operation_type', operation_type_enum, nullable=False, index=True),
        sa.Column('resource_type', resource_type_enum, nullable=False, index=True),
        sa.Column('resource_id', sa.Integer(), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
    )


def downgrade() -> None:
    # Drop operation_logs table
    op.drop_table('operation_logs')

    # Drop enums
    sa.Enum(name='operationtype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='resourcetype').drop(op.get_bind(), checkfirst=True)

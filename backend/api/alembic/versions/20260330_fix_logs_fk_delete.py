"""Fix operation_logs foreign key delete behavior to SET NULL

Revision ID: 20260330_fix_logs_fk_delete
Revises: 20260330_add_operation_logs
Create Date: 2026-03-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '20260330_fix_logs_fk_delete'
down_revision: Union[str, None] = '20260330_add_operation_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing foreign key constraint
    op.drop_constraint(
        'operation_logs_user_id_fkey',
        'operation_logs',
        type_='foreignkey'
    )

    # Add new foreign key with ON DELETE SET NULL
    # This preserves audit logs when users are deleted
    op.create_foreign_key(
        'operation_logs_user_id_fkey',
        'operation_logs',
        'users',
        ['user_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Make user_id nullable to support SET NULL
    op.alter_column(
        'operation_logs',
        'user_id',
        existing_type=sa.Integer(),
        nullable=True
    )


def downgrade() -> None:
    # Revert to NOT NULL
    op.alter_column(
        'operation_logs',
        'user_id',
        existing_type=sa.Integer(),
        nullable=False
    )

    # Drop foreign key with ON DELETE SET NULL
    op.drop_constraint(
        'operation_logs_user_id_fkey',
        'operation_logs',
        type_='foreignkey'
    )

    # Re-add original foreign key (default behavior: RESTRICT)
    op.create_foreign_key(
        'operation_logs_user_id_fkey',
        'operation_logs',
        'users',
        ['user_id'],
        ['id']
    )
"""Add resource_name column to operation_logs table

Revision ID: 20260330_add_resource_name
Revises: 20260330_add_operation_logs
Create Date: 2026-03-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '20260330_add_resource_name'
down_revision: Union[str, None] = '20260330_add_operation_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add resource_name column to operation_logs table
    op.add_column(
        'operation_logs',
        sa.Column('resource_name', sa.String(), nullable=True)
    )


def downgrade() -> None:
    # Drop resource_name column
    op.drop_column('operation_logs', 'resource_name')
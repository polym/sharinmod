"""Add kind column to usage_logs table

Revision ID: 20260205_add_kind_to_usage_logs
Revises: 20260204_remove_subscription_id_usage_logs
Create Date: 2026-02-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '20260205_add_kind_to_usage_logs'
down_revision: Union[str, None] = '20260204_remove_subscription_id_usage_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add kind column with default value 'direct'
    op.add_column('usage_logs', sa.Column('kind', sa.String(length=20), nullable=False, server_default='direct'))

    # Create index on kind column
    op.create_index(op.f('ix_usage_logs_kind'), 'usage_logs', ['kind'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index(op.f('ix_usage_logs_kind'), table_name='usage_logs')

    # Drop column
    op.drop_column('usage_logs', 'kind')

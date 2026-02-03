"""Remove subscription_id from usage_logs table

Revision ID: 20260204_remove_subscription_id_usage_logs
Revises: 20260203_add_cascade_delete_subscriptions
Create Date: 2026-02-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '20260204_remove_subscription_id_usage_logs'
down_revision: Union[str, None] = '20260203_add_cascade_delete_subscriptions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the foreign key constraint first
    op.drop_constraint(
        'usage_logs_subscription_id_fkey',
        'usage_logs',
        type_='foreignkey'
    )

    # Drop the subscription_id column
    op.drop_column('usage_logs', 'subscription_id')


def downgrade() -> None:
    # Add back the subscription_id column
    op.add_column('usage_logs', sa.Column('subscription_id', sa.Integer(), nullable=True))

    # Recreate the foreign key constraint
    op.create_foreign_key(
        'usage_logs_subscription_id_fkey',
        'usage_logs',
        'subscriptions',
        ['subscription_id'],
        ['id']
    )

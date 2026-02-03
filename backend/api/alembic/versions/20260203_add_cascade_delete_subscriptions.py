"""Add ON DELETE CASCADE to subscriptions shared_api_key_id foreign key

Revision ID: 20260203_add_cascade_delete_subscriptions
Revises: 20260202_add_usage_logs
Create Date: 2026-02-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '20260203_add_cascade_delete_subscriptions'
down_revision: Union[str, None] = '20260202_add_usage_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing foreign key constraint
    op.drop_constraint(
        'subscriptions_shared_api_key_id_fkey',
        'subscriptions',
        type_='foreignkey'
    )

    # Recreate the foreign key constraint with ON DELETE CASCADE
    op.create_foreign_key(
        'subscriptions_shared_api_key_id_fkey',
        'subscriptions',
        'shared_api_keys',
        ['shared_api_key_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Revert back to the original constraint without CASCADE
    op.drop_constraint(
        'subscriptions_shared_api_key_id_fkey',
        'subscriptions',
        type_='foreignkey'
    )

    op.create_foreign_key(
        'subscriptions_shared_api_key_id_fkey',
        'subscriptions',
        'shared_api_keys',
        ['shared_api_key_id'],
        ['id']
    )

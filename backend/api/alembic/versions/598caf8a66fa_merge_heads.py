"""merge heads

Revision ID: 598caf8a66fa
Revises: 20260326_add_user_status_fields, 20260326_create_api_key_limit_history
Create Date: 2026-03-26 08:58:04.111193

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '598caf8a66fa'
down_revision: Union[str, None] = ('20260326_add_user_status_fields', '20260326_create_api_key_limit_history')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

"""Change daily_token_limit and daily_tokens_used to BIGINT

Revision ID: 20260413_bigint_daily_token_fields
Revises: 20260408_add_org_invite_and_member_disable
Create Date: 2026-04-13

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260413_bigint_daily_token_fields'
down_revision: Union[str, None] = '20260408_add_org_invite_and_member_disable'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('unified_api_keys', 'daily_token_limit',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=True)
    op.alter_column('unified_api_keys', 'daily_tokens_used',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)


def downgrade() -> None:
    op.alter_column('unified_api_keys', 'daily_tokens_used',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=False)
    op.alter_column('unified_api_keys', 'daily_token_limit',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=True)

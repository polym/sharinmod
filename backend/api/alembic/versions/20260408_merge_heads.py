"""Merge all heads into single head

Revision ID: 20260408_merge_heads
Revises: 20260330_add_resource_name, 20260330_fix_is_admin_nullable,
         20260330_fix_logs_fk_delete, 20260407_add_org_to_usage_logs
Create Date: 2026-04-08

"""
from typing import Sequence, Union

revision: str = '20260408_merge_heads'
down_revision: Union[str, Sequence[str], None] = (
    '20260330_add_resource_name',
    '20260330_fix_is_admin_nullable',
    '20260330_fix_logs_fk_delete',
    '20260407_add_org_to_usage_logs',
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

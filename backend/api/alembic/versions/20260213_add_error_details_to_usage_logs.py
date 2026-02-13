"""Add error_details column to usage_logs table

Revision ID: 20260213_add_error_details
Revises: 20260212_add_is_admin
Create Date: 2026-02-13

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260213_add_error_details'
down_revision: Union[str, None] = '20260213_add_provider_configs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add error_details column to store failure error information as JSON array
    # Format: [{"start_time": 1739337600.0, "error_code": "500", "error_str": "...", "provider": "bigmodel", "subscription_id": 123}]
    op.add_column('usage_logs', sa.Column('error_details', sa.String(length=20000), nullable=True))

def downgrade() -> None:
    op.drop_column('usage_logs', 'error_details')

"""Convert all timestamp columns to timestamptz

Revision ID: 20260415_convert_timestamp_to_timestamptz
Revises: 20260413_bigint_daily_token_fields
Create Date: 2026-04-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260415_convert_timestamp_to_timestamptz'
down_revision: Union[str, None] = '20260413_bigint_daily_token_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert users table
    op.execute("ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE users ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE users ALTER COLUMN deleted_at TYPE TIMESTAMPTZ USING deleted_at AT TIME ZONE 'UTC'")

    # Convert unified_api_keys table
    op.execute("ALTER TABLE unified_api_keys ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE unified_api_keys ALTER COLUMN revoked_at TYPE TIMESTAMPTZ USING revoked_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE unified_api_keys ALTER COLUMN last_used_at TYPE TIMESTAMPTZ USING last_used_at AT TIME ZONE 'UTC'")

    # Convert usage_logs table
    op.execute("ALTER TABLE usage_logs ALTER COLUMN request_time TYPE TIMESTAMPTZ USING request_time AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE usage_logs ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")

    # Convert organizations table
    op.execute("ALTER TABLE organizations ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE organizations ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'")

    # Convert claws table
    op.execute("ALTER TABLE claws ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE claws ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'")

    # Convert password_reset_tokens table
    op.execute("ALTER TABLE password_reset_tokens ALTER COLUMN expires_at TYPE TIMESTAMPTZ USING expires_at AT TIME ZONE 'UTC'")

    # Convert api_key_limit_history table
    op.execute("ALTER TABLE api_key_limit_history ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")

    # Convert api_key_usage_history table
    op.execute("ALTER TABLE api_key_usage_history ALTER COLUMN timestamp TYPE TIMESTAMPTZ USING timestamp AT TIME ZONE 'UTC'")

    # Convert subscriptions table
    op.execute("ALTER TABLE subscriptions ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")

    # Convert organization_invites table
    op.execute("ALTER TABLE organization_invites ALTER COLUMN expires_at TYPE TIMESTAMPTZ USING expires_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE organization_invites ALTER COLUMN used_at TYPE TIMESTAMPTZ USING used_at AT TIME ZONE 'UTC'")

    # Convert organization_members table
    op.execute("ALTER TABLE organization_members ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")

    # Convert provider_configs table
    op.execute("ALTER TABLE provider_configs ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE provider_configs ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'")

    # Convert provider_models table
    op.execute("ALTER TABLE provider_models ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE provider_models ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'")

    # Convert global_models table
    op.execute("ALTER TABLE global_models ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE global_models ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'")

    # Convert system_settings table
    op.execute("ALTER TABLE system_settings ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE system_settings ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'")

    # Convert shared_api_keys table
    op.execute("ALTER TABLE shared_api_keys ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE shared_api_keys ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE shared_api_keys ALTER COLUMN last_used_at TYPE TIMESTAMPTZ USING last_used_at AT TIME ZONE 'UTC'")


def downgrade() -> None:
    # Revert users table
    op.execute("ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE users ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE users ALTER COLUMN deleted_at TYPE TIMESTAMP WITHOUT TIME ZONE")

    # Revert unified_api_keys table
    op.execute("ALTER TABLE unified_api_keys ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE unified_api_keys ALTER COLUMN revoked_at TYPE TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE unified_api_keys ALTER COLUMN last_used_at TYPE TIMESTAMP WITHOUT TIME ZONE")

    # Revert usage_logs table
    op.execute("ALTER TABLE usage_logs ALTER COLUMN request_time TYPE TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE usage_logs ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE")

    # Revert organizations table
    op.execute("ALTER TABLE organizations ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE organizations ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE")

    # Revert claws table
    op.execute("ALTER TABLE claws ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE claws ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE")

    # Revert password_reset_tokens table
    op.execute("ALTER TABLE password_reset_tokens ALTER COLUMN expires_at TYPE TIMESTAMP WITHOUT TIME ZONE")

    # Revert api_key_limit_history table
    op.execute("ALTER TABLE api_key_limit_history ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE")

    # Revert api_key_usage_history table
    op.execute("ALTER TABLE api_key_usage_history ALTER COLUMN timestamp TYPE TIMESTAMP WITHOUT TIME ZONE")

    # Revert subscriptions table
    op.execute("ALTER TABLE subscriptions ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE")

    # Revert organization_invites table
    op.execute("ALTER TABLE organization_invites ALTER COLUMN expires_at TYPE TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE organization_invites ALTER COLUMN used_at TYPE TIMESTAMP WITHOUT TIME ZONE")

    # Revert organization_members table
    op.execute("ALTER TABLE organization_members ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE")

    # Revert provider_configs table
    op.execute("ALTER TABLE provider_configs ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE provider_configs ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE")

    # Revert provider_models table
    op.execute("ALTER TABLE provider_models ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE provider_models ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE")

    # Revert global_models table
    op.execute("ALTER TABLE global_models ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE global_models ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE")

    # Revert system_settings table
    op.execute("ALTER TABLE system_settings ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE system_settings ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE")

    # Revert shared_api_keys table
    op.execute("ALTER TABLE shared_api_keys ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE shared_api_keys ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE")
    op.execute("ALTER TABLE shared_api_keys ALTER COLUMN last_used_at TYPE TIMESTAMP WITHOUT TIME ZONE")

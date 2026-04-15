"""Add email registration: invitation_codes, email_verification_tokens, users.email_verified

Revision ID: 20260415_add_email_registration
Revises: 20260415_convert_timestamp_to_timestamptz
Create Date: 2026-04-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260415_add_email_registration'
down_revision: Union[str, None] = '20260415_convert_timestamp_to_timestamptz'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create invitation_codes table
    op.create_table(
        'invitation_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=16), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('used_by_user_id', sa.Integer(), nullable=True),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_invitation_codes_code', 'invitation_codes', ['code'], unique=True)

    # Create email_verification_tokens table
    op.create_table(
        'email_verification_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_email_verification_tokens_token', 'email_verification_tokens', ['token'], unique=True)

    # Add email_verified column to users (False by default)
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))

    # Mark existing users (OAuth or password-based) as already verified — they didn't go through the new flow
    op.execute("UPDATE users SET email_verified = true WHERE hashed_password IS NOT NULL OR oauth_provider IS NOT NULL")


def downgrade() -> None:
    op.drop_column('users', 'email_verified')
    op.drop_index('ix_email_verification_tokens_token', table_name='email_verification_tokens')
    op.drop_table('email_verification_tokens')
    op.drop_index('ix_invitation_codes_code', table_name='invitation_codes')
    op.drop_table('invitation_codes')

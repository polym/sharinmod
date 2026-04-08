"""Add organization_invites table and is_disabled to organization_members

Revision ID: 20260408_add_org_invite_and_member_disable
Revises: 20260408_merge_heads
Create Date: 2026-04-08

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260408_add_org_invite_and_member_disable'
down_revision: Union[str, None] = '20260408_merge_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add is_disabled column to organization_members
    op.add_column(
        'organization_members',
        sa.Column('is_disabled', sa.Boolean(), nullable=False, server_default='false')
    )

    # 2. Create organization_invites table
    op.create_table(
        'organization_invites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('used_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['organization_id'], ['organizations.id'],
            name='fk_org_invites_organization_id',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['created_by_user_id'], ['users.id'],
            name='fk_org_invites_created_by_user_id'
        ),
        sa.ForeignKeyConstraint(
            ['used_by_user_id'], ['users.id'],
            name='fk_org_invites_used_by_user_id'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token', name='uq_org_invites_token'),
    )
    op.create_index('ix_organization_invites_token', 'organization_invites', ['token'])


def downgrade() -> None:
    op.drop_index('ix_organization_invites_token', table_name='organization_invites')
    op.drop_table('organization_invites')
    op.drop_column('organization_members', 'is_disabled')

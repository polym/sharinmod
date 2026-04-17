"""Add is_personal to organizations and create personal orgs for existing users

Revision ID: 20260417_add_personal_org
Revises: 20260416_merge_heads
Create Date: 2026-04-17

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260417_add_personal_org'
down_revision: Union[str, None] = '20260416_merge_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_personal column with default False (existing orgs are not personal)
    op.add_column('organizations', sa.Column('is_personal', sa.Boolean(), nullable=False, server_default='false'))

    # Step A: For users who already own an org, mark that org as their personal org.
    # (Each user can own at most one org due to the unique constraint on (user_id, role).)
    op.execute("""
        UPDATE organizations o
        SET is_personal = true
        FROM organization_members m
        WHERE m.organization_id = o.id
          AND m.role = 'owner'
    """)

    # Step B: Create personal orgs for users who have NO owner membership at all.
    op.execute("""
        INSERT INTO organizations (name, slug, is_personal, created_at, updated_at, default_daily_token_limit)
        SELECT
            COALESCE(NULLIF(u.name, ''), split_part(u.email, '@', 1)) || '的个人工作区',
            COALESCE(
                NULLIF(regexp_replace(lower(COALESCE(NULLIF(u.name, ''), split_part(u.email, '@', 1))), '[^a-z0-9]+', '-', 'g'), ''),
                'user'
            ) || '-personal-' || u.id::text,
            true,
            NOW(),
            NOW(),
            NULL
        FROM users u
        WHERE u.id NOT IN (
            SELECT user_id FROM organization_members WHERE role = 'owner'
        )
    """)

    # Step C: Create owner memberships for the newly created personal orgs (Step B users only).
    op.execute("""
        INSERT INTO organization_members (organization_id, user_id, role, is_disabled, created_at)
        SELECT
            o.id,
            u.id,
            'owner',
            false,
            NOW()
        FROM users u
        JOIN organizations o ON o.slug = COALESCE(
                NULLIF(regexp_replace(lower(COALESCE(NULLIF(u.name, ''), split_part(u.email, '@', 1))), '[^a-z0-9]+', '-', 'g'), ''),
                'user'
            ) || '-personal-' || u.id::text
        WHERE o.is_personal = true
        AND NOT EXISTS (
            SELECT 1 FROM organization_members m
            WHERE m.organization_id = o.id AND m.role = 'owner'
        )
    """)


def downgrade() -> None:
    # Revert Step C: delete memberships for orgs that were newly created (slug contains '-personal-')
    op.execute("DELETE FROM organization_members WHERE organization_id IN (SELECT id FROM organizations WHERE is_personal = true AND slug LIKE '%-personal-%')")
    # Revert Step B: delete newly created personal orgs
    op.execute("DELETE FROM organizations WHERE is_personal = true AND slug LIKE '%-personal-%'")
    # Revert Step A: un-mark orgs that were already owned (they existed before migration)
    op.execute("UPDATE organizations SET is_personal = false WHERE is_personal = true")
    op.drop_column('organizations', 'is_personal')

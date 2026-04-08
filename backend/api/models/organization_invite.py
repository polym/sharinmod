"""
OrganizationInvite model for managing organization invite links
"""
from sqlmodel import SQLModel, Field
from datetime import datetime, timedelta, timezone
from typing import Optional
import sqlalchemy as sa


def _default_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=7)


class OrganizationInvite(SQLModel, table=True):
    """
    OrganizationInvite model for tracking invite links to organizations

    Attributes:
        id: Primary key, auto-incremented
        organization_id: Foreign key to organizations.id (CASCADE DELETE)
        token: UUID4 string token, unique
        created_by_user_id: Foreign key to users.id
        expires_at: Expiry datetime (default: now + 7 days)
        used_at: When the invite was used (None = unused)
        used_by_user_id: User who accepted the invite (nullable)
    """
    __tablename__ = "organization_invites"

    id: Optional[int] = Field(default=None, primary_key=True)
    organization_id: int = Field(index=True)
    token: str = Field(max_length=64, index=True)
    created_by_user_id: int
    expires_at: datetime = Field(default_factory=_default_expires_at)
    used_at: Optional[datetime] = Field(default=None)
    used_by_user_id: Optional[int] = Field(default=None)

    __table_args__ = (
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
        sa.UniqueConstraint('token', name='uq_org_invites_token'),
    )

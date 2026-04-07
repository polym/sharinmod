"""
OrganizationMember model for managing user-organization relationships
"""
from sqlmodel import SQLModel, Field, Index
from datetime import datetime
from typing import Optional
import sqlalchemy as sa


class OrganizationMember(SQLModel, table=True):
    """
    OrganizationMember model mapping users to organizations

    Attributes:
        id: Primary key, auto-incremented
        organization_id: Foreign key to organizations.id
        user_id: Foreign key to users.id
        role: User role in the organization ('owner' or 'member')
        created_at: Timestamp when the relationship was created
    """
    __tablename__ = "organization_members"

    id: Optional[int] = Field(default=None, primary_key=True)
    organization_id: int = Field(index=True)
    user_id: int = Field(index=True)
    role: str = Field(max_length=20)  # 'owner' or 'member'
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Foreign keys with CASCADE delete and unique constraint
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ['organization_id'], ['organizations.id'],
            name='fk_organization_members_organization_id_organizations',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name='fk_organization_members_user_id_users',
            ondelete='CASCADE'
        ),
        # Unique constraint: user can only have one role per type
        Index("idx_user_role_unique", "user_id", "role", unique=True),
    )
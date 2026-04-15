"""
Invitation code model for controlled user registration
"""
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, DateTime, ForeignKey


class InvitationCode(SQLModel, table=True):
    """
    Invitation code for gating self-registration.

    Attributes:
        id: Primary key
        code: Unique 8-char uppercase hex code
        created_by_user_id: Admin who created this code (nullable for system-generated)
        used_by_user_id: User who redeemed this code
        used_at: Timestamp when code was redeemed
        created_at: Creation timestamp
    """
    __tablename__ = "invitation_codes"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=16)
    created_by_user_id: Optional[int] = Field(default=None)
    used_by_user_id: Optional[int] = Field(default=None)
    used_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True),
        default=None
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

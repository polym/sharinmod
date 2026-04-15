"""
System Setting model for platform-wide configuration
"""
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, DateTime


class SystemSetting(SQLModel, table=True):
    """
    System-wide configuration settings stored as key-value pairs

    Business Rules:
    - Settings are cached in memory for performance
    - Changes to settings take effect immediately
    """
    __tablename__ = "system_settings"

    key: str = Field(primary_key=True, max_length=100)
    value: str = Field(max_length=1000)
    description: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        default_factory=lambda: datetime.now(timezone.utc)
    )

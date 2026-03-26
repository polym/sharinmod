"""
System Setting model for platform-wide configuration
"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

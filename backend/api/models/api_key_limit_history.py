"""
API Key Limit History model for tracking limit-related actions
"""
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional


class APIKeyLimitHistory(SQLModel, table=True):
    """
    History of API key limit-related actions (disable/enable due to limits)

    Business Rules:
    - Records are created automatically when keys hit daily limits
    - Records are created when keys are reset daily
    - Cascades delete when the associated API key is deleted
    """
    __tablename__ = "api_key_limit_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    unified_api_key_id: int = Field(foreign_key="unified_api_keys.id")
    action: str = Field(max_length=50, description="Action type: 'disable' or 'enable'")
    reason: Optional[str] = Field(default=None, max_length=500, description="Reason for the action")
    tokens_used: int = Field(default=0, description="Tokens used at the time of action")
    token_limit: int = Field(default=0, description="Token limit at the time of action")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    unified_api_key: Optional["UnifiedAPIKey"] = Relationship(back_populates="limit_history")

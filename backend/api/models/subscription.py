"""
Subscription model for mapping model_id to SharedAPIKey and User
"""
from sqlmodel import SQLModel, Field, Index
from datetime import datetime
from typing import Optional


class Subscription(SQLModel, table=True):
    """
    Subscription model mapping LiteLLM model_id to SharedAPIKey and User

    This table maintains the relationship between:
    - model_id: LiteLLM model identifier
    - shared_api_key_id: The SharedAPIKey that provides this model
    - user_id: The user who owns the SharedAPIKey (contributor)

    When a callback is received:
    - user_api_key_hash -> identifies the consuming UserA
    - model_id -> identifies Subscription -> SharedAPIKey -> UserB (contributor)
    """
    __tablename__ = "subscriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    model_id: str = Field(unique=True, max_length=100, index=True)
    shared_api_key_id: int = Field(foreign_key="shared_api_keys.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Unique constraint on model_id
    __table_args__ = (
        Index("idx_model_id_unique", "model_id", unique=True),
    )

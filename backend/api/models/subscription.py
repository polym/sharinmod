"""
Subscription model for mapping model_id to SharedAPIKey and User
"""
from sqlmodel import SQLModel, Field, Index
from datetime import datetime
from typing import Optional
import sqlalchemy as sa


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
    shared_api_key_id: int = Field(index=True)
    user_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Unique constraint on model_id and foreign keys with CASCADE delete
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ['shared_api_key_id'], ['shared_api_keys.id'],
            name='fk_subscriptions_shared_api_key_id_shared_api_keys',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name='fk_subscriptions_user_id_users'
        ),
        Index("idx_model_id_unique", "model_id", unique=True),
    )

"""
Claw model - QQ bot instances deployed on Kubernetes
"""
from sqlmodel import SQLModel, Field, Index
from datetime import datetime
from typing import Optional
from enum import Enum


class ClawType(str, Enum):
    """Type of QQ bot"""
    NANOBOT = "NANOBOT"
    OPENCLAW = "OPENCLAW"
    ZEROBOT = "ZEROBOT"


class ClawStatus(str, Enum):
    """Claw deployment status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class Claw(SQLModel, table=True):
    """
    Claw - a QQ bot instance deployed as a K8s Deployment

    Business Rules:
    - Maximum 10 claws per user
    - K8s Deployment name: claw-{id}
    - Resource limits: CPU 2, Memory 8Gi; requests: CPU 0.2, Memory 800Mi
    """
    __tablename__ = "claws"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=100)
    type: ClawType = Field(default=ClawType.NANOBOT)
    qq_bot_id: str = Field(max_length=255)
    qq_bot_secret: str = Field(max_length=255)
    unified_api_key_id: Optional[int] = Field(default=None, foreign_key="unified_api_keys.id")
    brain_model: Optional[str] = Field(default=None, max_length=100)
    k8s_deployment_name: Optional[str] = Field(default=None, max_length=255)
    k8s_namespace: Optional[str] = Field(default=None, max_length=255)
    status: ClawStatus = Field(default=ClawStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        Index("idx_claw_user_status", "user_id", "status"),
    )

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Optional
from api.database import get_db
from api.dependencies.auth import get_current_user
from api.models.user import User
from api.schemas.models import ModelDiscoveryList
from api.services.models_service import get_available_models

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=ModelDiscoveryList)
def discover_models(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    org_id: Optional[int] = Query(None, description="组织 ID，私服场景下传入"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取可用的模型列表（按组织隔离）

    返回通过 Subscription 共享的模型，包括：
    - 模型显示名称和原始模型名称（模型 ID）
    - 模型描述、输入/输出类型、上下文长度等元数据
    - 可用订阅数量
    - 共享者信息列表

    需要 JWT 认证

    ?org_id=N: 私服场景，返回该组织内订阅的模型
    不传 org_id: 公区场景，返回 organization_id IS NULL 的订阅模型
    """
    items = get_available_models(db, organization_id=org_id)
    return ModelDiscoveryList(
        page=page,
        page_size=page_size,
        total=len(items),
        items=items
    )

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取所有可用的模型列表

    返回通过 Subscription 共享的所有模型，包括：
    - 模型显示名称和原始模型名称（模型 ID）
    - 模型描述、输入/输出类型、上下文长度等元数据
    - 可用订阅数量
    - 共享者信息列表

    需要 JWT 认证

    Response includes:
    - display_name: 显示名称（如 "BigModel: GLM-4.7"）
    - model_name: 原始模型名称/模型 ID（如 "glm-4.7"）
    - provider: API 提供商（如 "bigmodel"）
    - description: 模型描述
    - input_type / output_type: 输入/输出类型
    - context_length / max_output_length: 上下文和输出长度限制
    - available_subscriptions: 可用订阅数量
    - shared_by: 共享者列表（包含用户名和头像）
    """
    items = get_available_models(db)
    return ModelDiscoveryList(
        page=page,
        page_size=page_size,
        total=len(items),
        items=items
    )

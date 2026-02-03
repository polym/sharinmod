from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError
from api.models.subscription import Subscription
from api.models.shared_api_key import SharedAPIKey, APIKeyStatus
from api.services.shared_api_key_service import PROVIDER_INFO
from api.models.user import User
from api.schemas.models import ModelInfo, SharedBy
from typing import List, Dict
from collections import defaultdict
import json
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def _find_model_name_by_litellm_id(litellm_model_ids_json: str, target_model_id: str) -> str:
    """
    从 litellm_model_ids JSON 中通过 litellm_model_id 反向查找原始 model_name

    Args:
        litellm_model_ids_json: JSON 字符串，格式为 {"glm-4.7": "uuid-...", ...}
        target_model_id: 要查找的 LiteLLM model_id (UUID)

    Returns:
        原始 model_name (如 "glm-4.7")，如果未找到返回 target_model_id
    """
    try:
        litellm_model_ids = json.loads(litellm_model_ids_json)
        for model_name, model_id in litellm_model_ids.items():
            if model_id == target_model_id:
                return model_name
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse litellm_model_ids: {e}")
    return target_model_id


def get_available_models(db: Session) -> List[ModelInfo]:
    """
    获取所有可用的模型信息

    查询逻辑：
    1. 从 Subscription 表获取所有记录
    2. JOIN SharedAPIKey 获取 provider 信息（只包含 ACTIVE 状态）
    3. JOIN User 获取共享者信息
    4. 按 model_id 分组，收集共享者列表
    5. 从 PROVIDER_INFO 获取模型元数据
    6. 通过 Subscription.model_id（UUID）反向查找原始 model_name

    Args:
        db: Database session

    Returns:
        List[ModelInfo]: 模型信息列表

    Raises:
        HTTPException: 数据库查询失败时返回 500 错误
    """
    try:
        # 构建 JOIN 查询：Subscription -> SharedAPIKey -> User
        statement = (
            select(Subscription, SharedAPIKey, User)
            .join(SharedAPIKey, Subscription.shared_api_key_id == SharedAPIKey.id)
            .join(User, Subscription.user_id == User.id)
            .where(SharedAPIKey.status == APIKeyStatus.ACTIVE)
        )

        results = db.exec(statement).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_available_models: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve models. Please try again later."
        )

    # 按 model_name 分组，收集共享者列表
    # key: (provider, model_name), value: {"shared_by": [...], "model_id": ...}
    models_dict: Dict[tuple, Dict] = {}

    for subscription, shared_api_key, user in results:
        # 从 litellm_model_ids JSON 中反向查找原始 model_name
        model_name = _find_model_name_by_litellm_id(
            shared_api_key.litellm_model_ids or "{}",
            subscription.model_id
        )

        # 构建分组键
        key = (shared_api_key.provider, model_name)

        if key not in models_dict:
            models_dict[key] = {
                "shared_by": [],
                "litellm_model_ids": shared_api_key.litellm_model_ids or "{}"
            }

        # 添加共享者信息（去重）
        # 只暴露邮箱前缀以保护用户隐私
        username = user.email.split('@')[0] if user.email else f"user_{user.id}"
        shared_by_entry = SharedBy(
            user_id=user.id,
            name=username,
            avatar_url=user.avatar_url
        )
        # 检查是否已存在（同一用户可能共享了相同的模型）
        if not any(sb.user_id == user.id for sb in models_dict[key]["shared_by"]):
            models_dict[key]["shared_by"].append(shared_by_entry)

    # 构建返回的 ModelInfo 列表
    model_info_list = []

    for (provider, model_name), data in models_dict.items():
        # 从 PROVIDER_INFO 获取模型元数据
        provider_config = PROVIDER_INFO.get(provider)
        models_config = provider_config.get("models", {}) if provider_config else {}
        model_config = models_config.get(model_name, {})

        # 构建 display_name: provider 首字母大写 + ": " + 模型名大写
        display_name = f"{provider.value.title()}: {model_name.upper()}"

        # 如果 provider 不在配置中，记录警告并使用默认值
        if not provider_config:
            logger.warning(f"No provider config found for {provider}, using defaults for model {model_name}")

        model_info = ModelInfo(
            display_name=display_name,
            model_name=model_name,  # 原始模型名称，如 "glm-4.7"（显示为「模型 ID」）
            provider=provider.value,
            description=model_config.get("description", "暂无描述"),
            input_type=model_config.get("input_type", "Text"),
            output_type=model_config.get("output_type", "Text"),
            context_length=model_config.get("context_length", "N/A"),
            max_output_length=model_config.get("max_output_length", "N/A"),
            available_subscriptions=len(data["shared_by"]),
            shared_by=data["shared_by"]
        )
        model_info_list.append(model_info)

    # 按 provider 和 model_name 排序
    model_info_list.sort(key=lambda m: (m.provider, m.model_name))

    return model_info_list

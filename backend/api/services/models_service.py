from sqlmodel import Session, select, func
from sqlalchemy.exc import SQLAlchemyError
from api.models.subscription import Subscription
from api.models.shared_api_key import SharedAPIKey, APIKeyStatus
from api.services.shared_api_key_service import PROVIDER_INFO
from api.services.provider_config_service import get_unified_model_catalog
from api.models.user import User
from api.models.usage_log import UsageLog
from api.schemas.models import ModelInfo, SharedBy, ProviderInfo
from typing import List, Dict, Optional
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
    4. 按 model_name 分组（不按 provider），收集所有提供商和共享者列表
    5. 从 PROVIDER_INFO 获取模型元数据
    6. 从 usage_logs 表统计已使用 Token 总量

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

    # 查询每个模型的总 Token 使用量
    try:
        token_stats = (
            db.exec(
                select(UsageLog.model_name, func.sum(UsageLog.total_tokens).label("total_tokens"))
                .group_by(UsageLog.model_name)
            )
            .all()
        )
        # 转换为字典: {model_name: total_tokens}
        tokens_dict = {row.model_name: int(row.total_tokens) for row in token_stats}
    except SQLAlchemyError as e:
        logger.warning(f"Failed to fetch token statistics: {e}")
        tokens_dict = {}

    # 按 model_name 分组，收集提供商和共享者列表
    # key: model_name, value: {"providers": set(), "shared_by": [], "subscription_count": int}
    models_dict: Dict[str, Dict] = defaultdict(lambda: {"providers": set(), "shared_by": [], "subscription_count": 0})

    for subscription, shared_api_key, user in results:
        # 从 litellm_model_ids JSON 中反向查找原始 model_name
        model_name = _find_model_name_by_litellm_id(
            shared_api_key.litellm_model_ids or "{}",
            subscription.model_id
        )

        # 收集提供商
        models_dict[model_name]["providers"].add(shared_api_key.provider)

        # 添加共享者信息（不去重，保留所有订阅记录）
        # 只暴露邮箱前缀以保护用户隐私
        username = user.email.split('@')[0] if user.email else f"user_{user.id}"
        shared_by_entry = SharedBy(
            user_id=user.id,
            name=username,
            avatar_url=user.avatar_url
        )
        models_dict[model_name]["shared_by"].append(shared_by_entry)
        models_dict[model_name]["subscription_count"] += 1

    # 构建返回的 ModelInfo 列表
    model_info_list = []

    # 过滤：只保留模型配置中已启用的模型
    enabled_catalog = get_unified_model_catalog(db, enabled_only=True)
    enabled_model_keys = {item["model_key"] for item in enabled_catalog}

    # 批量查询 GlobalModel 获取所有元数据
    from api.models.provider_config import GlobalModel
    global_models = db.exec(select(GlobalModel)).all()
    global_model_map = {gm.model_key: gm for gm in global_models}

    for model_name, data in models_dict.items():
        # 跳过模型配置中已禁用的模型
        if model_name not in enabled_model_keys:
            continue

        # 优先从 GlobalModel 获取元数据
        global_model = global_model_map.get(model_name)

        # 获取该模型的第一个提供商（用于获取模型配置）
        # 优先使用 bigmodel，否则使用第一个提供商
        providers_list = list(data["providers"])
        first_provider = next((p for p in providers_list if p == "bigmodel"), providers_list[0])

        # 从 PROVIDER_INFO 获取模型元数据（provider 现在是 str 类型）
        # 需要尝试转换为 APIKeyProvider 枚举
        from api.models.shared_api_key import APIKeyProvider
        try:
            provider_enum = APIKeyProvider(first_provider)
            provider_config = PROVIDER_INFO.get(provider_enum)
        except ValueError:
            # 动态供应商，不在 PROVIDER_INFO 中
            provider_config = None

        models_config = provider_config.get("models", {}) if provider_config else {}
        model_config = models_config.get(model_name, {})

        # 构建 display_name: 优先级 GlobalModel > PROVIDER_INFO > model_name.upper()
        if global_model and global_model.display_name:
            display_name = global_model.display_name
        else:
            display_name = model_config.get("display_name", model_name.upper())

        # 构建提供商列表
        provider_infos = []
        for provider in providers_list:
            try:
                provider_enum = APIKeyProvider(provider)
                p_config = PROVIDER_INFO.get(provider_enum)
                if p_config:
                    provider_infos.append(ProviderInfo(
                        code=provider,
                        name=p_config.get("name", provider),
                        logo_path=p_config.get("logo_path", "")
                    ))
            except ValueError:
                # 动态供应商，尝试从数据库获取配置
                from api.services.provider_config_service import get_provider_by_key
                db_provider = get_provider_by_key(db, provider)
                if db_provider:
                    provider_infos.append(ProviderInfo(
                        code=provider,
                        name=db_provider.name or provider,
                        logo_path=db_provider.logo_path or ""
                    ))

        # 获取元数据：优先 GlobalModel，其次 PROVIDER_INFO，最后默认值
        if global_model:
            description = global_model.description or model_config.get("description", "暂无描述")
            context_length = global_model.context_length or model_config.get("context_length", "N/A")
            max_output_length = global_model.max_output_length or model_config.get("max_output_length", "N/A")
            input_types = global_model.input_types or model_config.get("input_types", ["Text"])
            output_types = global_model.output_types or model_config.get("output_types", ["Text"])
            coding_score = global_model.coding_score if global_model.coding_score is not None else model_config.get("coding_score")
            model_logo_url = global_model.logo_url
        else:
            description = model_config.get("description", "暂无描述")
            context_length = model_config.get("context_length", "N/A")
            max_output_length = model_config.get("max_output_length", "N/A")
            input_types = model_config.get("input_types", ["Text"])
            output_types = model_config.get("output_types", ["Text"])
            coding_score = model_config.get("coding_score")
            model_logo_url = None

        # 如果 provider 不在配置中，记录警告
        if not provider_config and not global_model:
            logger.warning(f"No config found for {first_provider}, using defaults for model {model_name}")

        model_info = ModelInfo(
            display_name=display_name,
            model_name=model_name,  # 原始模型名称，如 "glm-4.7"（显示为「模型 ID」）
            provider=first_provider,  # 使用第一个提供商作为主提供商（现在是 str 类型）
            description=description,
            input_types=input_types,
            output_types=output_types,
            context_length=context_length,
            max_output_length=max_output_length,
            available_subscriptions=data["subscription_count"],  # 使用实际订阅数量（不去重）
            shared_by=data["shared_by"],
            used_tokens=tokens_dict.get(model_name, 0),
            coding_score=coding_score,
            providers=provider_infos,
            subscription_platform_count=len(providers_list),
            model_logo_url=model_logo_url,
        )
        model_info_list.append(model_info)

    # 按 Coding 评分倒序排列，评分相同则按 Token 使用量倒序
    # 没有评分的排在最后
    model_info_list.sort(
        key=lambda m: (
            m.coding_score is None,  # None 排在最后
            -(m.coding_score or 0),  # 评分倒序
            -(m.used_tokens or 0)  # Token 使用量倒序
        )
    )

    return model_info_list

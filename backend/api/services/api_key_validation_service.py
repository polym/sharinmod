import httpx
import json
import logging
from api.models.shared_api_key import APIKeyProvider
from typing import Dict, Optional, List, Any

logger = logging.getLogger(__name__)


# Provider API configurations
PROVIDER_CONFIGS = {
    APIKeyProvider.BIGMODEL: {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "test_endpoint": "/models",
        "header_name": "Authorization",
        "test_model": "glm-4"
    },
    APIKeyProvider.ZAI: {
        "base_url": "https://api.z.ai/api/paas/v4",
        "test_endpoint": "/models",
        "header_name": "Authorization",
        "test_model": "gpt-4"
    },
    APIKeyProvider.VOLCENGINE: {
        "base_url": "https://ark.cn-beijing.volces.com/api/coding",
        "test_endpoint": "/v1/models",
        "header_name": "Authorization",
        "test_model": "doubao-seed-code"
    },
    APIKeyProvider.MOONSHOT: {
        "base_url": "https://api.kimi.com/coding/v1",
        "test_endpoint": "/models",
        "header_name": "Authorization",
        "test_model": "moonshot-v1-8k"
    },
    APIKeyProvider.MINIMAX: {
        "base_url": "https://api.minimaxi.com/anthropic",
        # HACK: minmax no model endpoint
        "test_endpoint": "/../v1/files/list",
        "header_name": "Authorization",
        "test_model": "minimax-m2.1"
    },
    APIKeyProvider.OPENROUTER: {
        "base_url": "https://openrouter.ai/api/v1",
        "test_endpoint": "/models",
        "header_name": "Authorization",
        "test_model": "pony-alpha"
    }
}


# Model validation configurations (separate from PROVIDER_CONFIGS)
# These configs are used for model availability validation via actual API calls
# api_type values: "openai", "anthropic", "openrouter"
MODEL_VALIDATION_CONFIGS = {
    APIKeyProvider.BIGMODEL: {
        "base_url": "https://open.bigmodel.cn/api",
        "api_type": "anthropic",
    },
    APIKeyProvider.ZAI: {
        "base_url": "https://z.ai/api",
        "api_type": "anthropic",
    },
    APIKeyProvider.VOLCENGINE: {
        "base_url": "https://ark.cn-beijing.volces.com/api",
        "api_type": "openai",
    },
    APIKeyProvider.MOONSHOT: {
        "base_url": "https://api.moonshot.cn/api",
        "api_type": "openai",
    },
    APIKeyProvider.MINIMAX: {
        "base_url": "https://api.minimaxi.com/api",
        "api_type": "anthropic",
    },
    APIKeyProvider.OPENROUTER: {
        "base_url": "https://openrouter.ai/api",
        "api_type": "openrouter",
    }
}


def get_model_validation_config(provider: str, session: Optional[Any] = None) -> dict:
    """
    获取模型验证配置

    优先级:
    1. 动态提供商：从数据库 provider_configs 读取
    2. 静态提供商：从 MODEL_VALIDATION_CONFIGS 读取

    Args:
        provider: 提供商标识
        session: 数据库会话（可选）

    Returns:
        {
            "base_url": str,
            "api_type": str  # "openai", "anthropic", or "openrouter"
        }
    """
    # 先尝试从数据库读取（动态提供商）
    if session:
        try:
            from sqlmodel import select
            from api.models.provider_config import ProviderConfig
            provider_config = session.exec(
                select(ProviderConfig).where(
                    ProviderConfig.provider_key == provider,
                    ProviderConfig.is_enabled == True
                )
            ).first()
            if provider_config and provider_config.base_url:
                return {
                    "base_url": provider_config.base_url,
                    "api_type": provider_config.custom_llm_provider or "openai",
                }
        except Exception as e:
            logger.warning(f"Failed to read provider config from database: {e}")

    # 静态提供商：从 MODEL_VALIDATION_CONFIGS 读取
    try:
        provider_enum = APIKeyProvider(provider)
        return MODEL_VALIDATION_CONFIGS.get(provider_enum, {})
    except ValueError:
        return {}


async def validate_api_key(provider: str, api_key: str) -> Dict[str, any]:
    """
    Validate API key by making a test API call to provider

    Args:
        provider: API key provider (supports dynamic providers from database)
        api_key: Plain text API key to validate

    Returns:
        Dict with validation result:
        {
            "valid": bool,
            "message": str,
            "provider_info": Optional[Dict]
        }

    Raises:
        ValueError: If provider is not supported
    """
    # Try to convert provider string to APIKeyProvider enum
    try:
        provider_enum = APIKeyProvider(provider)
        if provider_enum not in PROVIDER_CONFIGS:
            raise ValueError(f"Unsupported provider: {provider}")
        config = PROVIDER_CONFIGS[provider_enum]
    except ValueError:
        # Dynamic provider - skip validation for now
        # In the future, could fetch validation config from database
        return {
            "valid": True,
            "message": f"Provider {provider} is a dynamic provider - skipping API validation",
            "provider_info": {
                "provider": provider,
                "status_code": 200
            }
        }

    config = PROVIDER_CONFIGS[provider_enum]
    url = f"{config['base_url']}{config['test_endpoint']}"
    
    # Prepare authorization header
    # For most OpenAI-compatible APIs, format is "Bearer <api_key>"
    headers = {
        config["header_name"]: f"Bearer {api_key}"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            
            # Consider 200-299 as success
            if 200 <= response.status_code < 300:
                return {
                    "valid": True,
                    "message": "API key validation successful",
                    "provider_info": {
                        "provider": provider,
                        "status_code": response.status_code
                    }
                }
            # 401/403 means invalid API key
            elif response.status_code in [401, 403]:
                return {
                    "valid": False,
                    "message": "API key authentication failed - invalid credentials",
                    "provider_info": None
                }
            # Other errors
            else:
                return {
                    "valid": False,
                    "message": f"API key validation failed - provider returned {response.status_code}",
                    "provider_info": None
                }
                
    except httpx.TimeoutException:
        return {
            "valid": False,
            "message": "API key validation timeout - provider API unreachable",
            "provider_info": None
        }
    except Exception as e:
        return {
            "valid": False,
            "message": f"API key validation error: {str(e)}",
            "provider_info": None
        }


async def check_openai_model_async(
    base_url: str,
    api_key: str,
    model: str,
    max_tokens: int = 10
) -> tuple[bool, str]:
    """
    通过真实 API 调用验证 OpenAI 兼容模型是否可用

    Args:
        base_url: 提供商基础 URL
        api_key: API 密钥
        model: 模型名称
        max_tokens: 最大 token 数（默认 10，最小化消耗）

    Returns:
        tuple[bool, str]: (是否可用, 错误信息)
    """
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": max_tokens,
        "stream": False  # 不使用流式
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=data)

            # 状态码 200 即认为成功
            if response.status_code == 200:
                return True, ""

            # 尝试读取错误响应体
            try:
                error_body = response.text
                logger.warning(f"OpenAI model check failed for {model}: HTTP {response.status_code} - {error_body}")
                return False, f"HTTP {response.status_code}: {error_body[:200]}"  # 限制错误信息长度
            except Exception:
                logger.warning(f"OpenAI model check failed for {model}: HTTP {response.status_code}")
                return False, f"HTTP {response.status_code}"

    except httpx.TimeoutException:
        logger.warning(f"OpenAI model check timeout for {model}")
        return False, "验证超时：提供商 API 响应时间过长"
    except Exception as e:
        logger.warning(f"OpenAI model check error for {model}: {e}")
        return False, f"验证错误: {str(e)}"


async def check_anthropic_model_async(
    base_url: str,
    api_key: str,
    model: str,
    max_tokens: int = 10
) -> tuple[bool, str]:
    """
    通过真实 API 调用验证 Anthropic 模型是否可用

    Args:
        base_url: 提供商基础 URL
        api_key: API 密钥
        model: 模型名称
        max_tokens: 最大 token 数（默认 10，最小化消耗）

    Returns:
        tuple[bool, str]: (是否可用, 错误信息)
    """
    url = f"{base_url.rstrip('/')}/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": max_tokens,
        "stream": False  # 不使用流式
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=data)

            # 状态码 200 即认为成功
            if response.status_code == 200:
                return True, ""

            # 尝试读取错误响应体
            try:
                error_body = response.text
                logger.warning(f"Anthropic model check failed for {model}: HTTP {response.status_code} - {error_body}")
                return False, f"HTTP {response.status_code}: {error_body[:200]}"
            except Exception:
                logger.warning(f"Anthropic model check failed for {model}: HTTP {response.status_code}")
                return False, f"HTTP {response.status_code}"

    except httpx.TimeoutException:
        logger.warning(f"Anthropic model check timeout for {model}")
        return False, "验证超时：提供商 API 响应时间过长"
    except Exception as e:
        logger.warning(f"Anthropic model check error for {model}: {e}")
        return False, f"验证错误: {str(e)}"


async def validate_models_availability(
    provider: str,
    api_key: str,
    selected_models: List[str],
    session: Optional[Any] = None
) -> Dict[str, Any]:
    """
    验证选择的模型在提供商侧是否可用（通过真实 API 调用）

    Args:
        provider: 提供商标识
        api_key: API 密钥
        selected_models: 用户选择的模型列表
        session: 数据库会话（用于动态提供商）

    Returns:
        {
            "valid": bool,
            "message": str,
            "available_models": List[str],
            "unavailable_models": List[str],
            "model_errors": Dict[str, str]  # 模型名 -> 错误信息
        }
    """
    if not selected_models:
        return {
            "valid": True,
            "message": "No models specified",
            "available_models": [],
            "unavailable_models": [],
            "model_errors": {}
        }

    # 从配置源获取 base_url 和 api_type
    config = get_model_validation_config(provider, session)
    if not config:
        return {
            "valid": False,
            "message": f"Provider {provider} not configured",
            "available_models": [],
            "unavailable_models": selected_models.copy(),
            "model_errors": {model: "Provider not configured" for model in selected_models}
        }

    base_url = config.get("base_url")
    api_type = config.get("api_type", "openai")

    if not base_url:
        return {
            "valid": False,
            "message": f"Provider {provider} has no base_url configured",
            "available_models": [],
            "unavailable_models": selected_models.copy(),
            "model_errors": {model: "Provider base_url not configured" for model in selected_models}
        }

    # 逐个验证模型，记录每个模型的错误信息
    available = []
    unavailable = []
    model_errors = {}

    for model in selected_models:
        try:
            if api_type == "anthropic":
                is_available, error_msg = await check_anthropic_model_async(base_url, api_key, model)
            elif api_type in ("openai", "openrouter"):
                is_available, error_msg = await check_openai_model_async(base_url, api_key, model)
            else:
                # 未知 api_type，默认尝试 openai 方式
                is_available, error_msg = await check_openai_model_async(base_url, api_key, model)

            if is_available:
                available.append(model)
            else:
                unavailable.append(model)
                model_errors[model] = error_msg or "模型验证失败：未知错误"

        except httpx.TimeoutException:
            unavailable.append(model)
            model_errors[model] = "验证超时：提供商 API 响应时间过长"
        except httpx.HTTPStatusError as e:
            unavailable.append(model)
            try:
                error_body = e.response.text
                model_errors[model] = f"HTTP {e.response.status_code}: {error_body[:200]}"
            except Exception:
                model_errors[model] = f"HTTP 错误: {e.response.status_code}"
        except Exception as e:
            unavailable.append(model)
            model_errors[model] = f"验证错误: {str(e)}"

    if unavailable:
        return {
            "valid": False,
            "message": f"以下模型不可用: {', '.join(unavailable)}",
            "available_models": available,
            "unavailable_models": unavailable,
            "model_errors": model_errors
        }

    return {
        "valid": True,
        "message": "All models are available",
        "available_models": available,
        "unavailable_models": [],
        "model_errors": {}
    }

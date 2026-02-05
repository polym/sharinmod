import httpx
from api.models.shared_api_key import APIKeyProvider
from typing import Dict, Optional


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
    }
}


async def validate_api_key(provider: APIKeyProvider, api_key: str) -> Dict[str, any]:
    """
    Validate API key by making a test API call to provider
    
    Args:
        provider: API key provider (bigmodel or z.ai)
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
    if provider not in PROVIDER_CONFIGS:
        raise ValueError(f"Unsupported provider: {provider}")
    
    config = PROVIDER_CONFIGS[provider]
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

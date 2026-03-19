import httpx
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


async def validate_api_key(provider: str, api_key: str, db) -> Dict[str, any]:
    """
    Validate API key by making a test API call to provider

    Args:
        provider: API key provider (supports dynamic providers from database)
        api_key: Plain text API key to validate
        db: Database session for looking up provider configuration

    Returns:
        Dict with validation result:
        {
            "valid": bool,
            "message": str,
            "provider_info": Optional[Dict]
        }

    Raises:
        ValueError: If provider is not configured in database
    """
    from api.services.provider_config_service import get_provider_by_key

    # Look up provider configuration from database
    provider_config = get_provider_by_key(db, provider)

    if not provider_config or not provider_config.base_url:
        # Provider not found or no base_url configured - skip validation
        # This allows dynamic providers to be added without requiring validation endpoints
        logger.info(f"Provider {provider} has no validation configuration - skipping API validation")
        return {
            "valid": True,
            "message": f"Provider {provider} has no validation endpoint configured - API key accepted",
            "provider_info": {
                "provider": provider,
                "status_code": 200
            }
        }

    base_url = provider_config.base_url
    custom_provider = provider_config.custom_llm_provider or "openai"

    # Skip validation if no validation_endpoint is configured
    if not provider_config.validation_endpoint:
        logger.info(f"Provider {provider} has no validation_endpoint configured - skipping API validation")
        return {
            "valid": True,
            "message": f"Provider {provider} has no validation endpoint configured - API key accepted",
            "provider_info": {
                "provider": provider,
                "status_code": 200
            }
        }

    test_endpoint = provider_config.validation_endpoint

    url = f"{base_url}{test_endpoint}"

    # Prepare authorization header
    # For most OpenAI-compatible APIs, format is "Bearer <api_key>"
    headers = {
        "Authorization": f"Bearer {api_key}"
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

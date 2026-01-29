import httpx
from api.models.shared_token import TokenVendor
from typing import Dict, Optional


# Vendor API configurations
VENDOR_CONFIGS = {
    TokenVendor.BIGMODEL: {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "test_endpoint": "/models",
        "header_name": "Authorization",
        "test_model": "glm-4"
    },
    TokenVendor.ZAI: {
        "base_url": "https://api.z.ai/v1",
        "test_endpoint": "/models",
        "header_name": "Authorization",
        "test_model": "gpt-4"
    }
}


async def validate_vendor_token(vendor: TokenVendor, token: str) -> Dict[str, any]:
    """
    Validate token by making a test API call to vendor
    
    Args:
        vendor: Token vendor (bigmodel or z.ai)
        token: Plain text token to validate
        
    Returns:
        Dict with validation result:
        {
            "valid": bool,
            "message": str,
            "vendor_info": Optional[Dict]
        }
        
    Raises:
        ValueError: If vendor is not supported
    """
    if vendor not in VENDOR_CONFIGS:
        raise ValueError(f"Unsupported vendor: {vendor}")
    
    config = VENDOR_CONFIGS[vendor]
    url = f"{config['base_url']}{config['test_endpoint']}"
    
    # Prepare authorization header
    # For most OpenAI-compatible APIs, format is "Bearer <token>"
    headers = {
        config["header_name"]: f"Bearer {token}"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            
            # Consider 200-299 as success
            if 200 <= response.status_code < 300:
                return {
                    "valid": True,
                    "message": "Token validation successful",
                    "vendor_info": {
                        "vendor": vendor,
                        "status_code": response.status_code
                    }
                }
            # 401/403 means invalid token
            elif response.status_code in [401, 403]:
                return {
                    "valid": False,
                    "message": "Token authentication failed - invalid credentials",
                    "vendor_info": None
                }
            # Other errors
            else:
                return {
                    "valid": False,
                    "message": f"Token validation failed - vendor returned {response.status_code}",
                    "vendor_info": None
                }
                
    except httpx.TimeoutException:
        return {
            "valid": False,
            "message": "Token validation timeout - vendor API unreachable",
            "vendor_info": None
        }
    except Exception as e:
        return {
            "valid": False,
            "message": f"Token validation error: {str(e)}",
            "vendor_info": None
        }

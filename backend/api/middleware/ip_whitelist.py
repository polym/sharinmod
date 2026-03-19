"""
IP whitelist middleware for protecting webhook endpoints

This middleware checks if the request source IP is in the configured whitelist.
If not in whitelist, returns 403 Forbidden.
"""
import ipaddress
import logging
from fastapi import Request, status
from starlette.responses import JSONResponse
from api.config import settings

logger = logging.getLogger(__name__)

# Trusted proxy IPs that can set X-Forwarded-For header
TRUSTED_PROXIES = {"127.0.0.1", "::1", "localhost"}


def _ip_in_whitelist(client_ip: str, whitelist: list[str]) -> bool:
    """Check whether client_ip matches any entry in the whitelist.

    Supports exact IPs and CIDR notation (e.g. 10.0.0.0/8).
    """
    try:
        addr = ipaddress.ip_address(client_ip)
    except ValueError:
        return False
    for entry in whitelist:
        try:
            if addr in ipaddress.ip_network(entry, strict=False):
                return True
        except ValueError:
            logger.warning(f"[IP_WHITELIST] Invalid whitelist entry skipped: {entry}")
    return False


async def ip_whitelist_middleware(request: Request, call_next):
    """
    Middleware to check request IP against whitelist

    Skips check if whitelist is empty (disabled).
    Only applies to webhook endpoints.

    Security: Only trusts X-Forwarded-For from known proxy IPs to prevent spoofing.
    """
    # Check if this is a webhook endpoint
    if not request.url.path.startswith("/api/v1/webhooks"):
        return await call_next(request)

    # Get client IP
    # Only trust X-Forwarded-For if request comes from a trusted proxy
    direct_ip = request.client.host if request.client else "unknown"

    if direct_ip in TRUSTED_PROXIES:
        # Request from trusted proxy, use X-Forwarded-For
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first (original client)
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = direct_ip
    else:
        # Direct request, not through trusted proxy
        client_ip = direct_ip

    # Log for debugging
    logger.debug(f"[IP_WHITELIST] Path: {request.url.path}, Direct IP: {direct_ip}, Client IP: {client_ip}, Whitelist: {settings.LITELLM_WEBHOOK_IP_WHITELIST}")

    # Check whitelist
    whitelist = settings.LITELLM_WEBHOOK_IP_WHITELIST
    if whitelist and not _ip_in_whitelist(client_ip, whitelist):
        logger.warning(f"[IP_WHITELIST] REJECTED: IP {client_ip} not in whitelist")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": f"IP {client_ip} is not authorized to access this endpoint"},
        )

    logger.debug(f"[IP_WHITELIST] ALLOWED: IP {client_ip} passed whitelist check")
    return await call_next(request)

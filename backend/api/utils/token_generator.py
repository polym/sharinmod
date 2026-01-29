"""
Token generation utilities for creating secure random tokens
"""
import secrets
import base64
from sqlmodel import Session, select


def generate_unified_token() -> str:
    """
    Generate a secure 32-byte random token
    
    Returns:
        URL-safe base64-encoded 32-byte random string (~44 characters)
    """
    random_bytes = secrets.token_bytes(32)
    token = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')
    return token


def is_token_unique(session: Session, token: str) -> bool:
    """
    Check if generated token is unique
    
    Args:
        session: Database session
        token: Token to check
        
    Returns:
        True if token doesn't exist in database, False otherwise
    """
    from api.models.unified_token import UnifiedToken
    
    statement = select(UnifiedToken).where(UnifiedToken.token == token)
    existing = session.exec(statement).first()
    return existing is None

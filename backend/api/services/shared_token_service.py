from sqlmodel import Session, select
from api.models.shared_token import SharedToken, TokenVendor, TokenStatus
from api.models.user import User
from api.utils.encryption import encrypt_token, decrypt_token
from api.services.token_validation_service import validate_vendor_token
from api.services.token_usage_service import log_token_usage
from api.models.token_usage import TokenAction
from typing import List, Optional, Dict
from datetime import datetime
from fastapi import HTTPException


def check_vendor_token_exists(session: Session, user_id: int, vendor: TokenVendor) -> bool:
    """
    Check if user already has a token for this vendor
    
    Args:
        session: Database session
        user_id: User ID
        vendor: Token vendor
        
    Returns:
        True if token exists for this vendor, False otherwise
    """
    statement = select(SharedToken).where(
        SharedToken.user_id == user_id,
        SharedToken.vendor == vendor
    )
    result = session.exec(statement).first()
    return result is not None


async def create_shared_token(
    session: Session,
    user: User,
    vendor: TokenVendor,
    token: str,
    token_metadata: Optional[str] = None
) -> Dict[str, any]:
    """
    Create a new shared token with validation
    
    Args:
        session: Database session
        user: Current authenticated user
        vendor: Token vendor
        token: Plain text token to share
        token_metadata: Optional metadata JSON string
        
    Returns:
        Dict with created token info and validation result
        
    Raises:
        HTTPException: If duplicate vendor or validation fails
    """
    # Check if user already has a token for this vendor
    if check_vendor_token_exists(session, user.id, vendor):
        raise HTTPException(
            status_code=400,
            detail=f"You already have a token for {vendor.value}. Each account can only add one token per vendor."
        )
    
    # Validate token with vendor API
    validation_result = await validate_vendor_token(vendor, token)
    
    if not validation_result["valid"]:
        raise HTTPException(
            status_code=400,
            detail=f"Token validation failed: {validation_result['message']}"
        )
    
    # Encrypt token before storage
    encrypted = encrypt_token(token)
    
    # Create shared token record
    shared_token = SharedToken(
        user_id=user.id,
        vendor=vendor,
        encrypted_token=encrypted,
        status=TokenStatus.ACTIVE,
        token_metadata=token_metadata
    )
    
    session.add(shared_token)
    session.commit()
    session.refresh(shared_token)
    
    # Log sharing action in usage history
    log_token_usage(
        db=session,
        user_id=user.id,
        token_id=str(shared_token.id),
        action=TokenAction.SHARED,
        details=f"Shared {vendor.value} token"
    )
    
    return {
        "token": shared_token,
        "validation": validation_result
    }


def get_user_shared_tokens(session: Session, user_id: int) -> List[Dict]:
    """
    Get all shared tokens for a user
    
    Args:
        session: Database session
        user_id: User ID
        
    Returns:
        List of dicts compatible with SharedTokenResponse
    """
    statement = select(SharedToken).where(
        SharedToken.user_id == user_id
    ).order_by(SharedToken.created_at.desc())
    
    results = session.exec(statement).all()
    
    # Convert to dicts (Pydantic will handle SharedTokenResponse validation)
    return [token.model_dump() for token in results]

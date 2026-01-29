from sqlmodel import Session, select, func
from datetime import datetime, timezone
from api.models.shared_token import SharedToken, TokenStatus
from api.models.user import User
from api.schemas.token_discovery import TokenDiscoveryItem
from typing import List, Tuple


def get_available_tokens(
    db: Session,
    current_user_id: int,
    page: int = 1,
    page_size: int = 10
) -> Tuple[List[TokenDiscoveryItem], int]:
    """
    Get list of available shared tokens for discovery
    
    Excludes:
    - Current user's own tokens
    - Inactive or revoked tokens
    
    Args:
        db: Database session
        current_user_id: Current user's ID (to exclude their tokens)
        page: Page number (1-indexed)
        page_size: Items per page
        
    Returns:
        Tuple of (list of TokenDiscoveryItem, total count)
    """
    # Build base query with join to users table
    base_query = (
        select(SharedToken, User.email)
        .join(User, SharedToken.user_id == User.id)
        .where(
            SharedToken.user_id != current_user_id,  # Exclude own tokens
            SharedToken.status == TokenStatus.ACTIVE  # Only active tokens
        )
        .order_by(SharedToken.created_at.desc())
    )
    
    # Get total count
    count_query = (
        select(func.count())
        .select_from(SharedToken)
        .where(
            SharedToken.user_id != current_user_id,
            SharedToken.status == TokenStatus.ACTIVE
        )
    )
    total = db.exec(count_query).one()
    
    # Get paginated results
    offset = (page - 1) * page_size
    paginated_query = base_query.offset(offset).limit(page_size)
    results = db.exec(paginated_query).all()
    
    # Build discovery items
    now = datetime.now(timezone.utc)
    items = []
    
    for token, email in results:
        # Extract username from email (before @)
        provider_username = email.split('@')[0] if email else "unknown"
        
        # Calculate sharing duration in days
        created_at_aware = token.created_at.replace(tzinfo=timezone.utc) if token.created_at.tzinfo is None else token.created_at
        duration = now - created_at_aware
        shared_duration_days = duration.days
        
        item = TokenDiscoveryItem(
            id=token.id,
            vendor=token.vendor,
            provider_username=provider_username,
            shared_duration_days=shared_duration_days,
            total_uses=token.total_uses,
            created_at=token.created_at
        )
        items.append(item)
    
    return items, total

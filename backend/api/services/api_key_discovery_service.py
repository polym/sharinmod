from sqlmodel import Session, select, func
from datetime import datetime, timezone
from api.models.shared_api_key import SharedAPIKey, APIKeyStatus
from api.models.user import User
from api.schemas.api_key_discovery import APIKeyDiscoveryItem
from typing import List, Tuple


def get_available_api_keys(
    db: Session,
    current_user_id: int,
    page: int = 1,
    page_size: int = 10
) -> Tuple[List[APIKeyDiscoveryItem], int]:
    """
    Get list of available shared API keys for discovery
    
    Excludes:
    - Current user's own API keys
    - Inactive or revoked API keys
    
    Args:
        db: Database session
        current_user_id: Current user's ID (to exclude their API keys)
        page: Page number (1-indexed)
        page_size: Items per page
        
    Returns:
        Tuple of (list of APIKeyDiscoveryItem, total count)
    """
    # Build base query with join to users table
    base_query = (
        select(SharedAPIKey, User.email)
        .join(User, SharedAPIKey.user_id == User.id)
        .where(
            SharedAPIKey.user_id != current_user_id,  # Exclude own API keys
            SharedAPIKey.status == APIKeyStatus.ACTIVE  # Only active API keys
        )
        .order_by(SharedAPIKey.created_at.desc())
    )
    
    # Get total count
    count_query = (
        select(func.count())
        .select_from(SharedAPIKey)
        .where(
            SharedAPIKey.user_id != current_user_id,
            SharedAPIKey.status == APIKeyStatus.ACTIVE
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
    
    for api_key, email in results:
        # Extract username from email (before @)
        provider_username = email.split('@')[0] if email else "unknown"
        
        # Calculate sharing duration in days
        created_at_aware = api_key.created_at.replace(tzinfo=timezone.utc) if api_key.created_at.tzinfo is None else api_key.created_at
        duration = now - created_at_aware
        shared_duration_days = duration.days
        
        item = APIKeyDiscoveryItem(
            id=api_key.id,
            provider=api_key.provider,
            provider_username=provider_username,
            shared_duration_days=shared_duration_days,
            total_uses=api_key.total_uses,
            created_at=api_key.created_at
        )
        items.append(item)
    
    return items, total

"""
API key usage service layer for tracking and querying usage history
"""
from sqlmodel import Session, select, func, desc
from api.models.api_key_usage import APIKeyUsageHistory, APIKeyAction
from api.schemas.api_key_usage import APIKeyUsageStatistics, APIKeyUsageHistoryList, APIKeyUsageHistoryResponse
from typing import Optional
from datetime import datetime


def get_user_usage_history(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> APIKeyUsageHistoryList:
    """
    Get paginated usage history for a user
    
    Args:
        db: Database session
        user_id: User ID to query
        page: Page number (1-indexed)
        page_size: Number of items per page
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        APIKeyUsageHistoryList with paginated results
    """
    # Build query
    query = select(APIKeyUsageHistory).where(APIKeyUsageHistory.user_id == user_id)
    
    # Apply date filters if provided
    if start_date:
        query = query.where(APIKeyUsageHistory.timestamp >= start_date)
    if end_date:
        query = query.where(APIKeyUsageHistory.timestamp <= end_date)
    
    # Order by most recent first
    query = query.order_by(desc(APIKeyUsageHistory.timestamp))
    
    # Get total count
    count_query = select(func.count()).select_from(APIKeyUsageHistory).where(
        APIKeyUsageHistory.user_id == user_id
    )
    if start_date:
        count_query = count_query.where(APIKeyUsageHistory.timestamp >= start_date)
    if end_date:
        count_query = count_query.where(APIKeyUsageHistory.timestamp <= end_date)
    
    total = db.exec(count_query).one()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    results = db.exec(query).all()
    
    return APIKeyUsageHistoryList(
        total=total,
        page=page,
        page_size=page_size,
        items=[APIKeyUsageHistoryResponse.model_validate(item) for item in results]
    )


def get_user_usage_statistics(db: Session, user_id: int) -> APIKeyUsageStatistics:
    """
    Get usage statistics for a user
    
    Args:
        db: Database session
        user_id: User ID to query
        
    Returns:
        APIKeyUsageStatistics with aggregated data
    """
    # Get total actions
    total_query = select(func.count()).select_from(APIKeyUsageHistory).where(
        APIKeyUsageHistory.user_id == user_id
    )
    total_actions = db.exec(total_query).one()
    
    # Get action counts by type
    def count_actions(action: APIKeyAction) -> int:
        query = select(func.count()).select_from(APIKeyUsageHistory).where(
            APIKeyUsageHistory.user_id == user_id,
            APIKeyUsageHistory.action == action
        )
        return db.exec(query).one()
    
    api_keys_shared = count_actions(APIKeyAction.SHARED)
    api_keys_consumed = count_actions(APIKeyAction.CONSUMED)
    api_keys_generated = count_actions(APIKeyAction.GENERATED)
    
    # Get first and last activity timestamps
    timestamp_query = select(
        func.min(APIKeyUsageHistory.timestamp),
        func.max(APIKeyUsageHistory.timestamp)
    ).where(APIKeyUsageHistory.user_id == user_id)
    
    result = db.exec(timestamp_query).one()
    first_activity, last_activity = result if result else (None, None)
    
    return APIKeyUsageStatistics(
        total_actions=total_actions,
        api_keys_shared=api_keys_shared,
        api_keys_consumed=api_keys_consumed,
        api_keys_generated=api_keys_generated,
        first_activity=first_activity,
        last_activity=last_activity
    )


def log_api_key_usage(
    db: Session,
    user_id: int,
    action: APIKeyAction,
    api_key_id: Optional[str] = None,
    details: Optional[str] = None
) -> APIKeyUsageHistory:
    """
    Log an API key usage action
    
    Args:
        db: Database session
        user_id: User ID performing the action
        action: Type of action
        api_key_id: Optional API key identifier
        details: Optional JSON string with additional context
        
    Returns:
        Created APIKeyUsageHistory record
    """
    usage = APIKeyUsageHistory(
        user_id=user_id,
        api_key_id=api_key_id,
        action=action,
        details=details
    )
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage

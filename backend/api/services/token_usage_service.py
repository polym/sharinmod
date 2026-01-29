"""
Token usage service layer for tracking and querying usage history
"""
from sqlmodel import Session, select, func, desc
from api.models.token_usage import TokenUsageHistory, TokenAction
from api.schemas.token_usage import TokenUsageStatistics, TokenUsageHistoryList, TokenUsageHistoryResponse
from typing import Optional
from datetime import datetime


def get_user_usage_history(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> TokenUsageHistoryList:
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
        TokenUsageHistoryList with paginated results
    """
    # Build query
    query = select(TokenUsageHistory).where(TokenUsageHistory.user_id == user_id)
    
    # Apply date filters if provided
    if start_date:
        query = query.where(TokenUsageHistory.timestamp >= start_date)
    if end_date:
        query = query.where(TokenUsageHistory.timestamp <= end_date)
    
    # Order by most recent first
    query = query.order_by(desc(TokenUsageHistory.timestamp))
    
    # Get total count
    count_query = select(func.count()).select_from(TokenUsageHistory).where(
        TokenUsageHistory.user_id == user_id
    )
    if start_date:
        count_query = count_query.where(TokenUsageHistory.timestamp >= start_date)
    if end_date:
        count_query = count_query.where(TokenUsageHistory.timestamp <= end_date)
    
    total = db.exec(count_query).one()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    results = db.exec(query).all()
    
    return TokenUsageHistoryList(
        total=total,
        page=page,
        page_size=page_size,
        items=[TokenUsageHistoryResponse.model_validate(item) for item in results]
    )


def get_user_usage_statistics(db: Session, user_id: int) -> TokenUsageStatistics:
    """
    Get usage statistics for a user
    
    Args:
        db: Database session
        user_id: User ID to query
        
    Returns:
        TokenUsageStatistics with aggregated data
    """
    # Get total actions
    total_query = select(func.count()).select_from(TokenUsageHistory).where(
        TokenUsageHistory.user_id == user_id
    )
    total_actions = db.exec(total_query).one()
    
    # Get action counts by type
    def count_actions(action: TokenAction) -> int:
        query = select(func.count()).select_from(TokenUsageHistory).where(
            TokenUsageHistory.user_id == user_id,
            TokenUsageHistory.action == action
        )
        return db.exec(query).one()
    
    tokens_shared = count_actions(TokenAction.SHARED)
    tokens_consumed = count_actions(TokenAction.CONSUMED)
    tokens_generated = count_actions(TokenAction.GENERATED)
    
    # Get first and last activity timestamps
    timestamp_query = select(
        func.min(TokenUsageHistory.timestamp),
        func.max(TokenUsageHistory.timestamp)
    ).where(TokenUsageHistory.user_id == user_id)
    
    result = db.exec(timestamp_query).one()
    first_activity, last_activity = result if result else (None, None)
    
    return TokenUsageStatistics(
        total_actions=total_actions,
        tokens_shared=tokens_shared,
        tokens_consumed=tokens_consumed,
        tokens_generated=tokens_generated,
        first_activity=first_activity,
        last_activity=last_activity
    )


def log_token_usage(
    db: Session,
    user_id: int,
    action: TokenAction,
    token_id: Optional[str] = None,
    details: Optional[str] = None
) -> TokenUsageHistory:
    """
    Log a token usage action
    
    Args:
        db: Database session
        user_id: User ID performing the action
        action: Type of action
        token_id: Optional token identifier
        details: Optional JSON string with additional context
        
    Returns:
        Created TokenUsageHistory record
    """
    usage = TokenUsageHistory(
        user_id=user_id,
        token_id=token_id,
        action=action,
        details=details
    )
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage

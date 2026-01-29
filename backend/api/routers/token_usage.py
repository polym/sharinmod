"""
Token usage history router for user activity tracking
"""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from api.database import get_db
from api.dependencies.auth import get_current_user
from api.models.user import User
from api.schemas.token_usage import TokenUsageHistoryList, TokenUsageStatistics
from api.services.token_usage_service import get_user_usage_history, get_user_usage_statistics
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/users/me/token-usage", tags=["token-usage"])


@router.get("", response_model=TokenUsageHistoryList)
def get_my_token_usage_history(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    start_date: Optional[datetime] = Query(None, description="Filter start date"),
    end_date: Optional[datetime] = Query(None, description="Filter end date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's token usage history with pagination
    
    Requires JWT authentication
    Supports optional date range filtering
    """
    return get_user_usage_history(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/stats", response_model=TokenUsageStatistics)
def get_my_token_usage_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's token usage statistics
    
    Requires JWT authentication
    Returns aggregated statistics including action counts and activity timestamps
    """
    return get_user_usage_statistics(db=db, user_id=current_user.id)

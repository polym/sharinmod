"""
Usage log router for API call usage tracking
"""
from datetime import datetime, date, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from api.database import get_db
from api.dependencies.auth import get_current_user
from api.models.user import User
from api.models.usage_log import UsageLogStatus
from api.schemas.usage_log import UsageLogList, UsageOverviewResponse
from api.services.usage_log_service import get_user_usage_logs, get_user_usage_overview

router = APIRouter(prefix="/api/usage", tags=["usage"])

# UTC+8 offset for date handling
UTC8_OFFSET = timedelta(hours=8)


@router.get("/logs", response_model=UsageLogList)
def get_my_usage_logs(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    start_date: Optional[date] = Query(None, description="Filter start date (UTC+8)"),
    end_date: Optional[date] = Query(None, description="Filter end date (UTC+8)"),
    status: Optional[UsageLogStatus] = Query(None, description="Filter by status (success/failure)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's API usage logs with pagination

    Requires JWT authentication
    Supports optional date range filtering (UTC+8)
    Supports optional status filtering
    """
    return get_user_usage_logs(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        start_date=start_date,
        end_date=end_date,
        status=status
    )


@router.get("/overview", response_model=UsageOverviewResponse)
def get_my_usage_overview(
    target_date: Optional[date] = Query(None, description="Target date (UTC+8), defaults to today"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's usage overview for a specific date

    Requires JWT authentication
    Returns aggregated statistics including:
    - Total/successful/failed requests
    - Total/input/output tokens
    - 24-hour token distribution

    Default date is today (UTC+8)
    """
    # Default to today in UTC+8
    if target_date is None:
        target_date = (datetime.now(timezone.utc) + UTC8_OFFSET).date()

    return get_user_usage_overview(
        db=db,
        user_id=current_user.id,
        target_date=target_date
    )

"""
Service layer for usage log tracking and querying
"""
import logging
from datetime import datetime, date, timedelta, timezone
from typing import Optional

from sqlmodel import Session, select, func, desc
from sqlalchemy import text

from api.models.usage_log import UsageLog, UsageLogStatus, UsageLogKind
from api.models.unified_api_key import UnifiedAPIKey
from api.models.subscription import Subscription
from api.schemas.usage_log import (
    UsageLogList,
    UsageLogResponse,
    UsageOverviewResponse,
    HourlyTokenData
)
from api.schemas.litellm_callback import LiteLLMCallbackRequest

logger = logging.getLogger(__name__)

# UTC+8 offset in hours
UTC8_OFFSET = timedelta(hours=8)


def create_usage_log(
    db: Session,
    user_id: int,
    callback_data: LiteLLMCallbackRequest,
    subscription: Optional[Subscription] = None
) -> Optional[UsageLog]:
    """
    Create a usage log entry from LiteLLM callback data

    Args:
        db: Database session
        user_id: User ID who made the API call
        callback_data: Parsed LiteLLM callback data
        subscription: Subscription linking to contributor (optional, not stored but used for stats)

    Returns:
        Created UsageLog record or None if creation fails
    """
    try:
        # Calculate TTFT
        ttft = None
        if callback_data.completion_start_time and callback_data.start_time:
            ttft = callback_data.completion_start_time - callback_data.start_time
        elif callback_data.response_time:
            ttft = callback_data.response_time

        # Extract model_id
        model_id = callback_data.model_id
        if not model_id and callback_data.hidden_params:
            model_id = callback_data.hidden_params.model_id

        # Get unified_api_key_name from api_key_hash
        unified_api_key_id = None
        unified_api_key_name = None
        if callback_data.metadata and callback_data.metadata.user_api_key_hash:
            api_key_hash = callback_data.metadata.user_api_key_hash
            key_statement = select(UnifiedAPIKey).where(
                UnifiedAPIKey.api_key_hash == api_key_hash
            )
            unified_key = db.exec(key_statement).first()
            if unified_key:
                unified_api_key_id = unified_key.id
                unified_api_key_name = unified_key.api_key_name

        # Determine kind: own (contributor), shared (consumer), or direct (no subscription)
        kind = UsageLogKind.DIRECT
        if subscription:
            if subscription.user_id == user_id:
                kind = UsageLogKind.OWN  # User is the contributor
            else:
                kind = UsageLogKind.SHARED  # User is consuming someone else's API key

        # Create usage log
        usage_log = UsageLog(
            user_id=user_id,
            unified_api_key_id=unified_api_key_id,
            unified_api_key_name=unified_api_key_name,
            model_id=model_id,
            model_name=callback_data.model,
            status=UsageLogStatus.SUCCESS,
            kind=kind,
            total_duration=callback_data.response_time,
            ttft=ttft,
            input_tokens=callback_data.prompt_tokens,
            output_tokens=callback_data.completion_tokens,
            total_tokens=callback_data.total_tokens,
            request_time=datetime.fromtimestamp(callback_data.end_time, tz=timezone.utc)
        )

        db.add(usage_log)
        db.commit()
        db.refresh(usage_log)

        logger.info(f"Created usage log: user_id={user_id}, model={callback_data.model}, tokens={callback_data.total_tokens}")
        return usage_log

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create usage log: {e}")
        return None


def create_failure_usage_log(
    db: Session,
    user_id: int,
    model: Optional[str],
    error_message: Optional[str],
    model_id: Optional[str] = None,
    unified_api_key_id: Optional[int] = None,
    unified_api_key_name: Optional[str] = None,
    kind: UsageLogKind = UsageLogKind.DIRECT
) -> Optional[UsageLog]:
    """
    Create a failure usage log entry

    Args:
        db: Database session
        user_id: User ID who made the API call
        model: Model name (optional)
        error_message: Error message (optional)
        model_id: Model identifier (optional)
        unified_api_key_id: Unified API key ID (optional)
        unified_api_key_name: Unified API key name (optional)
        kind: Who provided the API key (default: direct)

    Returns:
        Created UsageLog record or None if creation fails
    """
    try:
        usage_log = UsageLog(
            user_id=user_id,
            unified_api_key_id=unified_api_key_id,
            unified_api_key_name=unified_api_key_name,
            model_id=model_id,
            model_name=model or "unknown",
            status=UsageLogStatus.FAILURE,
            kind=kind,
            total_duration=None,
            ttft=None,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            request_time=datetime.now(timezone.utc)
        )

        db.add(usage_log)
        db.commit()
        db.refresh(usage_log)

        logger.info(f"Created failure usage log: user_id={user_id}, model={model}, error={error_message}")
        return usage_log

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create failure usage log: {e}")
        return None


def get_user_usage_logs(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[UsageLogStatus] = None
) -> UsageLogList:
    """
    Get paginated usage logs for a user

    Args:
        db: Database session
        user_id: User ID to query
        page: Page number (1-indexed)
        page_size: Number of items per page
        start_date: Optional start date filter (UTC+8)
        end_date: Optional end date filter (UTC+8)
        status: Optional status filter (success/failure)

    Returns:
        UsageLogList with paginated results
    """
    # Build base query with user filter
    query = select(UsageLog).where(UsageLog.user_id == user_id)

    # Apply filters using helper function to avoid duplication
    query = _apply_date_and_status_filters(query, start_date, end_date, status)

    # Get total count using the same filters
    count_query = select(func.count()).select_from(UsageLog).where(UsageLog.user_id == user_id)
    count_query = _apply_date_and_status_filters(count_query, start_date, end_date, status)
    total = db.exec(count_query).one()

    # Order by most recent first and paginate
    query = query.order_by(desc(UsageLog.request_time))
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    results = db.exec(query).all()

    return UsageLogList(
        total=total,
        page=page,
        page_size=page_size,
        items=[UsageLogResponse.model_validate(item) for item in results]
    )


def _apply_date_and_status_filters(query, start_date: Optional[date], end_date: Optional[date], status: Optional[UsageLogStatus]):
    """
    Apply date and status filters to a query (shared between count and main query)

    Args:
        query: SQLModel query to apply filters to
        start_date: Optional start date filter (UTC+8)
        end_date: Optional end date filter (UTC+8)
        status: Optional status filter

    Returns:
        Query with filters applied
    """
    # Apply date filters if provided (convert UTC+8 date to UTC range)
    if start_date:
        # start_date in UTC+8, convert to UTC start (00:00:00 UTC+8 = 16:00:00 previous day UTC)
        utc_start = datetime.combine(start_date, datetime.min.time()) - UTC8_OFFSET
        query = query.where(UsageLog.request_time >= utc_start)

    if end_date:
        # end_date in UTC+8, convert to UTC end (23:59:59 UTC+8 = 15:59:59 next day UTC)
        utc_end = datetime.combine(end_date, datetime.max.time()) - UTC8_OFFSET
        query = query.where(UsageLog.request_time <= utc_end)

    # Apply status filter
    if status:
        query = query.where(UsageLog.status == status)

    return query


def get_user_usage_overview(
    db: Session,
    user_id: int,
    target_date: date
) -> UsageOverviewResponse:
    """
    Get usage overview for a user on a specific date (UTC+8)

    Args:
        db: Database session
        user_id: User ID to query
        target_date: Date to query (UTC+8)

    Returns:
        UsageOverviewResponse with aggregated data
    """
    # Convert target_date (UTC+8) to UTC range
    # 00:00:00 UTC+8 = 16:00:00 previous day UTC
    # 23:59:59 UTC+8 = 15:59:59 next day UTC
    utc_start = datetime.combine(target_date, datetime.min.time()) - UTC8_OFFSET
    utc_end = datetime.combine(target_date, datetime.max.time()) - UTC8_OFFSET

    # Get total requests
    total_query = select(func.count()).select_from(UsageLog).where(
        UsageLog.user_id == user_id,
        UsageLog.request_time >= utc_start,
        UsageLog.request_time <= utc_end
    )
    total_requests = db.exec(total_query).one()

    # Get successful requests
    success_query = select(func.count()).select_from(UsageLog).where(
        UsageLog.user_id == user_id,
        UsageLog.request_time >= utc_start,
        UsageLog.request_time <= utc_end,
        UsageLog.status == UsageLogStatus.SUCCESS
    )
    successful_requests = db.exec(success_query).one()

    # Failed requests
    failed_requests = total_requests - successful_requests

    # Get token totals
    token_query = select(
        func.sum(UsageLog.input_tokens),
        func.sum(UsageLog.output_tokens),
        func.sum(UsageLog.total_tokens)
    ).where(
        UsageLog.user_id == user_id,
        UsageLog.request_time >= utc_start,
        UsageLog.request_time <= utc_end
    )
    result = db.exec(token_query).one()
    input_tokens = result[0] or 0
    output_tokens = result[1] or 0
    total_tokens = result[2] or 0

    # Get 24-hour distribution
    # Convert request_time to UTC+8 hour and group by hour
    hourly_query = text("""
        SELECT CAST(strftime('%H', datetime(request_time, '+8 hours')) AS INTEGER) as hour,
               SUM(total_tokens) as tokens
        FROM usage_logs
        WHERE user_id = :user_id
          AND request_time >= :utc_start
          AND request_time <= :utc_end
        GROUP BY hour
        ORDER BY hour
    """)

    # Initialize all 24 hours with 0 tokens
    hourly_distribution = [HourlyTokenData(hour=h, tokens=0) for h in range(24)]

    # Execute query and update distribution
    # Convert datetime objects to ISO format strings for SQLite
    try:
        results = db.exec(
            hourly_query,
            {
                "user_id": user_id,
                "utc_start": utc_start.isoformat(),
                "utc_end": utc_end.isoformat()
            }
        ).fetchall()
    except Exception as e:
        logger.error(f"Hourly distribution query failed: {e}")
        results = []

    for row in results:
        hour, tokens = row
        if 0 <= hour < 24:
            hourly_distribution[hour] = HourlyTokenData(hour=hour, tokens=tokens or 0)

    return UsageOverviewResponse(
        date=target_date,
        total_requests=total_requests,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        total_tokens=total_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        hourly_distribution=hourly_distribution
    )

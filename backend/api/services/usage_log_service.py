"""
Service layer for usage log tracking and querying
"""
import json
import logging
from datetime import datetime, timedelta, timezone, date
from typing import Optional

from sqlmodel import Session, select, func, desc
from sqlalchemy import text

from api.models.usage_log import UsageLog, UsageLogStatus, UsageLogKind
from api.models.unified_api_key import UnifiedAPIKey
from api.models.subscription import Subscription
from api.models.user import User
from api.models.claw import Claw
from api.models.organization import Organization  # noqa: F401 - required for SQLModel FK resolution
from api.schemas.usage_log import (
    UsageLogList,
    UsageLogResponse,
    UsageOverviewResponse,
    QuarterHourlyTokenData,
    TrendData,
    DailyTrendData,  # Alias for backward compatibility
    UserRankingData,
    ClawRankingData,
    SystemOverviewResponse
)
from api.schemas.litellm_callback import LiteLLMSpendlogCallbackRequest
from api.utils.datetime import (
    get_timezone_offset,
    get_today_in_timezone,
    DEFAULT_TIMEZONE
)

logger = logging.getLogger(__name__)


def _extract_model_short_name(model: Optional[str]) -> str:
    """
    Extract the short name from a model identifier.

    Examples:
        "openai/Qwen/Qwen2.5-3B-Instruct" -> "Qwen2.5-3B-Instruct"
        "anthropic/claude-3-opus" -> "claude-3-opus"
        "gpt-4" -> "gpt-4"
        None -> "unknown"

    Args:
        model: Full model identifier

    Returns:
        Short model name (last part after /)
    """
    if not model:
        return "unknown"
    return model.split("/")[-1] if "/" in model else model


def create_usage_log(
    db: Session,
    user_id: int,
    callback_data: LiteLLMSpendlogCallbackRequest,
    subscription: Optional[Subscription] = None,
    client: Optional[str] = None,
    trace_id: Optional[str] = None,
    provider: Optional[str] = None
) -> Optional[UsageLog]:
    """
    Create a usage log entry from LiteLLM callback data

    Args:
        db: Database session
        user_id: User ID who made the API call
        callback_data: Parsed LiteLLM callback data
        subscription: Subscription linking to contributor (optional, not stored but used for stats)
        client: Client identifier (e.g., "Zed", "Claude-Code", "Chrome")

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

        # Calculate total duration
        total_duration = None
        if callback_data.end_time and callback_data.start_time:
            total_duration = callback_data.end_time - callback_data.start_time
        elif callback_data.response_time:
            total_duration = callback_data.response_time

        # Extract model_id
        model_id = callback_data.model_id
        if not model_id and callback_data.hidden_params:
            model_id = callback_data.hidden_params.model_id

        # Get unified_api_key_name from api_key_hash
        unified_api_key_id = None
        unified_api_key_name = None
        organization_id = None
        if callback_data.metadata and callback_data.metadata.user_api_key_hash:
            api_key_hash = callback_data.metadata.user_api_key_hash
            key_statement = select(UnifiedAPIKey).where(
                UnifiedAPIKey.api_key_hash == api_key_hash
            )
            unified_key = db.exec(key_statement).first()
            if unified_key:
                unified_api_key_id = unified_key.id
                unified_api_key_name = unified_key.api_key_name
                organization_id = unified_key.organization_id

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
            model_name=_extract_model_short_name(callback_data.model),
            provider=provider,
            status=UsageLogStatus.SUCCESS,
            kind=kind,
            client=client,
            total_duration=total_duration,
            ttft=ttft,
            input_tokens=callback_data.prompt_tokens,
            output_tokens=callback_data.completion_tokens,
            total_tokens=callback_data.total_tokens,
            request_time=datetime.fromtimestamp(callback_data.end_time, tz=timezone.utc),
            trace_id=trace_id,
            num_fails=0,
            organization_id=organization_id
        )

        db.add(usage_log)
        db.commit()
        db.refresh(usage_log)

        # Update last_used_at for the unified API key
        if unified_api_key_id:
            db.execute(
                text("UPDATE unified_api_keys SET last_used_at = :timestamp WHERE id = :key_id"),
                {"timestamp": datetime.now(timezone.utc), "key_id": unified_api_key_id}
            )
            db.commit()

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
    kind: UsageLogKind = UsageLogKind.DIRECT,
    trace_id: Optional[str] = None,
    error_details: Optional[str] = None,
    provider: Optional[str] = None,
    organization_id: Optional[int] = None
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
        trace_id: Trace ID for retry tracking (optional)
        error_details: JSON array of error details (optional)

    Returns:
        Created UsageLog record or None if creation fails
    """
    try:
        usage_log = UsageLog(
            user_id=user_id,
            unified_api_key_id=unified_api_key_id,
            unified_api_key_name=unified_api_key_name,
            model_id=model_id,
            model_name=_extract_model_short_name(model),
            provider=provider,
            status=UsageLogStatus.FAILURE,
            kind=kind,
            total_duration=None,
            ttft=None,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            request_time=datetime.now(timezone.utc),
            trace_id=trace_id,
            num_fails=1,
            error_details=error_details,
            organization_id=organization_id
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


def find_usage_log_by_trace(db: Session, user_id: int, trace_id: str) -> Optional[UsageLog]:
    """
    Find an existing usage log by user_id and trace_id

    Args:
        db: Database session
        user_id: User ID
        trace_id: Trace ID from callback

    Returns:
        UsageLog record or None if not found
    """
    try:
        statement = select(UsageLog).where(
            UsageLog.user_id == user_id,
            UsageLog.trace_id == trace_id
        )
        return db.exec(statement).first()
    except Exception as e:
        logger.error(f"Failed to find usage log by trace: {e}")
        return None


def update_usage_log_for_retry(
    db: Session,
    existing_log: UsageLog,
    callback_data: LiteLLMSpendlogCallbackRequest,
    new_status: UsageLogStatus,
    error_details_json: Optional[str] = None,
    client: Optional[str] = None,
    provider: Optional[str] = None
) -> Optional[UsageLog]:
    """
    Update an existing usage log for retry scenarios

    Merging logic:
    - Old failure + New success: Update status to success, update token fields, keep num_fails
    - Old failure + New failure: Increment num_fails, append error_details
    - Old success + New failure: Increment num_fails, update status to failure, set error_details
    - Old success + New success: Ignore (return None)

    Does NOT update request_time (keeps first callback time)

    Args:
        db: Database session
        existing_log: Existing UsageLog record
        callback_data: New callback data
        new_status: New status (success/failure)
        error_details_json: JSON array of error details (for failure callbacks)

    Returns:
        Updated UsageLog record or None (if ignored)
    """
    try:
        old_status = existing_log.status

        # Case: Old success + New success -> ignore
        if old_status == UsageLogStatus.SUCCESS and new_status == UsageLogStatus.SUCCESS:
            logger.info(f"Ignoring duplicate success callback for trace_id={existing_log.trace_id}")
            return None

        # Case: Old failure + New success -> update status and tokens, keep num_fails
        if old_status == UsageLogStatus.FAILURE and new_status == UsageLogStatus.SUCCESS:
            # Calculate TTFT
            ttft = None
            if callback_data.completion_start_time and callback_data.start_time:
                ttft = callback_data.completion_start_time - callback_data.start_time
            elif callback_data.response_time:
                ttft = callback_data.response_time

            # Calculate total duration
            total_duration = None
            if callback_data.end_time and callback_data.start_time:
                total_duration = callback_data.end_time - callback_data.start_time
            elif callback_data.response_time:
                total_duration = callback_data.response_time

            # Update status, token fields, client, duration
            db.execute(
                text("""
                    UPDATE usage_logs
                    SET status = :status,
                        model_name = :model_name,
                        provider = :provider,
                        client = :client,
                        total_duration = :total_duration,
                        ttft = :ttft,
                        input_tokens = :input_tokens,
                        output_tokens = :output_tokens,
                        total_tokens = :total_tokens
                    WHERE id = :log_id
                """),
                {
                    "status": new_status.name,
                    "model_name": _extract_model_short_name(callback_data.model),
                    "provider": provider,
                    "client": client,
                    "total_duration": total_duration,
                    "ttft": ttft,
                    "input_tokens": callback_data.prompt_tokens,
                    "output_tokens": callback_data.completion_tokens,
                    "total_tokens": callback_data.total_tokens,
                    "log_id": existing_log.id
                }
            )
            db.commit()
            db.refresh(existing_log)
            logger.info(f"Updated failure->success for trace_id={existing_log.trace_id}, num_fails={existing_log.num_fails}")
            return existing_log

        # Case: Old failure + New failure -> increment num_fails, append error_details
        if old_status == UsageLogStatus.FAILURE and new_status == UsageLogStatus.FAILURE:
            # Append new error to existing error_details array
            updated_error_details = existing_log.error_details
            if error_details_json:
                try:
                    new_errors = json.loads(error_details_json)
                    if updated_error_details:
                        # Parse existing array and append
                        existing_errors = json.loads(updated_error_details)
                        existing_errors.extend(new_errors)
                        updated_error_details = json.dumps(existing_errors)

                        # Truncate if exceeds database column limit
                        MAX_ERROR_DETAILS_LENGTH = 19000  # Leave buffer for JSON overhead
                        if len(updated_error_details) > MAX_ERROR_DETAILS_LENGTH:
                            # Middle truncation on the last error's error_str
                            last_error_str = existing_errors[-1].get("error_str", "")
                            if len(last_error_str) > 1000:
                                truncation_marker = "... [truncated] ... "
                                half = (1000 - len(truncation_marker)) // 2
                                existing_errors[-1]["error_str"] = last_error_str[:half] + truncation_marker + last_error_str[-half:]
                            else:
                                existing_errors[-1]["error_str"] = last_error_str
                            updated_error_details = json.dumps(existing_errors)
                            # If still too long, remove older errors
                            while len(updated_error_details) > MAX_ERROR_DETAILS_LENGTH and len(existing_errors) > 1:
                                existing_errors.pop(0)  # Remove oldest error
                                updated_error_details = json.dumps(existing_errors)
                    else:
                        # No existing errors, use new ones
                        updated_error_details = error_details_json
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Failed to parse error_details JSON: {e}")
                    # Keep existing error_details if parse fails
                    updated_error_details = existing_log.error_details

            db.execute(
                text("UPDATE usage_logs SET num_fails = num_fails + 1, error_details = :error_details WHERE id = :log_id"),
                {"log_id": existing_log.id, "error_details": updated_error_details}
            )
            db.commit()
            db.refresh(existing_log)
            logger.info(f"Updated failure->failure for trace_id={existing_log.trace_id}, num_fails={existing_log.num_fails}")
            return existing_log

        # Case: Old success + New failure -> increment num_fails, update status to failure, set error_details
        if old_status == UsageLogStatus.SUCCESS and new_status == UsageLogStatus.FAILURE:
            db.execute(
                text("""
                    UPDATE usage_logs
                    SET status = :status, num_fails = num_fails + 1, error_details = :error_details
                    WHERE id = :log_id
                """),
                {"status": new_status.name, "log_id": existing_log.id, "error_details": error_details_json}
            )
            db.commit()
            db.refresh(existing_log)
            logger.info(f"Updated success->failure for trace_id={existing_log.trace_id}, num_fails={existing_log.num_fails}")
            return existing_log

        return existing_log
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update usage log for retry: {e}")
        return None


def get_user_usage_logs(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[UsageLogStatus] = None,
    timezone_str: Optional[str] = None,
    unified_api_key_id: Optional[int] = None,
    organization_id: Optional[int] = None
) -> UsageLogList:
    """
    Get paginated usage logs for a user

    Args:
        db: Database session
        user_id: User ID to query
        page: Page number (1-indexed)
        page_size: Number of items per page
        start_date: Optional start date filter (user timezone)
        end_date: Optional end date filter (user timezone)
        status: Optional status filter (success/failure)
        timezone_str: Optional timezone string (e.g., "Asia/Shanghai", "UTC")
        unified_api_key_id: Optional filter by unified API key ID
        organization_id: Optional filter by organization ID (private server isolation)

    Returns:
        UsageLogList with paginated results
    """
    # Debug log
    logger.info(f"get_user_usage_logs called: user_id={user_id}, unified_api_key_id={unified_api_key_id}, organization_id={organization_id}, start_date={start_date}, end_date={end_date}")

    # Normalize timezone string
    tz_str = timezone_str or DEFAULT_TIMEZONE

    # Build base query with user filter
    query = select(UsageLog).where(UsageLog.user_id == user_id)

    # Apply filters using helper function to avoid duplication
    query = _apply_date_and_status_filters(query, start_date, end_date, status, tz_str, unified_api_key_id, organization_id)

    # Get total count using the same filters
    count_query = select(func.count()).select_from(UsageLog).where(UsageLog.user_id == user_id)
    count_query = _apply_date_and_status_filters(count_query, start_date, end_date, status, tz_str, unified_api_key_id, organization_id)
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
        items=[UsageLogResponse.model_validate(item) for item in results],
        timezone=tz_str
    )


def _apply_date_and_status_filters(query, start_date: Optional[date], end_date: Optional[date], status: Optional[UsageLogStatus], timezone_str: Optional[str] = None, unified_api_key_id: Optional[int] = None, organization_id: Optional[int] = None):
    """
    Apply date and status filters to a query (shared between count and main query)

    Args:
        query: SQLModel query to apply filters to
        start_date: Optional start date filter (user timezone)
        end_date: Optional end date filter (user timezone)
        status: Optional status filter
        timezone_str: Optional timezone string for date conversion
        unified_api_key_id: Optional filter by unified API key ID
        organization_id: Optional filter by organization ID (None = private only)

    Returns:
        Query with filters applied
    """
    # Get timezone offset
    tz_offset = get_timezone_offset(timezone_str)

    # Apply date filters if provided (convert user timezone date to UTC range)
    if start_date:
        # start_date in user timezone, convert to UTC start
        utc_start = datetime.combine(start_date, datetime.min.time()) - tz_offset
        query = query.where(UsageLog.request_time >= utc_start)

    if end_date:
        # end_date in user timezone, convert to UTC end
        utc_end = datetime.combine(end_date, datetime.max.time()) - tz_offset
        query = query.where(UsageLog.request_time <= utc_end)

    # Apply status filter
    if status:
        query = query.where(UsageLog.status == status)

    # Apply unified API key filter
    if unified_api_key_id is not None:
        logger.info(f"Applying unified_api_key_id filter: {unified_api_key_id}")
        query = query.where(UsageLog.unified_api_key_id == unified_api_key_id)

    # Apply organization filter
    # None means public only (organization_id IS NULL)
    # A specific value means that organization only
    if organization_id is not None:
        query = query.where(UsageLog.organization_id == organization_id)
    else:
        # Default: only show public records (organization_id IS NULL)
        query = query.where(UsageLog.organization_id.is_(None))

    return query


def get_user_usage_overview(
    db: Session,
    user_id: int,
    target_date: Optional[date] = None,
    timezone_str: Optional[str] = None,
    unified_api_key_id: Optional[int] = None,
    organization_id: Optional[int] = None
) -> UsageOverviewResponse:
    """
    Get usage overview for a user on a specific date (user timezone)

    Args:
        db: Database session
        user_id: User ID to query
        target_date: Date to query (user timezone), defaults to today
        timezone_str: Optional timezone string for date conversion
        unified_api_key_id: Optional filter by unified API key ID
        organization_id: Optional filter by organization ID (private server isolation)

    Returns:
        UsageOverviewResponse with aggregated data
    """
    # Normalize timezone string
    tz_str = timezone_str or DEFAULT_TIMEZONE

    # Default to today in the specified timezone
    if target_date is None:
        target_date = get_today_in_timezone(tz_str)

    # Get timezone offset
    tz_offset = get_timezone_offset(tz_str)

    # Convert target_date (user timezone) to UTC range
    utc_start = datetime.combine(target_date, datetime.min.time()) - tz_offset
    utc_end = datetime.combine(target_date, datetime.max.time()) - tz_offset

    # Build base filters
    base_filters = [
        UsageLog.user_id == user_id,
        UsageLog.request_time >= utc_start,
        UsageLog.request_time <= utc_end
    ]

    # Add unified API key filter if provided
    if unified_api_key_id is not None:
        base_filters.append(UsageLog.unified_api_key_id == unified_api_key_id)

    # Add organization filter
    if organization_id is not None:
        base_filters.append(UsageLog.organization_id == organization_id)
    else:
        # Default: only show public records (organization_id IS NULL)
        base_filters.append(UsageLog.organization_id.is_(None))

    # Get total requests
    total_query = select(func.count()).select_from(UsageLog).where(*base_filters)
    total_requests = db.exec(total_query).one()

    # Get successful requests
    success_filters = base_filters + [UsageLog.status == UsageLogStatus.SUCCESS]
    success_query = select(func.count()).select_from(UsageLog).where(*success_filters)
    successful_requests = db.exec(success_query).one()

    # Failed requests
    failed_requests = total_requests - successful_requests

    # Get token totals
    token_query = select(
        func.sum(UsageLog.input_tokens),
        func.sum(UsageLog.output_tokens),
        func.sum(UsageLog.total_tokens)
    ).where(*base_filters)
    result = db.exec(token_query).one()
    input_tokens = result[0] or 0
    output_tokens = result[1] or 0
    total_tokens = result[2] or 0

    # Get 96 quarter-hour distribution (15-minute intervals)
    # Calculate timezone offset in hours for PostgreSQL date conversion
    tz_offset_hours = int(tz_offset.total_seconds() / 3600)

    # Build WHERE clause for unified_api_key_id and organization_id filters
    key_filter = "AND unified_api_key_id = :key_id" if unified_api_key_id is not None else ""
    org_filter = "AND organization_id = :org_id" if organization_id is not None else ""

    # Build WHERE clause for organization_id filter
    if organization_id is not None:
        org_filter = "AND organization_id = :org_id"
    else:
        org_filter = "AND organization_id IS NULL"

    # Check database type to use appropriate SQL syntax
    # PostgreSQL uses EXTRACT(EPOCH FROM ...), SQLite uses strftime
    db_url = str(db.get_bind().url)
    is_sqlite = db_url.startswith("sqlite")

    if is_sqlite:
        # SQLite compatible query - calculate quarter_hour using strftime
        # Convert UTC time to local timezone by adding offset hours
        # strftime('%s', ...) gives seconds since epoch, then calculate quarter_hour
        quarter_hourly_query = text(f"""
            SELECT CAST(((strftime('%%s', datetime(request_time, '+{tz_offset_hours} hours')) %% 86400) / 900) AS INTEGER) AS quarter_hour,
                   SUM(total_tokens) as tokens
            FROM usage_logs
            WHERE user_id = :user_id
              AND request_time >= :utc_start
              AND request_time <= :utc_end
              {key_filter}
              {org_filter}
            GROUP BY quarter_hour
            ORDER BY quarter_hour
        """)
    else:
        # PostgreSQL query
        quarter_hourly_query = text(f"""
            SELECT FLOOR(EXTRACT(EPOCH FROM (request_time AT TIME ZONE 'UTC' + INTERVAL '1 hour' * :offset)) % 86400 / 900)::int AS quarter_hour,
                   SUM(total_tokens) as tokens
            FROM usage_logs
            WHERE user_id = :user_id
              AND request_time >= :utc_start
              AND request_time <= :utc_end
              {key_filter}
              {org_filter}
            GROUP BY quarter_hour
            ORDER BY quarter_hour
        """)

    # Initialize all 96 quarter-hours with 0 tokens
    quarter_hourly_distribution = [QuarterHourlyTokenData(quarter_hour=q, tokens=0) for q in range(96)]

    # Execute query and update distribution
    query_params = {
        "user_id": user_id,
        "utc_start": utc_start,
        "utc_end": utc_end,
        "offset": tz_offset_hours
    }
    if unified_api_key_id is not None:
        query_params["key_id"] = unified_api_key_id
    if organization_id is not None:
        query_params["org_id"] = organization_id

    try:
        results = db.execute(quarter_hourly_query, query_params).fetchall()
    except Exception as e:
        logger.error(f"Quarter-hourly distribution query failed: {e}")
        results = []

    for row in results:
        quarter_hour, tokens = row
        if 0 <= quarter_hour < 96:
            quarter_hourly_distribution[quarter_hour] = QuarterHourlyTokenData(quarter_hour=quarter_hour, tokens=tokens or 0)

    return UsageOverviewResponse(
        date=target_date,
        total_requests=total_requests,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        total_tokens=total_tokens,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        quarter_hourly_distribution=quarter_hourly_distribution,
        timezone=tz_str
    )


def get_system_overview(
    db: Session,
    days: int = 7,
    organization_id: Optional[int] = None
) -> SystemOverviewResponse:
    """
    Get system-wide usage overview statistics

    Args:
        db: Database session
        days: Number of days to include for trend data (default: 7)
        organization_id: Optional organization ID for filtering (default: None)

    Returns:
        SystemOverviewResponse with aggregated system statistics
    """
    # Get total tokens across all time
    total_tokens_query = select(func.sum(UsageLog.total_tokens))
    if organization_id is not None:
        total_tokens_query = total_tokens_query.where(UsageLog.organization_id == organization_id)
    else:
        total_tokens_query = total_tokens_query.where(UsageLog.organization_id.is_(None))
    total_tokens = db.exec(total_tokens_query).one() or 0

    # Get today's tokens (UTC date)
    today_utc = datetime.now(timezone.utc).date()
    utc_start = datetime.combine(today_utc, datetime.min.time()).replace(tzinfo=timezone.utc)
    utc_end = datetime.combine(today_utc, datetime.max.time()).replace(tzinfo=timezone.utc)

    today_tokens_query = select(func.sum(UsageLog.total_tokens)).where(
        UsageLog.request_time >= utc_start,
        UsageLog.request_time <= utc_end
    )
    if organization_id is not None:
        today_tokens_query = today_tokens_query.where(UsageLog.organization_id == organization_id)
    else:
        today_tokens_query = today_tokens_query.where(UsageLog.organization_id.is_(None))
    today_tokens = db.exec(today_tokens_query).one() or 0

    # Get user count (exclude soft-deleted users)
    if organization_id is not None:
        # For organization scope, count organization members
        from api.models.organization_member import OrganizationMember
        user_count_query = select(func.count()).select_from(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id
        )
    else:
        # For system scope, count all users
        user_count_query = select(func.count()).select_from(User).where(User.deleted_at.is_(None))
    user_count = db.exec(user_count_query).one()

    # Get claw count (all claws regardless of status)
    claw_count_query = select(func.count()).select_from(Claw)
    if organization_id is not None:
        # For organization scope, count claws with unified_api_key belonging to the org
        claw_count_query = claw_count_query.join(UnifiedAPIKey, Claw.unified_api_key_id == UnifiedAPIKey.id).where(
            UnifiedAPIKey.organization_id == organization_id
        )
    else:
        # For system scope, count claws without organization (public claws)
        claw_count_query = claw_count_query.join(UnifiedAPIKey, Claw.unified_api_key_id == UnifiedAPIKey.id).where(
            UnifiedAPIKey.organization_id.is_(None)
        )
    claw_count = db.exec(claw_count_query).one()

    # Get trend data with 96 data points, granularity depends on days parameter
    utc_start_trends = datetime.now(timezone.utc) - timedelta(days=days)

    # Calculate granularity: total hours / 96 data points
    total_hours = days * 24
    minutes_per_slot = int((total_hours * 60) / 96)  # Convert to minutes

    # Check database type
    db_url = str(db.get_bind().url)
    is_sqlite = db_url.startswith("sqlite")

    # Initialize 96 data points with 0 tokens
    trends_data = [TrendData(time_slot=i, total_tokens=0) for i in range(96)]

    if is_sqlite:
        # SQLite compatible query
        org_filter = "AND organization_id = :org_id" if organization_id is not None else "AND organization_id IS NULL"
        trends_query = text(f"""
            SELECT CAST(((strftime('%%s', request_time) - strftime('%%s', :start_time)) / {minutes_per_slot * 60}) AS INTEGER) AS time_slot,
                   SUM(total_tokens) AS tokens
            FROM usage_logs
            WHERE request_time >= :start_date
            {org_filter}
            GROUP BY time_slot
            ORDER BY time_slot
        """)
    else:
        # PostgreSQL query
        org_filter = "AND organization_id = :org_id" if organization_id is not None else "AND organization_id IS NULL"
        trends_query = text(f"""
            SELECT FLOOR(EXTRACT(EPOCH FROM (request_time - :start_time)) / {minutes_per_slot * 60})::int AS time_slot,
                   SUM(total_tokens) AS tokens
            FROM usage_logs
            WHERE request_time >= :start_date
            {org_filter}
            GROUP BY time_slot
            ORDER BY time_slot
        """)

    try:
        query_params = {"start_date": utc_start_trends, "start_time": utc_start_trends}
        if organization_id is not None:
            query_params["org_id"] = organization_id
        trends_result = db.execute(
            trends_query,
            query_params
        ).fetchall()

        # Fill in the actual data (limit to 96 slots)
        for row in trends_result:
            time_slot, tokens = row
            if 0 <= time_slot < 96:
                trends_data[time_slot] = TrendData(time_slot=time_slot, total_tokens=tokens or 0)
    except Exception as e:
        logger.error(f"Trends data query failed: {e}")

    # Use alias for backward compatibility
    daily_trends = trends_data

    # Get top 10 users by token consumption (all time)
    if organization_id is not None:
        user_rankings_query = text("""
            SELECT u.id as user_id,
                   u.name,
                   u.email,
                   SUM(ul.total_tokens) AS tokens
            FROM usage_logs ul
            JOIN users u ON ul.user_id = u.id
            WHERE u.deleted_at IS NULL AND ul.organization_id = :org_id
            GROUP BY u.id, u.name, u.email
            ORDER BY tokens DESC
            LIMIT 10
        """)
        user_rankings_result = db.execute(user_rankings_query, {"org_id": organization_id}).fetchall()
    else:
        user_rankings_query = text("""
            SELECT u.id as user_id,
                   u.name,
                   u.email,
                   SUM(ul.total_tokens) AS tokens
            FROM usage_logs ul
            JOIN users u ON ul.user_id = u.id
            WHERE u.deleted_at IS NULL AND ul.organization_id IS NULL
            GROUP BY u.id, u.name, u.email
            ORDER BY tokens DESC
            LIMIT 10
        """)
        user_rankings_result = db.execute(user_rankings_query).fetchall()

    user_rankings = [
        UserRankingData(
            user_id=row[0],
            user_name=row[1] or row[2].split('@')[0],  # Use name or email prefix
            consumed_tokens=row[3] or 0
        )
        for row in user_rankings_result
    ]

    # Get top 10 claws by token consumption (all time)
    if organization_id is not None:
        claw_rankings_query = text("""
            SELECT c.id as claw_id,
                   c.name as claw_name,
                   u.name as user_name,
                   SUM(ul.total_tokens) AS tokens
            FROM usage_logs ul
            JOIN claws c ON ul.unified_api_key_id = c.unified_api_key_id
            JOIN unified_api_keys uak ON ul.unified_api_key_id = uak.id
            JOIN users u ON c.user_id = u.id
            WHERE c.unified_api_key_id IS NOT NULL AND uak.organization_id = :org_id
            GROUP BY c.id, c.name, u.name
            ORDER BY tokens DESC
            LIMIT 10
        """)
        claw_rankings_result = db.execute(claw_rankings_query, {"org_id": organization_id}).fetchall()
    else:
        claw_rankings_query = text("""
            SELECT c.id as claw_id,
                   c.name as claw_name,
                   u.name as user_name,
                   SUM(ul.total_tokens) AS tokens
            FROM usage_logs ul
            JOIN claws c ON ul.unified_api_key_id = c.unified_api_key_id
            JOIN unified_api_keys uak ON ul.unified_api_key_id = uak.id
            JOIN users u ON c.user_id = u.id
            WHERE c.unified_api_key_id IS NOT NULL AND uak.organization_id IS NULL
            GROUP BY c.id, c.name, u.name
            ORDER BY tokens DESC
            LIMIT 10
        """)
        claw_rankings_result = db.execute(claw_rankings_query).fetchall()

    claw_rankings = [
        ClawRankingData(
            claw_id=row[0],
            claw_name=row[1],
            user_name=row[2],
            consumed_tokens=row[3] or 0
        )
        for row in claw_rankings_result
    ]

    return SystemOverviewResponse(
        total_tokens=total_tokens,
        today_tokens=today_tokens,
        user_count=user_count,
        claw_count=claw_count,
        daily_trends=daily_trends,
        user_rankings=user_rankings,
        claw_rankings=claw_rankings
    )

"""
Service layer for operation log tracking and querying
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlmodel import Session, select, func, desc
from sqlalchemy import or_

from api.models.operation_log import OperationLog, OperationType, ResourceType
from api.models.user import User
from api.schemas.operation_log import OperationLogDetailList, OperationLogDetail

logger = logging.getLogger(__name__)


def create_operation_log(
    user_id: int,
    operation_type: OperationType,
    resource_type: ResourceType,
    resource_id: int,
    resource_name: Optional[str] = None
) -> Optional[OperationLog]:
    """
    Create an operation log entry.

    Uses a separate database session to ensure audit logs are written
    independently of the main business transaction.

    Args:
        user_id: ID of the user who performed the operation
        operation_type: Type of operation performed
        resource_type: Type of resource affected
        resource_id: ID of the affected resource
        resource_name: Name of the affected resource (persisted for audit trail)

    Returns:
        Created OperationLog object or None if failed
    """
    try:
        # Use a separate session for logging to ensure audit logs
        # are written even if the main business transaction fails.
        # This prevents the "operation logged but didn't happen" problem.
        from api.database import engine
        from sqlmodel import Session

        with Session(engine) as log_session:
            log_entry = OperationLog(
                user_id=user_id,
                operation_type=operation_type,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name
            )
            log_session.add(log_entry)
            log_session.commit()
            log_session.refresh(log_entry)
            return log_entry
    except Exception as e:
        logger.error(f"Failed to create operation log: {e}")
        return None


def _apply_filters(
    query,
    user_id: Optional[int] = None,
    operation_type: Optional[OperationType] = None,
    resource_type: Optional[ResourceType] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    search: Optional[str] = None
):
    """
    Apply filters to operation log query.

    Args:
        query: SQLModel select query
        user_id: Filter by user ID
        operation_type: Filter by operation type
        resource_type: Filter by resource type
        start_time: Filter by start time (inclusive)
        end_time: Filter by end time (inclusive)
        search: Search in user email, user name, and resource name

    Returns:
        Filtered query
    """
    if user_id is not None:
        query = query.where(OperationLog.user_id == user_id)
    if operation_type is not None:
        query = query.where(OperationLog.operation_type == operation_type)
    if resource_type is not None:
        query = query.where(OperationLog.resource_type == resource_type)
    if start_time is not None:
        query = query.where(OperationLog.created_at >= start_time)
    if end_time is not None:
        query = query.where(OperationLog.created_at <= end_time)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(search_pattern),
                User.name.ilike(search_pattern),
                OperationLog.resource_name.ilike(search_pattern)
            )
        )
    return query


def get_operation_logs_count(
    db: Session,
    user_id: Optional[int] = None,
    operation_type: Optional[OperationType] = None,
    resource_type: Optional[ResourceType] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    search: Optional[str] = None
) -> int:
    """
    Get count of operation logs matching filters.

    Args:
        db: Database session
        user_id: Filter by user ID
        operation_type: Filter by operation type
        resource_type: Filter by resource type
        start_time: Filter by start time (inclusive)
        end_time: Filter by end time (inclusive)
        search: Search in user email, user name, and resource name

    Returns:
        Count of matching logs
    """
    query = select(func.count(OperationLog.id)).join(User, OperationLog.user_id == User.id)
    query = _apply_filters(query, user_id, operation_type, resource_type, start_time, end_time, search)
    result = db.exec(query).one()
    return result


def get_operation_logs_with_details(
    db: Session,
    offset: int = 0,
    limit: int = 20,
    user_id: Optional[int] = None,
    operation_type: Optional[OperationType] = None,
    resource_type: Optional[ResourceType] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> OperationLogDetailList:
    """
    Get operation logs with user details (email and name).

    Args:
        db: Database session
        offset: Number of logs to skip (for pagination)
        limit: Maximum number of logs to return
        user_id: Filter by user ID
        operation_type: Filter by operation type
        resource_type: Filter by resource type
        start_time: Filter by start time (inclusive)
        end_time: Filter by end time (inclusive)
        search: Search in user email, user name, and resource name
        sort_by: Field to sort by (created_at, operation_type, resource_type)
        sort_order: Sort order (asc, desc)

    Returns:
        Paginated list of operation logs with user and resource details
    """
    # Get total count
    total = get_operation_logs_count(db, user_id, operation_type, resource_type, start_time, end_time, search)

    # Build query with user join
    query = select(OperationLog, User).join(User, OperationLog.user_id == User.id)

    # Apply filters
    query = _apply_filters(query, user_id, operation_type, resource_type, start_time, end_time, search)

    # Apply sorting
    sort_column = OperationLog.created_at  # default
    if sort_by == "operation_type":
        sort_column = OperationLog.operation_type
    elif sort_by == "resource_type":
        sort_column = OperationLog.resource_type

    if sort_order == "asc":
        query = query.order_by(sort_column)
    else:
        query = query.order_by(desc(sort_column))

    query = query.offset(offset).limit(limit)

    results = db.exec(query).all()

    # Build response items (resource_name is now stored in the log)
    items = []
    for log, user in results:
        items.append(OperationLogDetail(
            id=log.id,
            user_id=log.user_id,
            user_email=user.email if user else None,
            user_name=user.name if user else None,
            operation_type=log.operation_type,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            resource_name=log.resource_name,
            created_at=log.created_at
        ))

    page = offset // limit + 1 if limit > 0 else 1
    return OperationLogDetailList(
        total=total,
        page=page,
        page_size=limit,
        items=items
    )

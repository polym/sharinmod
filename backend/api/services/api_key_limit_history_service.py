"""
Service layer for API key limit history
"""
from sqlmodel import Session, select
from typing import List

from api.models.api_key_limit_history import APIKeyLimitHistory


def create_limit_history_entry(
    session: Session,
    unified_api_key_id: int,
    action: str,
    tokens_used: int = 0,
    token_limit: int = 0,
    reason: str = None
) -> APIKeyLimitHistory:
    """
    Create a limit history entry

    Args:
        session: Database session
        unified_api_key_id: ID of the unified API key
        action: Action type ('disable' or 'enable')
        tokens_used: Current tokens used at time of action
        token_limit: Token limit at time of action
        reason: Optional reason for the action

    Returns:
        Created APIKeyLimitHistory object
    """
    history_entry = APIKeyLimitHistory(
        unified_api_key_id=unified_api_key_id,
        action=action,
        tokens_used=tokens_used,
        token_limit=token_limit,
        reason=reason
    )

    session.add(history_entry)
    session.commit()
    session.refresh(history_entry)

    return history_entry


def get_limit_history(
    session: Session,
    unified_api_key_id: int,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[APIKeyLimitHistory], int]:
    """
    Get limit history for a specific API key with pagination

    Args:
        session: Database session
        unified_api_key_id: ID of the unified API key
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Tuple of (history list, total count)
    """
    # Get total count
    count_statement = select(APIKeyLimitHistory).where(
        APIKeyLimitHistory.unified_api_key_id == unified_api_key_id
    )
    total = len(session.exec(count_statement).all())

    # Get paginated results
    offset = (page - 1) * page_size
    statement = (
        select(APIKeyLimitHistory)
        .where(APIKeyLimitHistory.unified_api_key_id == unified_api_key_id)
        .order_by(APIKeyLimitHistory.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    results = session.exec(statement).all()
    return results, total


def get_all_limit_history(
    session: Session,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[APIKeyLimitHistory], int]:
    """
    Get all limit history with pagination

    Args:
        session: Database session
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Tuple of (history list, total count)
    """
    # Get total count
    total_statement = select(APIKeyLimitHistory)
    total = len(session.exec(total_statement).all())

    # Get paginated results
    offset = (page - 1) * page_size
    statement = (
        select(APIKeyLimitHistory)
        .order_by(APIKeyLimitHistory.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    results = session.exec(statement).all()
    return results, total

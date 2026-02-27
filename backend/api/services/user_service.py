"""
User service layer for business logic
"""
from sqlmodel import Session, select, func
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
from api.models.user import User
from api.models.subscription import Subscription
from api.models.shared_api_key import SharedAPIKey, APIKeyStatus
from api.models.usage_log import UsageLog
from api.schemas.user import UserProfileUpdate


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Get user by email address
    
    Args:
        db: Database session
        email: Email address to search for
        
    Returns:
        User object if found, None otherwise
    """
    statement = select(User).where(User.email == email)
    return db.exec(statement).first()

def update_user_profile(db: Session, user: User, profile_data: UserProfileUpdate) -> User:
    """
    Update user profile with partial data
    
    Args:
        db: Database session
        user: User object to update
        profile_data: Profile update data (only provided fields will be updated)
        
    Returns:
        Updated user object
    """
    # Update only provided fields (PATCH semantics)
    update_data = profile_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    # Update timestamp
    user.updated_at = datetime.utcnow()
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_profile(user: User) -> User:
    """
    Get user profile (simple pass-through, but allows for future expansion)

    Args:
        user: User object

    Returns:
        User object with profile data
    """
    return user


def get_all_users(
    db: Session,
    offset: int = 0,
    limit: int = 20,
    role_filter: Optional[str] = None
) -> Tuple[list[User], int, Dict[int, Dict[str, Any]]]:
    """
    Get all users with statistics (admin only)

    Supports:
    - Pagination via offset/limit
    - Role filtering (all/admin/user)
    - Aggregation statistics (subscription_count, last_used_at)

    Args:
        db: Database session
        offset: Number of users to skip (for pagination)
        limit: Maximum number of users to return
        role_filter: Filter by role ('all', 'admin', 'user')

    Returns:
        Tuple of (list of User objects, total count, stats dict per user_id)
    """
    # Build base query for users
    base_query = select(User)

    # Apply role filter
    if role_filter == 'admin':
        base_query = base_query.where(User.is_admin == True)
    elif role_filter == 'user':
        base_query = base_query.where(User.is_admin == False)

    # Order by created_at descending
    base_query = base_query.order_by(User.created_at.desc())

    # Get total count (before pagination)
    count_query = select(func.count()).select_from(User)
    if role_filter == 'admin':
        count_query = count_query.where(User.is_admin == True)
    elif role_filter == 'user':
        count_query = count_query.where(User.is_admin == False)
    total = db.exec(count_query).one()

    # Get paginated results
    paginated_query = base_query.offset(offset).limit(limit)
    users = db.exec(paginated_query).all()

    # Build stats map for user statistics
    user_ids = [u.id for u in users]
    stats_map: Dict[int, Dict[str, Any]] = {uid: {} for uid in user_ids}

    if user_ids:
        # Get SharedAPIKey counts (total) per user
        key_counts = db.exec(
            select(SharedAPIKey.user_id, func.count(SharedAPIKey.id).label('cnt'))
            .where(SharedAPIKey.user_id.in_(user_ids))
            .group_by(SharedAPIKey.user_id)
        ).all()
        for user_id, cnt in key_counts:
            stats_map[user_id]['subscription_count'] = cnt

        # Get SharedAPIKey counts (ACTIVE only) per user
        active_key_counts = db.exec(
            select(SharedAPIKey.user_id, func.count(SharedAPIKey.id).label('cnt'))
            .where(SharedAPIKey.user_id.in_(user_ids))
            .where(SharedAPIKey.status == APIKeyStatus.ACTIVE)
            .group_by(SharedAPIKey.user_id)
        ).all()
        for user_id, cnt in active_key_counts:
            stats_map[user_id]['active_subscription_count'] = cnt

        # Get last used times
        last_used = db.exec(
            select(UsageLog.user_id, func.max(UsageLog.request_time).label('max_time'))
            .where(UsageLog.user_id.in_(user_ids))
            .group_by(UsageLog.user_id)
        ).all()
        for user_id, max_time in last_used:
            stats_map[user_id]['last_used_at'] = max_time

    return users, total, stats_map


def grant_admin_privilege(db: Session, user_id: int) -> User | None:
    """
    Grant admin privileges to a user

    Args:
        db: Database session
        user_id: ID of the user to grant admin privileges

    Returns:
        Updated User object, or None if user not found
    """
    user = db.get(User, user_id)
    if user:
        user.is_admin = True
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def revoke_admin_privilege(db: Session, user_id: int) -> User | None:
    """
    Revoke admin privileges from a user

    Args:
        db: Database session
        user_id: ID of the user to revoke admin privileges

    Returns:
        Updated User object, or None if user not found
    """
    user = db.get(User, user_id)
    if user:
        user.is_admin = False
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
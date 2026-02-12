"""
User service layer for business logic
"""
from sqlmodel import Session, select
from datetime import datetime
from api.models.user import User
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


def get_all_users(db: Session, offset: int = 0, limit: int = 100) -> list[User]:
    """
    Get all users (admin only)

    Args:
        db: Database session
        offset: Number of users to skip (for pagination)
        limit: Maximum number of users to return

    Returns:
        List of User objects
    """
    statement = select(User).offset(offset).limit(limit)
    return list(db.exec(statement).all())


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
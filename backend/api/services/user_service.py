"""
User service layer for business logic
"""
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from api.models.user import User
from api.schemas.user import UserCreate, UserProfileUpdate
from api.utils.security import hash_password


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create a new user with hashed password
    
    Args:
        db: Database session
        user_data: User registration data
        
    Returns:
        Created user object
        
    Raises:
        ValueError: If email is already registered
    """
    # Hash the password before storing
    hashed_password = hash_password(user_data.password)
    
    # Create user instance
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    # Add to database
    db.add(db_user)
    
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError("Email already registered")


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
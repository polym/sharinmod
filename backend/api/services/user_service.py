"""
User service layer for business logic
"""
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from api.models.user import User
from api.schemas.user import UserCreate
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

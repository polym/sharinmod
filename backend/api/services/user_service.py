"""
User service layer for business logic
"""
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import httpx
from api.models.user import User
from api.schemas.user import UserCreate, UserProfileUpdate
from api.utils.security import hash_password
from api.config import settings


async def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create a new user with hashed password and LiteLLM integration
    
    Args:
        db: Database session
        user_data: User registration data
        
    Returns:
        Created user object
        
    Raises:
        ValueError: If email is already registered or LiteLLM creation fails
    """
    # Hash the password before storing
    hashed_password = hash_password(user_data.password)
    
    # Create user instance
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    # First, create user in LiteLLM (skip in testing)
    if not settings.TESTING:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{settings.LITELLM_BASE_URL}/user/new",
                    json={"user_id": user_data.email},
                    headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                )
                response.raise_for_status()
                litellm_data = response.json()
                litellm_user_id = litellm_data["user_id"]
        except Exception as e:
            raise ValueError(f"Failed to create user in LiteLLM: {str(e)}")
    else:
        litellm_user_id = user_data.email
    
    # Set the LiteLLM user ID
    db_user.litellm_user_id = litellm_user_id
    
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
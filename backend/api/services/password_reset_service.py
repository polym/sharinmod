"""
Password reset service layer for business logic
"""
from sqlmodel import Session, select
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from api.models.user import User
from api.models.password_reset_token import PasswordResetToken
from api.utils.security import hash_password
from api.utils.token_generator import generate_unified_token
from api.services.oauth_service import create_user_in_litellm


# Token validity period: 24 hours
TOKEN_EXPIRY_HOURS = 24


def _utcnow() -> datetime:
    """Get current UTC time as timezone-aware datetime (for database compatibility)"""
    return datetime.now(timezone.utc)


def create_reset_token(db: Session, user: User) -> PasswordResetToken:
    """
    Create a password reset token for a user

    Args:
        db: Database session
        user: User object to create token for

    Returns:
        PasswordResetToken object
    """
    token = generate_unified_token()
    expires_at = _utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)

    reset_token = PasswordResetToken(
        token=token,
        user_id=user.id,
        expires_at=expires_at,
        is_used=False
    )

    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)
    return reset_token


def verify_reset_token(db: Session, token: str) -> Tuple[bool, Optional[User], Optional[str]]:
    """
    Verify a password reset token

    Args:
        db: Database session
        token: Reset token to verify

    Returns:
        Tuple of (is_valid, user_object, error_message)
        - is_valid: True if token is valid
        - user_object: User object if valid, None otherwise
        - error_message: Error message if invalid, None otherwise
    """
    # Find token in database
    statement = select(PasswordResetToken).where(PasswordResetToken.token == token)
    reset_token = db.exec(statement).first()

    if not reset_token:
        return False, None, "令牌不存在"

    # Check if token has been used
    if reset_token.is_used:
        return False, None, "令牌已使用"

    # Check if token has expired
    if reset_token.expires_at < _utcnow():
        return False, None, "令牌已过期"

    # Get user
    user = db.get(User, reset_token.user_id)
    if not user:
        return False, None, "用户不存在"

    return True, user, None


def set_password_by_token(db: Session, token: str, new_password: str) -> Tuple[bool, Optional[User], Optional[str]]:
    """
    Set new password using reset token

    Args:
        db: Database session
        token: Reset token
        new_password: New plain text password

    Returns:
        Tuple of (success, user_object, error_message)
        - success: True if password was set successfully
        - user_object: Updated User object if successful, None otherwise
        - error_message: Error message if failed, None otherwise
    """
    # Verify token first
    is_valid, user, error_msg = verify_reset_token(db, token)
    if not is_valid:
        return False, None, error_msg

    # Set new password
    user.hashed_password = hash_password(new_password)
    user.force_password_change = False
    user.updated_at = _utcnow()

    # Mark token as used
    statement = select(PasswordResetToken).where(PasswordResetToken.token == token)
    reset_token = db.exec(statement).first()
    if reset_token:
        reset_token.is_used = True
        db.add(reset_token)

    db.add(user)
    db.commit()
    db.refresh(user)
    return True, user, None


async def create_user_with_reset_token(db: Session, email: str) -> Tuple[bool, Optional[PasswordResetToken], Optional[str]]:
    """
    Create a new user with force_password_change=True and generate reset token

    Args:
        db: Database session
        email: User email address

    Returns:
        Tuple of (success, reset_token_object, error_message)
        - success: True if user was created successfully
        - reset_token_object: PasswordResetToken object if successful, None otherwise
        - error_message: Error message if failed, None otherwise
    """
    # Check if user already exists
    existing_user = select(User).where(User.email == email)
    if db.exec(existing_user).first():
        return False, None, "邮箱已存在"

    # Extract username from email (part before @)
    username = email.split('@')[0]

    # Create user with no password (will be set via token)
    user = User(
        email=email,
        name=username,
        hashed_password=None,
        force_password_change=True
    )

    # Sync user to LiteLLM
    try:
        litellm_user_id = await create_user_in_litellm(email)
        user.litellm_user_id = litellm_user_id
    except Exception as e:
        return False, None, f"创建用户失败（LiteLLM 服务异常）: {str(e)}"

    db.add(user)
    db.commit()
    db.refresh(user)

    # Auto-create personal organization for the new admin-created user
    from api.services.organization_service import create_personal_organization
    create_personal_organization(db, user)

    # Create reset token
    reset_token = create_reset_token(db, user)
    return True, reset_token, None


def reset_user_password(db: Session, user_id: int) -> Tuple[bool, Optional[PasswordResetToken], Optional[str]]:
    """
    Reset user password by clearing hashed_password and generating new reset token

    Args:
        db: Database session
        user_id: ID of the user to reset password for

    Returns:
        Tuple of (success, reset_token_object, error_message)
        - success: True if password was reset successfully
        - reset_token_object: PasswordResetToken object if successful, None otherwise
        - error_message: Error message if failed, None otherwise
    """
    # Get user
    user = db.get(User, user_id)
    if not user:
        return False, None, "用户不存在"

    # Clear password and set force_password_change flag
    user.hashed_password = None
    user.force_password_change = True
    user.updated_at = _utcnow()

    db.add(user)
    db.commit()

    # Create reset token
    reset_token = create_reset_token(db, user)
    return True, reset_token, None


def generate_reset_link(token: str, base_url: str) -> str:
    """
    Generate reset password link with token

    Args:
        token: Reset token
        base_url: Base URL for the application (e.g., http://localhost:28888)

    Returns:
        Full reset password URL with token parameter
    """
    return f"{base_url}/reset-password?token={token}"

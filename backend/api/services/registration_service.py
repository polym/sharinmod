"""
Registration service: invite-code validation, user creation, email verification
"""
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlmodel import Session, select

from api.models.invitation_code import InvitationCode
from api.models.email_verification_token import EmailVerificationToken
from api.models.user import User
from api.utils.security import hash_password
from api.utils.token_generator import generate_unified_token
from api.services.oauth_service import create_user_in_litellm
from api.services.organization_service import create_personal_organization

logger = logging.getLogger(__name__)

TOKEN_EXPIRY_HOURS = 24


def generate_invitation_code() -> str:
    """Generate an 8-char uppercase hex code (e.g. A3F8C91D)."""
    return secrets.token_hex(4).upper()


def create_invitation_code(db: Session, created_by_user_id: Optional[int] = None) -> InvitationCode:
    """Create and persist a new invitation code."""
    code = InvitationCode(
        code=generate_invitation_code(),
        created_by_user_id=created_by_user_id,
    )
    db.add(code)
    db.commit()
    db.refresh(code)
    return code


def validate_invitation_code(
    db: Session, code: str
) -> Tuple[bool, Optional[InvitationCode], Optional[str]]:
    """
    Check if the invite code exists and has not been used.

    Returns:
        (valid, invite_obj, error_message)
    """
    # Normalise to uppercase to be forgiving of user input
    normalised = code.strip().upper()
    stmt = select(InvitationCode).where(InvitationCode.code == normalised)
    invite = db.exec(stmt).first()

    if not invite:
        return False, None, "邀请码不存在或已失效"
    if invite.used_by_user_id is not None:
        return False, None, "邀请码已被使用"
    return True, invite, None


def create_email_verification_token(db: Session, user: User) -> EmailVerificationToken:
    """Create and persist an email verification token for the given user."""
    token = EmailVerificationToken(
        token=generate_unified_token(),
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS),
        is_used=False,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


async def register_user(
    db: Session, email: str, password: str, invitation_code: str
) -> Tuple[bool, Optional[EmailVerificationToken], Optional[str]]:
    """
    Full registration flow:
      1. Validate invite code (without consuming it yet)
      2. Check email is not already registered
      3. Create user with email_verified=False
      4. Mark invite code as used
      5. Create and return email verification token

    Returns:
        (success, verification_token, error_message)
    """
    # 1. Validate invite code
    valid, invite, error = validate_invitation_code(db, invitation_code)
    if not valid:
        return False, None, error

    # 2. Check email uniqueness before consuming the code (AC 8)
    existing = db.exec(select(User).where(User.email == email)).first()
    if existing:
        return False, None, "该邮箱已被注册"

    # 3. Create user
    username = email.split("@")[0]
    user = User(
        email=email,
        name=username,
        hashed_password=hash_password(password),
        email_verified=False,
    )

    # Sync to LiteLLM (non-blocking on error)
    try:
        litellm_user_id = await create_user_in_litellm(email)
        user.litellm_user_id = litellm_user_id
    except Exception as exc:
        logger.warning("[Registration] LiteLLM sync failed for %s: %s", email, exc)

    db.add(user)
    db.commit()
    db.refresh(user)

    # 4. Consume invite code
    invite.used_by_user_id = user.id
    invite.used_at = datetime.now(timezone.utc)
    db.add(invite)
    db.commit()

    # Auto-create personal organization for the new user (non-blocking on error)
    try:
        create_personal_organization(db, user)
    except Exception as exc:
        logger.warning("[Registration] Failed to create personal org for user %s: %s", user.id, exc)

    # 5. Create verification token
    token = create_email_verification_token(db, user)
    return True, token, None


def verify_email_token(
    db: Session, token: str
) -> Tuple[bool, Optional[User], Optional[str]]:
    """
    Verify the email token and mark the user's email as verified.

    Returns:
        (success, user, error_message)
    """
    stmt = select(EmailVerificationToken).where(EmailVerificationToken.token == token)
    verification = db.exec(stmt).first()

    if not verification:
        return False, None, "令牌不存在"
    if verification.is_used:
        return False, None, "令牌已使用"
    if verification.expires_at < datetime.now(timezone.utc):
        return False, None, "令牌已过期"

    user = db.get(User, verification.user_id)
    if not user:
        return False, None, "用户不存在"

    # Mark email as verified and token as consumed
    user.email_verified = True
    verification.is_used = True
    db.add(user)
    db.add(verification)
    db.commit()
    db.refresh(user)
    return True, user, None

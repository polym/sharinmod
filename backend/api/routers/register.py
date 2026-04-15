"""
Registration router: self-service sign-up with invite codes and email verification
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session

from api.database import get_db
from api.config import settings
from api.services import registration_service, email_service

router = APIRouter(prefix="/api/auth", tags=["registration"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    invitation_code: str = Field(min_length=1)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.

    Validates the invite code, creates the user, then sends a verification email.
    The account is created regardless of whether the email send succeeds.
    """
    success, token, error = await registration_service.register_user(
        db, data.email, data.password, data.invitation_code
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    verification_link = f"{settings.WEBSITE_BASE_URL}/verify-email?token={token.token}"
    email_service.send_verification_email(data.email, verification_link)

    return {"message": "注册成功，请查收验证邮件"}


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Verify an email address using the token from the verification email.
    Redirects to the frontend verify-email page with the result.
    """
    success, user, error = registration_service.verify_email_token(db, token)
    if not success:
        return RedirectResponse(
            url=f"{settings.WEBSITE_BASE_URL}/verify-email?status=error&message={error}"
        )
    return RedirectResponse(
        url=f"{settings.WEBSITE_BASE_URL}/verify-email?status=success"
    )

"""
Password reset router for public password reset endpoints
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session
from api.database import get_db
from api.schemas.password_reset import SetPasswordRequest, VerifyTokenResponse
from api.services.password_reset_service import verify_reset_token, set_password_by_token

router = APIRouter(prefix="/api/password-reset", tags=["password-reset"])


@router.post("/verify", response_model=VerifyTokenResponse)
def verify_token(
    token: str,
    db: Session = Depends(get_db)
) -> VerifyTokenResponse:
    """
    Verify password reset token validity (public endpoint)

    Args:
        token: Reset token to verify
        db: Database session

    Returns:
        User email if token is valid
    """
    is_valid, user, error_msg = verify_reset_token(db, token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    return VerifyTokenResponse(
        email=user.email,
        valid=True
    )


@router.post("/set-password")
def set_password(
    token: str,
    password_data: SetPasswordRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Set new password using reset token (public endpoint)

    Args:
        token: Reset token
        password_data: New password data
        db: Database session

    Returns:
        Success message
    """
    success, user, error_msg = set_password_by_token(db, token, password_data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    return {"message": "密码设置成功", "email": user.email}

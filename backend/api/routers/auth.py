"""Authentication router for user login"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from api.database import get_db
from api.schemas.auth import UserLogin, TokenResponse
from api.schemas.user import UserResponse
from api.services.auth_service import authenticate_user, create_user_token

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT access token
    
    Args:
        user_credentials: Email and password
        db: Database session
        
    Returns:
        TokenResponse with access_token and token_type
        
    Raises:
        HTTPException 401: Invalid credentials
        HTTPException 403: Email not verified
    """
    user, error_type = authenticate_user(db, user_credentials.email, user_credentials.password)

    if error_type == "email_not_verified":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="请先验证您的邮箱地址，验证邮件已发送至您注册时填写的邮箱",
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_user_token(user)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        force_password_change=user.force_password_change
    )

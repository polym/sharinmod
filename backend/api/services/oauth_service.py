"""OAuth service for GitHub authentication"""
from typing import Optional
from sqlmodel import Session
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException
from api.models.user import User
from api.services.user_service import create_user_with_litellm
from api.utils.jwt import create_access_token
from datetime import timedelta
from api.config import settings
import secrets

# 创建 OAuth 客户端注册表
oauth = OAuth()


def register_github_client():
    """Register GitHub OAuth client"""
    oauth.register(
        name='github',
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        server_metadata_url='https://api.github.com/.well-known/oauth-authorization-server',
        client_kwargs={
            'scope': 'user:email'
        }
    )


def get_or_create_github_user(db: Session, github_user_info: dict) -> User:
    """
    Get existing user by GitHub ID or create new user from GitHub info

    Args:
        db: Database session
        github_user_info: GitHub user info from API

    Returns:
        User object
    """
    github_id = str(github_user_info['id'])
    email = github_user_info.get('email')

    # 先通过 GitHub ID 查找
    from sqlmodel import select
    statement = select(User).where(
        User.oauth_provider == 'github',
        User.oauth_provider_user_id == github_id
    )
    user = db.exec(statement).first()

    if user:
        return user

    # 如果 GitHub 没有返回 email，需要获取用户的 email
    if not email:
        raise HTTPException(
            status_code=400,
            detail="GitHub account has no public email. Please add an email to your GitHub account."
        )

    # 检查邮箱是否已被使用
    statement = select(User).where(User.email == email)
    existing_user = db.exec(statement).first()

    if existing_user:
        # 如果邮箱已存在但不是通过 GitHub 登录的，更新为 GitHub 登录
        existing_user.oauth_provider = 'github'
        existing_user.oauth_provider_user_id = github_id
        db.add(existing_user)
        db.commit()
        db.refresh(existing_user)
        return existing_user

    # 创建新用户
    name = github_user_info.get('name') or github_user_info.get('login')
    avatar_url = github_user_info.get('avatar_url')

    # 为 OAuth 用户生成一个随机密码（防止密码字段为空导致的问题）
    random_password = secrets.token_urlsafe(32)

    new_user = User(
        email=email,
        hashed_password=random_password,  # 存储一个随机密码，用户不会用到
        name=name,
        avatar_url=avatar_url,
        oauth_provider='github',
        oauth_provider_user_id=github_id,
    )

    # 创建用户并同步到 LiteLLM
    user = create_user_with_litellm(db, new_user)
    return user


def create_oauth_token(user: User) -> str:
    """
    Create JWT token for OAuth-authenticated user

    Args:
        user: User object

    Returns:
        JWT access token string
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return access_token

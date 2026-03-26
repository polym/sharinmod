"""OAuth service for GitHub authentication"""
from typing import Optional
from sqlmodel import Session
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException
from api.models.user import User
from api.utils.jwt import create_access_token
from datetime import timedelta
from api.config import settings
import secrets
import httpx

# 创建 OAuth 客户端注册表
oauth = OAuth()


def register_github_client():
    """Register GitHub OAuth client"""
    oauth.register(
        name='github',
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        access_token_url='https://github.com/login/oauth/access_token',
        authorize_url='https://github.com/login/oauth/authorize',
        api_base_url='https://api.github.com/',
        client_kwargs={
            'scope': 'user:email'
        }
    )


def register_gitlab_client():
    """Register GitLab OAuth client"""
    oauth.register(
        name='gitlab',
        client_id=settings.GITLAB_CLIENT_ID,
        client_secret=settings.GITLAB_CLIENT_SECRET,
        access_token_url=f'{settings.GITLAB_BASE_URL}/oauth/token',
        authorize_url=f'{settings.GITLAB_BASE_URL}/oauth/authorize',
        api_base_url=f'{settings.GITLAB_BASE_URL}/api/v4/',
        client_kwargs={
            'scope': 'read_user'
        }
    )


async def create_user_in_litellm(email: str) -> str:
    """
    Create user in LiteLLM or get existing user

    Args:
        email: User email to use as user_id

    Returns:
        LiteLLM user_id
    """
    if not settings.TESTING:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 尝试创建用户
                response = await client.post(
                    f"{settings.LITELLM_BASE_URL}/user/new",
                    json={"user_id": email},
                    headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                )

                if response.status_code == 201:
                    # 用户创建成功
                    litellm_data = response.json()
                    return litellm_data["user_id"]
                elif response.status_code == 409:
                    # 用户已存在，直接返回邮箱作为 user_id
                    print(f"[LiteLLM] User {email} already exists, using existing user")
                    return email
                else:
                    # 其他错误
                    response.raise_for_status()
                    litellm_data = response.json()
                    return litellm_data["user_id"]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                # 处理 409 冲突错误（用户已存在）
                print(f"[LiteLLM] User {email} already exists, using existing user")
                return email
            else:
                raise ValueError(f"Failed to create user in LiteLLM: HTTP {e.response.status_code}")
        except Exception as e:
            raise ValueError(f"Failed to create user in LiteLLM: {str(e)}")
    return email


async def get_or_create_github_user(db: Session, github_user_info: dict) -> User:
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
    try:
        litellm_user_id = await create_user_in_litellm(email)
        new_user.litellm_user_id = litellm_user_id
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"创建用户失败（LiteLLM 服务异常）: {str(e)}。请联系管理员处理。"
        )

    # 添加到数据库
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


async def get_or_create_gitlab_user(db: Session, gitlab_user_info: dict) -> User:
    """
    Get existing user by GitLab ID or create new user from GitLab info

    Args:
        db: Database session
        gitlab_user_info: GitLab user info from API

    Returns:
        User object
    """
    gitlab_id = str(gitlab_user_info['id'])
    email = gitlab_user_info.get('email')

    # 先通过 GitLab ID 查找
    from sqlmodel import select
    statement = select(User).where(
        User.oauth_provider == 'gitlab',
        User.oauth_provider_user_id == gitlab_id
    )
    user = db.exec(statement).first()

    if user:
        return user

    # 如果 GitLab 没有返回 email，需要提示用户添加邮箱
    if not email:
        raise HTTPException(
            status_code=400,
            detail="GitLab 账户没有公开邮箱。请在 GitLab 账户设置中添加邮箱。"
        )

    # 检查邮箱是否已被使用
    statement = select(User).where(User.email == email)
    existing_user = db.exec(statement).first()

    if existing_user:
        # 如果邮箱已存在但不是通过 GitLab 登录的，更新为 GitLab 登录
        existing_user.oauth_provider = 'gitlab'
        existing_user.oauth_provider_user_id = gitlab_id
        db.add(existing_user)
        db.commit()
        db.refresh(existing_user)
        return existing_user

    # 创建新用户
    name = gitlab_user_info.get('name')
    avatar_url = gitlab_user_info.get('avatar_url')

    # 为 OAuth 用户生成一个随机密码（防止密码字段为空导致的问题）
    random_password = secrets.token_urlsafe(32)

    new_user = User(
        email=email,
        hashed_password=random_password,
        name=name,
        avatar_url=avatar_url,
        oauth_provider='gitlab',
        oauth_provider_user_id=gitlab_id,
    )

    # 创建用户并同步到 LiteLLM
    try:
        litellm_user_id = await create_user_in_litellm(email)
        new_user.litellm_user_id = litellm_user_id
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"创建用户失败（LiteLLM 服务异常）: {str(e)}。请联系管理员处理。"
        )

    # 添加到数据库
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


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

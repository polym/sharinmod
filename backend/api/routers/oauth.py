"""OAuth router for GitHub login"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from starlette.requests import Request as StarletteRequest
from api.database import get_db
from api.services.oauth_service import oauth, register_github_client, get_or_create_github_user, create_oauth_token
from api.schemas.user import UserResponse
from api.config import settings

router = APIRouter(prefix="/api/oauth", tags=["oauth"])

# 注册 GitHub OAuth 客户端
register_github_client()


@router.get("/github/login")
async def github_login(request: Request):
    """
    Redirect user to GitHub OAuth authorization page

    Returns:
        RedirectResponse to GitHub authorization URL
    """
    # 将 FastAPI Request 转换为 Starlette Request
    starlette_request = StarletteRequest(request.scope, request.receive)
    client = oauth.create_client('github')
    redirect_uri = str(request.url_for('github_callback'))
    return await client.authorize_redirect(starlette_request, redirect_uri)


@router.get("/github/callback", name="github_callback")
async def github_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle GitHub OAuth callback

    Args:
        request: FastAPI request containing authorization code
        db: Database session

    Returns:
        RedirectResponse to frontend with JWT token in URL
    """
    starlette_request = StarletteRequest(request.scope, request.receive)
    client = oauth.create_client('github')
    token = await client.authorize_access_token(starlette_request)

    # 获取用户信息
    resp = await client.get('https://api.github.com/user', token=token)
    github_user_info = resp.json()

    # 获取或创建用户
    user = get_or_create_github_user(db, github_user_info)

    # 创建 JWT token
    access_token = create_oauth_token(user)

    # 获取前端 URL（从环境变量或使用默认值）
    frontend_url = f"http://localhost:{settings.HOST_PORT if hasattr(settings, 'HOST_PORT') else '28888'}/auth/callback?token={access_token}"
    return RedirectResponse(url=frontend_url)


@router.get("/providers")
async def get_oauth_providers():
    """
    Get list of available OAuth providers

    Returns:
        List of supported OAuth providers
    """
    return {
        "providers": [
            {
                "id": "github",
                "name": "GitHub",
                "enabled": bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET),
                "login_url": "/api/oauth/github/login"
            }
        ]
    }

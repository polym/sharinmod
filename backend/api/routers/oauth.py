"""OAuth router for GitHub login"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from starlette.requests import Request as StarletteRequest
from api.database import get_db
from api.services.oauth_service import oauth, register_github_client, register_gitlab_client, get_or_create_github_user, get_or_create_gitlab_user, create_oauth_token
from api.schemas.user import UserResponse
from api.config import settings

router = APIRouter(prefix="/api/oauth", tags=["oauth"])

# 注册 GitHub OAuth 客户端
register_github_client()
# 注册 GitLab OAuth 客户端
register_gitlab_client()


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
    # 使用环境变量中配置的回调地址
    redirect_uri = settings.GITHUB_REDIRECT_URI
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

    # 获取或创建用户 - 修复：添加 await
    user = await get_or_create_github_user(db, github_user_info)

    # 创建 JWT token
    access_token = create_oauth_token(user)

    # 获取前端 URL（从环境变量配置）
    frontend_url = f"{settings.WEBSITE_BASE_URL}/auth/callback?token={access_token}"
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
            },
            {
                "id": "gitlab",
                "name": "GitLab",
                "enabled": bool(settings.GITLAB_CLIENT_ID and settings.GITLAB_CLIENT_SECRET),
                "login_url": "/api/oauth/gitlab/login"
            }
        ]
    }


@router.get("/gitlab/login")
async def gitlab_login(request: Request):
    """
    Redirect user to GitLab OAuth authorization page

    Returns:
        RedirectResponse to GitLab authorization URL
    """
    starlette_request = StarletteRequest(request.scope, request.receive)
    client = oauth.create_client('gitlab')
    # 使用环境变量中配置的回调地址，如果没有则使用默认值
    redirect_uri = settings.GITLAB_REDIRECT_URI or f"{settings.WEBSITE_BASE_URL}/api/oauth/gitlab/callback"
    return await client.authorize_redirect(starlette_request, redirect_uri)


@router.get("/gitlab/callback", name="gitlab_callback")
async def gitlab_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle GitLab OAuth callback

    Args:
        request: FastAPI request containing authorization code
        db: Database session

    Returns:
        RedirectResponse to frontend with JWT token in URL
    """
    try:
        starlette_request = StarletteRequest(request.scope, request.receive)
        client = oauth.create_client('gitlab')

        # 添加调试信息
        print(f"[GitLab OAuth] Starting token authorization")
        print(f"[GitLab OAuth] Request URL: {request.url}")
        print(f"[GitLab OAuth] Query params: {dict(request.query_params)}")

        # 打印客户端配置
        print(f"[GitLab OAuth] Client config:")
        print(f"[GitLab OAuth] - client_id: {client.client_id}")
        print(f"[GitLab OAuth] - access_token_url: {client.access_token_url}")
        print(f"[GitLab OAuth] - authorize_url: {client.authorize_url}")
        print(f"[GitLab OAuth] - api_base_url: {client.api_base_url}")

        # 获取授权码和状态参数
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        print(f"[GitLab OAuth] Authorization code: {code[:20]}..." if code else "No code")
        print(f"[GitLab OAuth] State: {state}")

        token = await client.authorize_access_token(starlette_request)
        print(f"[GitLab OAuth] Token acquired: {type(token)}")
        print(f"[GitLab OAuth] Token keys: {list(token.keys()) if token else 'None'}")

    except Exception as e:
        print(f"[GitLab OAuth] Error during token authorization: {str(e)}")
        print(f"[GitLab OAuth] Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to authorize GitLab token: {str(e)}"
        )

    try:
        # 获取用户信息
        resp = await client.get('user', token=token)

        # 添加详细的调试日志
        print(f"[GitLab OAuth] Response status: {resp.status_code}")
        print(f"[GitLab OAuth] Response headers: {dict(resp.headers)}")
        print(f"[GitLab OAuth] Response text: {resp.text[:1000]}")

        # 检查响应状态
        if resp.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"GitLab API returned status {resp.status_code}. Response: {resp.text[:500]}"
            )

        if not resp.text:
            raise HTTPException(
                status_code=500,
                detail=f"GitLab API returned empty response. Status: {resp.status_code}"
            )

        try:
            gitlab_user_info = resp.json()
            print(f"[GitLab OAuth] User info: {gitlab_user_info}")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse GitLab user info: {str(e)}. Response text: {resp.text[:500]}"
            )

    except Exception as e:
        print(f"[GitLab OAuth] Error during API call: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with GitLab API: {str(e)}"
        )

    # 获取或创建用户
    user = await get_or_create_gitlab_user(db, gitlab_user_info)

    # 创建 JWT token
    access_token = create_oauth_token(user)

    # 重定向到前端回调页面
    frontend_url = f"{settings.WEBSITE_BASE_URL}/auth/callback?token={access_token}"
    return RedirectResponse(url=frontend_url)

# GitHub OAuth 登录实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 为平台添加 GitHub 账号登录功能，允许用户使用 GitHub 账号注册和登录

**架构:** 使用 GitHub OAuth 2.0 协议实现第三方登录。用户点击"使用 GitHub 登录"按钮后跳转到 GitHub 授权页面，授权后 GitHub 将用户重定向回应用回调端点，后端使用授权码换取访问令牌，获取用户信息并创建/查找用户，最后返回 JWT token 给前端。

**技术栈:**
- 后端: FastAPI + `authlib` (OAuth 客户端)
- 前端: Next.js + Zustand (状态管理)
- 数据库: PostgreSQL + Alembic (迁移)

---

## 准备工作

### Task 1: 安装后端依赖

**文件:**
- 修改: `backend/requirements.txt`

**Step 1: 在 requirements.txt 中添加 authlib**

```python
# 将以下内容添加到文件末尾
authlib>=1.3.0
```

**Step 2: 在容器中安装依赖**

Run: `docker exec -it sharinmod-backend-1 pip install authlib>=1.3.0`

Expected: 成功安装 authlib

**Step 3: 提交**

```bash
git add backend/requirements.txt
git commit -m "feat: add authlib dependency for OAuth"
```

---

## 后端实现

### Task 2: 添加 GitHub OAuth 配置

**文件:**
- 修改: `backend/api/config.py:30-50`

**Step 1: 在 Settings 类中添加 GitHub OAuth 配置**

```python
# 在 ACCESS_TOKEN_EXPIRE_MINUTES 后、LITELLM_BASE_URL 前添加

# GitHub OAuth Configuration
GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI: str = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:3000/auth/callback/github")
```

**Step 2: 在 backend/.env 中添加配置**

```bash
# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here
GITHUB_REDIRECT_URI=http://localhost:3000/auth/callback/github
```

**Step 3: 提交**

```bash
git add backend/api/config.py
git commit -m "feat: add GitHub OAuth configuration"
```

---

### Task 3: 扩展用户模型支持 OAuth

**文件:**
- 修改: `backend/api/models/user.py:24-42`

**Step 1: 在 User 模型中添加 OAuth 相关字段**

```python
# 在 hashed_password 字段后、created_at 前添加

# OAuth fields
oauth_provider: Optional[str] = Field(default=None, max_length=50)  # 'github', 'google', etc.
oauth_provider_user_id: Optional[str] = Field(default=None, max_length=255)  # GitHub user ID, etc.

# 修改 hashed_password 为可选（OAuth 用户没有密码）
# 将: hashed_password: str = Field(max_length=255)
# 改为: hashed_password: Optional[str] = Field(default=None, max_length=255)
```

**Step 2: 提交**

```bash
git add backend/api/models/user.py
git commit -m "feat: add OAuth fields to User model"
```

---

### Task 4: 创建数据库迁移

**文件:**
- 创建: `backend/api/alembic/versions/20250211_add_oauth_fields.py`

**Step 1: 创建迁移文件**

```python
"""Add OAuth fields to users table

Revision ID: 20250211_add_oauth
Revises:
Create Date: 2025-02-11

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20250211_add_oauth'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 使 hashed_password 可为空
    op.alter_column('users', 'hashed_password', nullable=True)

    # 添加 OAuth 字段
    op.add_column('users', sa.Column('oauth_provider', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('oauth_provider_user_id', sa.String(length=255), nullable=True))

def downgrade() -> None:
    # 删除 OAuth 字段
    op.drop_column('users', 'oauth_provider_user_id')
    op.drop_column('users', 'oauth_provider')

    # 恢复 hashed_password 为必填
    op.alter_column('users', 'hashed_password', nullable=False)
```

**Step 2: 运行迁移**

Run: `docker exec -it sharinmod-backend-1 alembic upgrade head`

Expected: 迁移成功执行

**Step 3: 验证迁移**

Run: `docker exec -it sharinmod-backend-1 alembic current`

Expected: 显示 `20250211_add_oauth`

**Step 4: 提交**

```bash
git add backend/api/alembic/versions/20250211_add_oauth_fields.py
git commit -m "feat: add OAuth fields migration"
```

---

### Task 5: 创建 OAuth 服务

**文件:**
- 创建: `backend/api/services/oauth_service.py`

**Step 1: 创建 OAuth 服务文件**

```python
"""OAuth service for GitHub authentication"""
from typing import Optional
from sqlmodel import Session
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request

from api.models.user import User
from api.services.user_service import create_user_with_litellm
from api.utils.jwt import create_access_token
from datetime import timedelta
from api.config import settings

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
    import secrets
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
```

**Step 2: 提交**

```bash
git add backend/api/services/oauth_service.py
git commit -m "feat: create OAuth service for GitHub"
```

---

### Task 6: 创建 OAuth 路由

**文件:**
- 创建: `backend/api/routers/oauth.py`

**Step 1: 创建 OAuth 路由文件**

```python
"""OAuth router for GitHub login"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from starlette.requests import Request as StarletteRequest
from api.database import get_db
from api.services.oauth_service import oauth, register_github_client, get_or_create_github_user, create_oauth_token
from api.schemas.user import UserResponse

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


@router.get("/github/callback")
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

    # 重定向回前端，携带 token
    frontend_url = f"http://localhost:3000/auth/callback?token={access_token}"
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
```

**Step 2: 提交**

```bash
git add backend/api/routers/oauth.py
git commit -m "feat: create OAuth router for GitHub"
```

---

### Task 7: 注册 OAuth 路由

**文件:**
- 修改: `backend/api/app.py:1-85`

**Step 1: 在 app.py 中导入并注册 oauth_router**

```python
# 在文件顶部导入部分添加（约第 20 行）
from api.routers.oauth import router as oauth_router router as oauth_router

# 在 create_app 函数中注册路由（约第 80 行，在 auth_router 后添加）
app.include_router(oauth_router)
```

**Step 2: 验证后端重启**

Run: `docker-compose restart backend`

Expected: backend 成功重启

**Step 3: 检查日志确认无错误**

Run: `docker-compose logs backend | tail -20`

Expected: 无错误日志

**Step 4: 提交**

```bash
git add backend/api/app.py
git commit -m "feat: register OAuth router in app"
```

---

## 前端实现

### Task 8: 创建 OAuth 回调页面

**文件:**
- 创建: `frontend/src/app/auth/callback/page.tsx`

**Step 1: 创建回调页面组件**

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { authAPI } from '@/lib/services';

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string>('');
  const login = useAuthStore((state) => state.login);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const token = searchParams.get('token');
        const error = searchParams.get('error');

        if (error) {
          setError(decodeURIComponent(error));
          return;
        }

        if (!token) {
          setError('No token received from OAuth provider');
          return;
        }

        // 使用 token 获取用户信息
        const response = await authAPI.getProfile();
        const user = response.data;

        // 登录并存储 token
        login(user, token);

        // 跳转到共享页面
        router.push('/shared');
      } catch (err) {
        console.error('OAuth callback error:', err);
        setError('Authentication failed. Please try again.');
      }
    };

    handleCallback();
  }, [searchParams, router, login]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full p-8 bg-white rounded-lg shadow-md">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Authentication Error</h1>
          <p className="text-gray-700 mb-6">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
          >
            Return to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Logging you in...</p>
      </div>
    </div>
  );
}
```

**Step 2: 提交**

```bash
git add frontend/src/app/auth/callback/page.tsx
git commit -m "feat: create OAuth callback page"
```

---

### Task 9: 添加 GitHub 登录按钮到登录对话框

**文件:**
- 修改: `frontend/src/components/LoginDialogContent.tsx`

**Step 1: 在文件顶部添加 GitHub 图标导入和翻译键**

```typescript
// 在现有导入后添加（约第 11 行后）
import GithubIcon from '@/components/icons/github-icon';

// 翻译使用（已有 t, tValidation, tToast，不需要额外添加）
```

**Step 2: 创建 GitHub 图标组件**

**文件:**
- 创建: `frontend/src/components/icons/github-icon.tsx`

```typescript
export default function GithubIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="currentColor"
    >
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.234 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
    </svg>
  );
}
```

**Step 3: 修改 LoginDialogContent.tsx 添加 GitHub 登录按钮**

```typescript
// 在现有导入后添加（约第 11 行后）
import GithubIcon from '@/components/icons/github-icon';

// 在现有状态后添加（约第 33 行后）
const [oauthLoading, setOauthLoading] = useState(false);

// 添加 GitHub 登录函数（在 handleSubmit 函数后添加）
const handleGithubLogin = async () => {
  setOauthLoading(true);
  try {
    // 跳转到后端 OAuth 端点
    window.location.href = 'http://localhost:28888/api/oauth/github/login';
  } catch (err) {
    console.error('GitHub login error:', err);
    setError(tToast('loginFailed'));
    setOauthLoading(false);
  }
};

// 在表单中添加分隔符和 GitHub 按钮（在 <form> 标签内的最后一个 Button 后、"没有账号" div 前添加）
<div className="relative my-4">
  <div className="absolute inset-0 flex items-center">
    <div className="w-full border-t border-gray-300"></div>
  </div>
  <div className="relative flex justify-center text-sm">
    <span className="px-2 bg-white text-gray-500">或</span>
  </div>
</div>

<Button
  type="button"
  variant="outline"
  className="w-full"
  onClick={handleGithubLogin}
}
  disabled={oauthLoading || loading}
>
  {oauthLoading ? (
    <span className="animate-spin mr-2">
      <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </span>
  ) : (
    <GithubIcon className="h-4 w-4 mr-2" />
  )}
  {t('githubLogin')}
</Button>
```

**Step 4: 添加翻译键**

**文件:**
- 修改: `frontend/src/messages/zh-CN.json` (需要查找正确的翻译文件)

```json
// 在 auth 对象中添加
"githubLogin": "使用 GitHub 登录"
```

**Step 5: 提交**

```bash
git add frontend/src/components/icons/github-icon.tsx
git add frontend/src/components/LoginDialogContent.tsx
git add frontend/src/messages/zh-CN.json
git commit -m "feat: add GitHub login button to login dialog"
```

---

### Task 10: 在 API 服务中添加 OAuth 相关调用

**文件:**
- 修改: `frontend/src/lib/services.ts:8-18`

**Step 1: 在 authAPI 中添加 OAuth 相关方法**

```typescript
// Auth API
export const authAPI = {
  register: (data: { email: string; password: string }) =>
    api.post('/api/users/register', data),

  login: (data: { email: string; password: string }) =>
    api.post('/api/auth/login', data),

  getProfile: () => api.get('/api/users/me'),

  // 新增 OAuth 相关方法
  getOAuthProviders: () => api.get('/api/oauth/providers'),
};
```

**Step 2: 提交**

```bash
git add frontend/src/lib/services.ts
git commit -m "feat: add OAuth API methods to services"
```

---

## 配置和测试

### Task 11: 配置 GitHub OAuth 应用

**说明:** 这个任务需要在 GitHub 上完成，不能通过代码自动化

**Step 1: 在 GitHub 创建 OAuth App**

1. 访问 https://github.com/settings/developers
2. 点击 "New OAuth App"
3. 填写以下信息：
   - Application name: `Sharinmod` (或你喜欢的名称)
   - Homepage URL: `http://localhost:28888` (或生产环境域名)
   - Application description: `Sharinmod AI Platform`
   - Authorization callback URL: `http://localhost:28888/api/oauth/github/callback`
4. 点击 "Register application"
5. 复制 Client ID 和 Client Secret

**Step 2: 更新环境变量**

**文件:**
- 修改: `.env` (项目根目录)

```bash
# GitHub OAuth
GITHUB_CLIENT_ID=your_actual_client_id_from_github
GITHUB_CLIENT_SECRET=your_actual_client_secret_from_github
GITHUB_REDIRECT_URI=http://localhost:28888/api/oauth/github/callback
```

**Step 3: 重启后端服务**

Run: `docker-compose restart backend`

Expected: backend 成功重启

**Step 4: 提交 .env.example**

**文件:**
- 修改: `.env.example`

```bash
# GitHub OAuth (需要从 GitHub 获取)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:28888/api/oauth/github/callback
```

**Step 5: 提交**

```bash
git add .env.example
git commit -m "feat: document GitHub OAuth configuration"
```

---

### Task 12: 端到端测试

**说明:** 手动测试 GitHub 登录流程

**Step 1: 启动所有服务**

Run: `docker-compose up -d`

Expected: 所有服务正常运行

**Step 2: 访问前端页面**

Run: 浏览器打开 `http://localhost:28888`

Expected: 页面正常加载

**Step 3: 打开登录对话框**

操作: 点击导航栏上的登录按钮

Expected: 登录对话框正常显示

**Step 4: 测试 GitHub 登录按钮**

操作: 点击 "使用 GitHub 登录" 按钮

Expected:
1. 跳转到 GitHub 授权页面
2. 看到应用名称和请求的权限
3. 点击 "Authorize" 按钮

**Step 5: 验证登录成功**

Expected:
1. 重定向回前端 `/shared` 页面
2. 用户已登录状态
3. 用户信息显示正确（头像、名称等）

**Step 6: 检查数据库**

Run: `docker exec -it sharinmod-backend-1 psql -U postgres -d sharinmod -c "SELECT id, email, name, oauth_provider, oauth_provider_user_id FROM users WHERE oauth_provider = 'github';"`

Expected: 看到新创建的 GitHub 用户记录

**Step 7: 测试重复登录（同一用户）**

操作:
1. 登出当前用户
2. 再次使用同一 GitHub 账号登录

Expected:
1. 成功登录
2. 不会创建新用户记录（使用已有记录）

**Step 8: 测试数据库持久化**

操作: 重启服务后检查用户登录状态

Expected: JWT token 仍然有效，用户保持登录状态

---

## 可选任务

### Task 13: 在注册页面添加 GitHub 注册按钮

**文件:**
- 修改: `frontend/src/app/register/page.tsx`

**Step 1: 在注册页面添加相同的 GitHub 登录按钮**

（参考 Task 9 中的实现方式）

**Step 2: 提交**

```bash
git add frontend/src/app/register/page.tsx
git commit -m "feat: add GitHub login button to register page"
```

---

### Task 14: 添加环境变量验证

**文件:**
- 修改: `backend/api/config.py:30-50`

**Step 1: 添加环境变量验证逻辑**

```python
# 在 Settings 类中添加验证方法

@field_validator("GITHUB_CLIENT_ID")
@classmethod
def validate_github_config(cls, v: str, info) -> str:
    """Validate that both GitHub client ID and secret are provided together"""
    if v and not info.data.get("GITHUB_CLIENT_SECRET"):
        raise ValueError("GITHUB_CLIENT_SECRET must be set when GITHUB_CLIENT_ID is provided")
    return v
```

**Step 2: 提交**

```bash
git add backend/api/config.py
git commit -m "feat: add GitHub OAuth config validation"
```

---

## 最终验证

### Task 15: 完整功能验证和文档

**Step 1: 运行所有后端测试（如果有）**

Run: `docker exec -it sharinmod-backend-1 pytest -v`

Expected: 所有测试通过

**Step 2: 检查 Docker 容器日志**

Run: `docker-compose logs --tail=50`

Expected: 无错误日志

**Step 3: 验证 CORS 配置**

Run: `curl -X OPTIONS http://localhost:28888/api/oauth/providers -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: GET" -v`

Expected: 返回正确的 CORS headers

**Step 4: 测试 /api/oauth/providers 端点**

Run: `curl http://localhost:28888/api/oauth/providers`

Expected: 返回 OAuth 提供商列表，包含 GitHub

**Step 5: 检查 git 状态**

Run: `git status`

Expected: 只有未跟踪的文件，没有未提交的更改

**Step 6: 提交最终代码**

```bash
git add .
git commit -m "feat: complete GitHub OAuth login implementation"
```

---

## 回滚计划

如果需要回滚此功能：

1. **移除 OAuth 路由:**
   ```bash
   docker exec -it sharinmod-backend-1 alembic downgrade -1
   ```

2. **恢复代码:**
   ```bash
   git revert HEAD
   ```

3. **重启服务:**
   ```bash
   docker-compose restart backend frontend
   ```

---

## 注意事项

1. **HTTPS 要求:** 生产环境必须使用 HTTPS，GitHub OAuth 不接受 HTTP 回调（localhost 除外）
2. **环境变量:** 永远不要将 `.env` 文件提交到 git
3. **密钥安全:** Client Secret 应该通过安全渠道部署到生产环境
4. **用户数据:** GitHub 用户信息中可能没有公开邮箱，需要提示用户添加邮箱
5. **已有用户:** 如果用户的 GitHub 邮箱已存在系统中，会链接到已有账户

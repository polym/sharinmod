"""
REST API endpoints for Claw (QQ bot) management
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlmodel import Session
from typing import List
import re
import httpx

from api.database import get_db
from api.dependencies.auth import get_current_user
from api.models.user import User
from api.schemas.claw import ClawCreate, ClawResponse, ClawUpdate, ClawList
from api.config import settings
from api.services import k8s_service
from api.services.claw_service import (
    create_claw_async,
    get_user_claws,
    get_user_claw_by_id,
    update_claw_name,
    delete_claw_async,
)
from api.utils.jwt import verify_token
from api.services.user_service import get_user_by_email

router = APIRouter(prefix="/api/claws", tags=["claws"])


@router.get("/config")
def get_claw_config(
    current_user: User = Depends(get_current_user),
):
    """返回龙虾相关前端配置，包括主流大脑模型列表"""
    import yaml
    from api.config import _get_config_path
    config_path = _get_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        full_config = yaml.safe_load(f) or {}
    claw_types_config = full_config.get("claw_types", {})
    featured = claw_types_config.get("featured_brain_models", ["glm-4.7", "minimax-m2.5", "kimi-k2.5"])
    return {"featured_brain_models": featured}


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ClawResponse)
async def create_claw(
    request: ClawCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    Create a new Claw (QQ bot Deployment on K8s)

    - Maximum 10 claws per user
    - Returns 201 Created with claw details
    - Creates K8s Deployment named claw-{id}
    """
    return await create_claw_async(session, current_user, request)


@router.get("", response_model=ClawList)
def list_claws(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    List all claws belonging to the current user

    - Returns claws ordered by creation date (newest first)
    """
    claws = get_user_claws(session, current_user.id)
    return ClawList(total=len(claws), items=claws)


@router.put("/{claw_id}", response_model=ClawResponse)
def update_claw(
    claw_id: int,
    request: ClawUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    Update the name of a claw

    - Returns 404 if claw not found or not owned by current user
    """
    return update_claw_name(session, current_user.id, claw_id, request)


@router.delete("/{claw_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_claw(
    claw_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    Delete a claw and its K8s StatefulSet

    - Deletes K8s StatefulSet, Service, PVC, ConfigMap (ignores 404)
    - Then deletes database record
    - Returns 204 No Content
    """
    await delete_claw_async(session, current_user.id, claw_id)


@router.post("/{claw_id}/restart", response_model=ClawResponse)
async def restart_claw(
    claw_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """Restart a claw by deleting its K8s Pod and letting StatefulSet recreate it."""
    claw = get_user_claw_by_id(session, current_user.id, claw_id)
    if not claw.k8s_deployment_name:
        raise HTTPException(status_code=400, detail="Claw has no K8s resource")

    k8s_service.restart_statefulset_pod(
        claw.k8s_deployment_name,
        namespace=claw.k8s_namespace or "default"
    )
    return claw


@router.get("/{claw_id}/logs")
def stream_claw_logs(
    claw_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    Stream real-time logs for a claw via SSE.

    - Returns text/event-stream
    - Each SSE event: data: <log_line>
    - Requires claw to be owned by current user
    """
    claw = get_user_claw_by_id(session, current_user.id, claw_id)
    if not claw.k8s_deployment_name:
        raise HTTPException(status_code=400, detail="Claw has no K8s resource")

    def sse_generator():
        for line in k8s_service.stream_statefulset_logs(claw.k8s_deployment_name, namespace=claw.k8s_namespace or "default", container="claw"):
            if isinstance(line, bytes):
                text = line.decode("utf-8", errors="replace").rstrip("\n")
            else:
                text = str(line).rstrip("\n")
            if text:
                yield f"data: {text}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
        },
    )


# HTTP/1.1 hop-by-hop headers，转发时需过滤
# 'cookie' 单独过滤：避免将后端 auth cookie 泄露给上游 filebrowser
_HOP_BY_HOP_HEADERS = frozenset({
    "connection", "transfer-encoding", "te", "trailers",
    "upgrade", "keep-alive", "proxy-authenticate",
    "proxy-authorization", "host", "content-length", "cookie",
})

# RFC 1123 label: lowercase alphanumeric and hyphens, 1-63 chars
_K8S_NS_RE = re.compile(r'^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$')

_FB_COOKIE_NAME = "sharinmod-fb-token"


def _get_filebrowser_user(request: Request, session: Session = Depends(get_db)) -> User:
    """
    Auth for filebrowser proxy: accepts either
    - Authorization: Bearer <jwt>  (programmatic / axios)
    - Cookie sharinmod-fb-token=<jwt>  (browser iframe, all subsequent SPA requests)
    """
    token: str | None = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if not token:
        token = request.cookies.get(_FB_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    email = verify_token(token)
    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    user = get_user_by_email(session, email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.get("/{claw_id}/filebrowser", include_in_schema=False)
async def redirect_to_filebrowser(
    claw_id: int,
    current_user: User = Depends(_get_filebrowser_user),
    session: Session = Depends(get_db),
):
    """重定向到 filebrowser 根路径（补充 trailing slash）"""
    get_user_claw_by_id(session, current_user.id, claw_id)  # ownership check，非所有者返回 404
    return RedirectResponse(url=f"/api/claws/{claw_id}/filebrowser/", status_code=302)


@router.api_route(
    "/{claw_id}/filebrowser/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def proxy_filebrowser(
    claw_id: int,
    path: str,
    request: Request,
    current_user: User = Depends(_get_filebrowser_user),
    session: Session = Depends(get_db),
):
    """
    将 filebrowser 请求代理到对应 pod。
    注入 X-Auth-User header 完成 proxy auth，无需 filebrowser 密码验证。
    ownership check 确保用户只能访问自己的龙虾。
    """
    claw = get_user_claw_by_id(session, current_user.id, claw_id)
    namespace = claw.k8s_namespace or "default"
    if not _K8S_NS_RE.match(namespace):
        raise HTTPException(status_code=500, detail="Invalid namespace in claw record")

    # Pod headless DNS: {pod-name}.{svc-name}.{namespace}.svc.cluster.local
    target_base = (
        f"http://claw-{claw_id}-0.claw-{claw_id}.{namespace}.svc.cluster.local:8080"
        f"/api/claws/{claw_id}/filebrowser/{path}"
    )
    if request.query_params:
        target_base += f"?{request.query_params}"

    # 过滤 hop-by-hop headers，注入 proxy auth header
    fwd_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP_HEADERS
    }
    fwd_headers["X-Auth-User"] = "sharinmod"

    body = await request.body()
    async_client = httpx.AsyncClient(timeout=300.0)
    try:
        upstream_req = async_client.build_request(
            method=request.method,
            url=target_base,
            headers=fwd_headers,
            content=body,
        )
        upstream_resp = await async_client.send(upstream_req, stream=True)
    except Exception:
        await async_client.aclose()
        raise

    async def _stream_response():
        try:
            async for chunk in upstream_resp.aiter_bytes():
                yield chunk
        finally:
            await upstream_resp.aclose()
            await async_client.aclose()

    resp_headers = {
        k: v for k, v in upstream_resp.headers.items()
        if k.lower() not in _HOP_BY_HOP_HEADERS
    }
    return StreamingResponse(
        _stream_response(),
        status_code=upstream_resp.status_code,
        headers=resp_headers,
    )

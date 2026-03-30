"""
REST API endpoints for Claw (QQ bot) management
"""
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketException, status
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlmodel import Session
from typing import List
import re
import httpx
import asyncio
import websockets

from api.database import get_db
from api.dependencies.auth import get_current_user
from api.models.user import User
from api.models.claw import ClawStatus
from api.schemas.claw import ClawCreate, ClawResponse, ClawUpdate, ClawList, ArchiveList, ArchiveItem, ArchiveCreateResponse
from api.config import settings
from api.services import k8s_service
from api.services.claw_service import (
    create_claw_async,
    get_user_claws_with_usage,
    get_user_claw_by_id,
    update_claw_name,
    delete_claw_async,
)
from api.utils.jwt import verify_token
from api.services.user_service import get_user_by_email
from api.models.operation_log import OperationType, ResourceType
from api.utils.operation_log import log_operation

router = APIRouter(prefix="/api/claws", tags=["claws"])


@router.get("/config")
def get_claw_config(
    current_user: User = Depends(get_current_user),
):
    """返回龙虾相关前端配置，包括主流大脑模型列表和存档开关"""
    import yaml
    from api.config import _get_config_path
    config_path = _get_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        full_config = yaml.safe_load(f) or {}
    claw_types_config = full_config.get("claw_types", {})
    featured = claw_types_config.get("featured_brain_models", ["glm-4.7", "minimax-m2.5", "kimi-k2.5"])
    prunc_enabled = full_config.get("prunc_enabled", False) is True
    claws_archive_enabled = full_config.get("claws_archive_enabled", False) is True
    claws_archive_auto_enabled = full_config.get("claws_archive_auto_enabled", False) is True
    claws_archive_schedule_interval = full_config.get("claws_archive_schedule_interval", 20)
    return {
        "featured_brain_models": featured,
        "prunc_enabled": prunc_enabled,
        "claws_archive_enabled": claws_archive_enabled,
        "claws_archive_auto_enabled": claws_archive_auto_enabled,
        "claws_archive_schedule_interval": claws_archive_schedule_interval,
    }


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ClawResponse)
@log_operation(ResourceType.CLAW, OperationType.CREATE, use_return_value=True)
async def create_claw(
    request: ClawCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    Create a new Claw (QQ bot Deployment on K8s)

    - Maximum {max_claws} claws per user (Admin users exempt)
    - Returns 201 Created with claw details
    - Creates K8s Deployment named claw-{id}
    """
    return await create_claw_async(session, current_user, request)


@router.get("/{claw_id}", response_model=ClawResponse)
def get_claw(
    claw_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    Get a specific claw by ID

    - Returns 404 if claw not found or not owned by current user
    - Includes real-time `ready` status from K8s Pod
    """
    claw = get_user_claw_by_id(session, current_user.id, claw_id)

    # 实时获取 Pod 状态填充 ready 字段
    ready = None
    if claw.k8s_deployment_name:
        pod_status = k8s_service.get_pod_status(
            claw.k8s_namespace or "default",
            f"{claw.k8s_deployment_name}-0"
        )
        ready = pod_status.get("claw_ready")

    # 使用 from_attributes 创建响应，避免修改原 ORM 对象
    return ClawResponse.model_validate(claw).model_copy(update={"ready": ready})


@router.get("", response_model=ClawList)
def list_claws(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    List all claws belonging to the current user with daily usage data

    - Returns claws ordered by creation date (newest first)
    """
    claws_data = get_user_claws_with_usage(session, current_user.id)
    # 将 dict 列表转换为 ClawResponse 对象列表
    claws = [ClawResponse(**item) for item in claws_data]
    return ClawList(total=len(claws), items=claws)


@router.put("/{claw_id}", response_model=ClawResponse)
@log_operation(ResourceType.CLAW, OperationType.UPDATE, resource_id_param="claw_id")
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
@log_operation(ResourceType.CLAW, OperationType.DELETE, resource_id_param="claw_id")
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
@log_operation(ResourceType.CLAW, OperationType.RESTART, resource_id_param="claw_id")
async def restart_claw(
    claw_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """Restart a claw by deleting its K8s Pod and letting StatefulSet recreate it."""
    from datetime import datetime
    from api.models.claw import ClawStatus

    claw = get_user_claw_by_id(session, current_user.id, claw_id)
    if not claw.k8s_deployment_name:
        raise HTTPException(status_code=400, detail="Claw has no K8s resource")

    # 立即更新数据库状态为 PENDING（重启中）
    claw.status = ClawStatus.PENDING
    claw.updated_at = datetime.utcnow()
    session.add(claw)
    session.commit()
    session.refresh(claw)

    # 异步执行 K8s 重启操作
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


@router.post("/{claw_id}/lark-install")
def lark_install(
    claw_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    在 claw 容器中执行 npx -y @larksuite/openclaw-lark@2026.3.17 install
    并以 SSE 格式流式返回输出。
    仅支持 OPENCLAW 类型且 status 为 RUNNING 的龙虾。
    """
    from api.models.claw import ClawType, ClawStatus
    claw = get_user_claw_by_id(session, current_user.id, claw_id)
    if claw.type != ClawType.OPENCLAW:
        raise HTTPException(status_code=400, detail="仅 OpenClaw 类型支持飞书安装")
    if claw.status != ClawStatus.RUNNING:
        raise HTTPException(status_code=400, detail="龙虾未在运行状态")
    if not claw.k8s_deployment_name:
        raise HTTPException(status_code=400, detail="Claw has no K8s resource")

    def sse_generator():
        command = ["sh", "-c", "COLUMNS=80 LINES=24 npx -y @larksuite/openclaw-lark@2026.3.17 install"]
        for chunk in k8s_service.exec_pod_command_stream(
            claw.k8s_deployment_name,
            command=command,
            namespace=claw.k8s_namespace or "default",
            container="claw",
        ):
            if isinstance(chunk, bytes):
                text = chunk.decode("utf-8", errors="replace")
            else:
                text = str(chunk)
            # 按行分割，每行作为一个 SSE 事件
            for line in text.splitlines():
                if line:
                    yield f"data: {line}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{claw_id}/weixin-login")
def weixin_login(
    claw_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    在 claw 容器中执行 openclaw channels login --channel openclaw-weixin
    并以 SSE 格式流式返回输出。
    仅支持 OPENCLAW 类型且 status 为 RUNNING 的龙虾。
    """
    from api.models.claw import ClawType, ClawStatus
    claw = get_user_claw_by_id(session, current_user.id, claw_id)
    if claw.type != ClawType.OPENCLAW:
        raise HTTPException(status_code=400, detail="仅 OpenClaw 类型支持微信登录")
    if claw.status != ClawStatus.RUNNING:
        raise HTTPException(status_code=400, detail="龙虾未在运行状态")
    if not claw.k8s_deployment_name:
        raise HTTPException(status_code=400, detail="Claw has no K8s resource")

    def sse_generator():
        command = ["sh", "-c", "COLUMNS=80 LINES=24 openclaw channels login --channel openclaw-weixin"]
        for chunk in k8s_service.exec_pod_command_stream(
            claw.k8s_deployment_name,
            command=command,
            namespace=claw.k8s_namespace or "default",
            container="claw",
        ):
            if isinstance(chunk, bytes):
                text = chunk.decode("utf-8", errors="replace")
            else:
                text = str(chunk)
            # 按行分割，每行作为一个 SSE 事件
            for line in text.splitlines():
                if line:
                    yield f"data: {line}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# HTTP/1.1 hop-by-hop headers，转发时需过滤
# 'cookie' 单独处理：过滤 sharinmod-fb-token，保留 filebrowser 的 auth 等其他 cookie
_HOP_BY_HOP_HEADERS = frozenset({
    "connection", "transfer-encoding", "te", "trailers",
    "upgrade", "keep-alive", "proxy-authenticate",
    "proxy-authorization", "content-length",
})

# RFC 1123 label: lowercase alphanumeric and hyphens, 1-63 chars
_K8S_NS_RE = re.compile(r'^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$')

_FB_COOKIE_NAME = "sharinmod-fb-token"
_OW_COOKIE_NAME = "sharinmod-ow-token"


@router.get("/{claw_id}/archives", response_model=ArchiveList)
def get_claw_archives(
    claw_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    获取龙虾的存档列表

    - 返回指定龙虾的所有存档
    - 仅在 prunc_enabled=true 且 claws_archive_enabled=true 时可用
    """
    from api.config import _get_config_path
    import yaml

    # 检查存档功能是否启用
    config_path = _get_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        full_config = yaml.safe_load(f) or {}
    prunc_enabled = full_config.get("prunc_enabled", False) is True
    claws_archive_enabled = full_config.get("claws_archive_enabled", False) is True

    if not prunc_enabled or not claws_archive_enabled:
        raise HTTPException(status_code=403, detail="存档功能未启用")

    claw = get_user_claw_by_id(session, current_user.id, claw_id)

    # 获取存档列表
    archives = k8s_service.list_snapshots(
        claw_id,
        namespace=claw.k8s_namespace or "default",
    )

    return ArchiveList(total=len(archives), items=archives)


@router.post("/{claw_id}/archives", status_code=status.HTTP_201_CREATED, response_model=ArchiveCreateResponse)
def create_claw_archive(
    claw_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    创建龙虾存档

    - 为指定龙虾创建 workspace 和 rootfs 的 VolumeSnapshot
    - 仅在 prunc_enabled=true 且 claws_archive_enabled=true 时可用
    - 龙虾状态必须为 RUNNING
    """
    import time
    from api.config import _get_config_path
    import yaml

    # 检查存档功能是否启用
    config_path = _get_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        full_config = yaml.safe_load(f) or {}
    prunc_enabled = full_config.get("prunc_enabled", False) is True
    claws_archive_enabled = full_config.get("claws_archive_enabled", False) is True

    if not prunc_enabled or not claws_archive_enabled:
        raise HTTPException(status_code=403, detail="存档功能未启用")

    claw = get_user_claw_by_id(session, current_user.id, claw_id)

    # 检查手动存档数量限制
    max_manual = full_config.get("claws_archive_max_manual", 5)
    manual_count = k8s_service.count_manual_archives(
        claw_id,
        namespace=claw.k8s_namespace or "default",
    )
    if manual_count >= max_manual:
        raise HTTPException(
            status_code=400,
            detail=f"手动存档数量已达上限（{max_manual}个），请删除旧存档后重试"
        )

    # 检查龙虾状态
    if claw.status != ClawStatus.RUNNING:
        raise HTTPException(status_code=400, detail="只能在运行中的龙虾上创建存档")

    if not claw.k8s_deployment_name:
        raise HTTPException(status_code=400, detail="Claw has no K8s resource")

    namespace = claw.k8s_namespace or "default"
    timestamp = str(int(time.time()))

    # 获取当前 PVC 名称
    from kubernetes import client
    from kubernetes.client.rest import ApiException

    core_v1 = k8s_service._get_core_v1_api()

    try:
        pvcs = core_v1.list_namespaced_persistent_volume_claim(
            namespace=namespace,
            label_selector=f"app=claw-{claw_id}",
        )
    except ApiException as e:
        raise HTTPException(status_code=500, detail=f"Failed to list PVCs: {e}")

    workspace_pvc = None
    rootfs_pvc = None

    for pvc in pvcs.items:
        pvc_type = pvc.metadata.labels.get("pvc-type")
        if pvc_type == "workspace":
            workspace_pvc = pvc.metadata.name
        elif pvc_type == "rootfs":
            rootfs_pvc = pvc.metadata.name

    if not workspace_pvc:
        raise HTTPException(status_code=500, detail="Workspace PVC not found")

    # 创建 workspace snapshot
    workspace_snapshot = k8s_service.create_snapshot(
        claw_id,
        workspace_pvc,
        "workspace-data",
        timestamp,
        namespace,
    )

    # 创建 rootfs snapshot (如果存在)
    rootfs_snapshot = None
    if rootfs_pvc:
        rootfs_snapshot = k8s_service.create_snapshot(
            claw_id,
            rootfs_pvc,
            "rootfs",
            timestamp,
            namespace,
        )

    return ArchiveCreateResponse(
        timestamp=timestamp,
        workspace_snapshot_name=workspace_snapshot,
        rootfs_snapshot_name=rootfs_snapshot,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


@router.post("/{claw_id}/archives/{timestamp}/restore", response_model=ClawResponse)
def restore_claw_archive(
    claw_id: int,
    timestamp: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    从存档恢复龙虾

    - 从指定 timestamp 的存档恢复龙虾
    - 仅在 prunc_enabled=true 且 claws_archive_enabled=true 时可用
    - 会创建新 PVC 并更新 StatefulSet
    """
    from api.config import _get_config_path
    import yaml

    # 检查存档功能是否启用
    config_path = _get_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        full_config = yaml.safe_load(f) or {}
    prunc_enabled = full_config.get("prunc_enabled", False) is True
    claws_archive_enabled = full_config.get("claws_archive_enabled", False) is True

    if not prunc_enabled or not claws_archive_enabled:
        raise HTTPException(status_code=403, detail="存档功能未启用")

    claw = get_user_claw_by_id(session, current_user.id, claw_id)

    if not claw.k8s_deployment_name:
        raise HTTPException(status_code=400, detail="Claw has no K8s resource")

    # 获取存档信息
    archives = k8s_service.list_snapshots(
        claw_id,
        namespace=claw.k8s_namespace or "default",
    )

    target_archive = None
    for archive in archives:
        if archive["timestamp"] == timestamp:
            target_archive = archive
            break

    if not target_archive:
        raise HTTPException(status_code=404, detail=f"Archive {timestamp} not found")

    # 验证快照名称存在
    workspace_snapshot_name = target_archive.get("workspace_snapshot_name")
    if not workspace_snapshot_name:
        raise HTTPException(status_code=400, detail="Archive has no workspace snapshot")

    # 恢复存档
    k8s_service.restore_from_snapshot(
        claw_id,
        timestamp,
        workspace_snapshot_name,
        target_archive.get("rootfs_snapshot_name"),
        namespace=claw.k8s_namespace or "default",
    )

    return claw


@router.delete("/{claw_id}/archives/{timestamp}", status_code=status.HTTP_204_NO_CONTENT)
def delete_claw_archive(
    claw_id: int,
    timestamp: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    删除龙虾存档

    - 删除指定 timestamp 的 workspace 和 rootfs VolumeSnapshot
    - 仅在 prunc_enabled=true 且 claws_archive_enabled=true 时可用
    """
    from api.config import _get_config_path
    import yaml

    # 检查存档功能是否启用
    config_path = _get_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        full_config = yaml.safe_load(f) or {}
    prunc_enabled = full_config.get("prunc_enabled", False) is True
    claws_archive_enabled = full_config.get("claws_archive_enabled", False) is True

    if not prunc_enabled or not claws_archive_enabled:
        raise HTTPException(status_code=403, detail="存档功能未启用")

    claw = get_user_claw_by_id(session, current_user.id, claw_id)

    # 调用删除服务
    k8s_service.delete_snapshot(
        claw_id,
        timestamp,
        namespace=claw.k8s_namespace or "default",
    )


def _filter_cookie_header(cookie_header: str | None, cookie_name: str = _FB_COOKIE_NAME) -> str | None:
    """
    过滤掉 sharinmod 专用 cookie，保留其他 cookie
    """
    if not cookie_header:
        return None
    cookies = [
        c.strip() for c in cookie_header.split(";")
        if c.strip() and not c.strip().startswith(f"{cookie_name}=")
    ]
    return "; ".join(cookies) if cookies else None


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
    # 过滤掉 sharinmod-fb-token，保留 filebrowser 的 auth 等其他 cookie
    if "cookie" in request.headers:
        filtered_cookie = _filter_cookie_header(request.headers["cookie"])
        if filtered_cookie:
            fwd_headers["cookie"] = filtered_cookie
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
            async for chunk in upstream_resp.aiter_raw():
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


def _get_openclaw_web_user(request: Request, session: Session = Depends(get_db)) -> User:
    """
    Auth for openclaw-web proxy: accepts either
    - Authorization: Bearer <jwt>  (programmatic / axios)
    - Cookie sharinmod-ow-token=<jwt>  (browser, all subsequent SPA requests)
    """
    token: str | None = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if not token:
        token = request.cookies.get(_OW_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    email = verify_token(token)
    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    user = get_user_by_email(session, email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.api_route(
    "/{claw_id}/openclaw-web",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def proxy_openclaw_web_root(
    claw_id: int,
    request: Request,
    current_user: User = Depends(_get_openclaw_web_user),
    session: Session = Depends(get_db),
):
    """
    将 openclaw-web 根路径请求代理到对应 pod 的 3000 端口。
    ownership check 确保用户只能访问自己的龙虾。
    """
    claw = get_user_claw_by_id(session, current_user.id, claw_id)
    namespace = claw.k8s_namespace or "default"
    if not _K8S_NS_RE.match(namespace):
        raise HTTPException(status_code=500, detail="Invalid namespace in claw record")

    # Pod headless DNS: {pod-name}.{svc-name}.{namespace}.svc.cluster.local
    target_base = (
        f"http://claw-{claw_id}-0.claw-{claw_id}.{namespace}.svc.cluster.local:3000"
        f"/api/claws/{claw_id}/openclaw-web"
    )
    if request.query_params:
        target_base += f"?{request.query_params}"

    # 过滤 hop-by-hop headers
    fwd_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP_HEADERS and k.lower() != "host"
    }
    # 重写 Host 为目标地址
    fwd_headers["host"] = f"claw-{claw_id}-0.claw-{claw_id}.{namespace}.svc.cluster.local:3000"
    # 重写 Origin 为目标地址
    if "origin" in fwd_headers:
        fwd_headers["origin"] = f"http://claw-{claw_id}-0.claw-{claw_id}.{namespace}.svc.cluster.local:3000"
    # 过滤掉 sharinmod-ow-token
    if "cookie" in request.headers:
        filtered_cookie = _filter_cookie_header(request.headers["cookie"], _OW_COOKIE_NAME)
        if filtered_cookie:
            fwd_headers["cookie"] = filtered_cookie

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
            async for chunk in upstream_resp.aiter_raw():
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


@router.api_route(
    "/{claw_id}/openclaw-web/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def proxy_openclaw_web(
    claw_id: int,
    path: str,
    request: Request,
    current_user: User = Depends(_get_openclaw_web_user),
    session: Session = Depends(get_db),
):
    """
    将 openclaw-web 请求代理到对应 pod 的 3000 端口。
    ownership check 确保用户只能访问自己的龙虾。
    """
    claw = get_user_claw_by_id(session, current_user.id, claw_id)
    namespace = claw.k8s_namespace or "default"
    if not _K8S_NS_RE.match(namespace):
        raise HTTPException(status_code=500, detail="Invalid namespace in claw record")

    # Pod headless DNS: {pod-name}.{svc-name}.{namespace}.svc.cluster.local
    target_base = (
        f"http://claw-{claw_id}-0.claw-{claw_id}.{namespace}.svc.cluster.local:3000"
        f"/api/claws/{claw_id}/openclaw-web/{path}"
    )
    if request.query_params:
        target_base += f"?{request.query_params}"

    # 过滤 hop-by-hop headers
    fwd_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP_HEADERS and k.lower() != "host"
    }
    # 重写 Host 为目标地址
    fwd_headers["host"] = f"claw-{claw_id}-0.claw-{claw_id}.{namespace}.svc.cluster.local:3000"
    # 重写 Origin 为目标地址
    if "origin" in fwd_headers:
        fwd_headers["origin"] = f"http://claw-{claw_id}-0.claw-{claw_id}.{namespace}.svc.cluster.local:3000"
    # 过滤掉 sharinmod-ow-token
    if "cookie" in request.headers:
        filtered_cookie = _filter_cookie_header(request.headers["cookie"], _OW_COOKIE_NAME)
        if filtered_cookie:
            fwd_headers["cookie"] = filtered_cookie

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
            async for chunk in upstream_resp.aiter_raw():
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


@router.websocket("/{claw_id}/openclaw-web")
@router.websocket("/{claw_id}/openclaw-web/")
@router.websocket("/{claw_id}/openclaw-web/{path:path}")
async def proxy_openclaw_web_ws(
    websocket: WebSocket,
    claw_id: int,
    path: str = "",
    session: Session = Depends(get_db),
):
    """
    WebSocket 代理到 openclaw-web。
    认证方式：通过 query 参数 token 传递 jwt
    """
    # 验证 token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    email = verify_token(token)
    if email is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    user = get_user_by_email(session, email)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # ownership check
    claw = get_user_claw_by_id(session, user.id, claw_id)
    namespace = claw.k8s_namespace or "default"
    if not _K8S_NS_RE.match(namespace):
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    await websocket.accept()

    # 构建 WebSocket 目标 URL
    target_path = f"/api/claws/{claw_id}/openclaw-web/{path}".rstrip("/")
    query_params = [
        (k, v) for k, v in websocket.query_params.items() if k != "token"
    ]
    query_string = "&".join(f"{k}={v}" for k, v in query_params) if query_params else ""

    target_url = (
        f"ws://claw-{claw_id}-0.claw-{claw_id}.{namespace}.svc.cluster.local:3000"
        f"{target_path}"
    )
    if query_string:
        target_url += f"?{query_string}"

    async with websockets.connect(target_url) as ws:
        # 双向转发
        async def forward_client_to_server():
            try:
                while True:
                    data = await websocket.receive_text()
                    await ws.send(data)
            except Exception:
                pass

        async def forward_server_to_client():
            try:
                while True:
                    data = await ws.recv()
                    await websocket.send_text(data)
            except Exception:
                pass

        await asyncio.gather(
            forward_client_to_server(),
            forward_server_to_client(),
        )

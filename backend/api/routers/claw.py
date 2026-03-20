"""
REST API endpoints for Claw (QQ bot) management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from typing import List

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
        for line in k8s_service.stream_statefulset_logs(claw.k8s_deployment_name, namespace=settings.K8S_NAMESPACE):
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

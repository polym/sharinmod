"""
Service layer for Claw management
"""
import logging
import os
from datetime import datetime
from typing import List

from fastapi import HTTPException
from sqlmodel import Session, select

from api.models.claw import Claw, ClawStatus
from api.models.user import User
from api.schemas.claw import ClawCreate, ClawUpdate
from api.services import k8s_service
from api.config import settings

logger = logging.getLogger(__name__)


def _load_claw_type_config(claw_type: str) -> dict:
    """Load image, model_id and config_template from config.yaml for given claw_type."""
    import yaml
    from api.config import _get_config_path
    config_path = _get_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config["claw_types"][claw_type]


MAX_CLAWS_PER_USER = 10


def count_user_claws(session: Session, user_id: int) -> int:
    """Count total claws owned by a user."""
    statement = select(Claw).where(Claw.user_id == user_id)
    return len(session.exec(statement).all())


def get_user_claws(session: Session, user_id: int) -> List[Claw]:
    """Return all claws for a user, ordered by creation date (newest first)."""
    statement = select(Claw).where(Claw.user_id == user_id).order_by(Claw.created_at.desc())
    return session.exec(statement).all()


def get_user_claw_by_id(session: Session, user_id: int, claw_id: int) -> Claw:
    """Return a specific claw owned by the user, or raise 404."""
    statement = select(Claw).where(Claw.id == claw_id, Claw.user_id == user_id)
    claw = session.exec(statement).first()
    if not claw:
        raise HTTPException(status_code=404, detail="Claw not found")
    return claw


async def create_claw_async(session: Session, current_user: User, data: ClawCreate) -> Claw:
    """
    Create a new Claw:
    1. Check feature flag
    2. Check quota (max 10 per user)
    3. Auto-create API Key with claw name
    4. Persist a PENDING record to obtain the ID
    5. Build IMAGE, COMMAND and CONFIG_FILES dict from config.yaml
    6. Create K8s ConfigMap (all files mounted at /config) + Deployment
    7. Update record with deployment name and RUNNING status
    If any step fails, rollback everything.
    """
    # 检查功能开关
    if not settings.FEATURE_FLAG_ENABLE_CLAW_CREATION:
        logger.warning(f"[FEATURE_FLAGS] Claw creation attempt blocked for user {current_user.id} (feature disabled)")
        raise HTTPException(
            status_code=403,
            detail="Claw creation is disabled by administrator"
        )

    logger.info(f"[FEATURE_FLAGS] Claw creation attempt for user {current_user.id} (feature enabled)")

    if count_user_claws(session, current_user.id) >= MAX_CLAWS_PER_USER:
        raise HTTPException(
            status_code=400,
            detail=f"每用户最多 {MAX_CLAWS_PER_USER} 只龙虾"
        )

    # Auto-create API Key with claw name
    from api.services.unified_api_key_service import (
        create_unified_api_key_async,
        block_unified_api_key_async,
        delete_unified_api_key_async
    )

    api_key_obj = None
    try:
        api_key_obj = await create_unified_api_key_async(
            session=session,
            user=current_user,
            api_key_name=data.name,  # 使用龙虾名字作为 API Key 名称
            description=f"Auto-created for claw: {data.name}",
            is_auto_created=True  # 标记为自动创建，不占用配额
        )
    except HTTPException as e:
        raise HTTPException(
            status_code=400,
            detail=f"创建 API Key 失败: {e.detail}"
        )

    # Persist initial record to get an auto-increment ID
    claw = Claw(
        user_id=current_user.id,
        name=data.name,
        type=data.type,
        qq_bot_id=data.qq_bot_id,
        qq_bot_secret=data.qq_bot_secret,
        unified_api_key_id=api_key_obj.id,  # 关联自动创建的 API Key
        brain_model=data.brain_model,
        chat_tool=data.chat_tool,
        k8s_namespace=settings.K8S_NAMESPACE,
        status=ClawStatus.PENDING,
    )
    session.add(claw)
    session.commit()
    session.refresh(claw)

    # Build IMAGE, COMMAND and CONFIG_FILES from config.yaml
    type_config = _load_claw_type_config(claw.type.value)
    image = type_config["image"]
    model_id = data.brain_model if data.brain_model else type_config["model_id"]
    command = type_config.get("command")
    config_template = type_config["config_template"]  # dict[str, str]
    openai_base_url = settings.WEBSITE_BASE_URL + "/api/openai"
    config_files = {
        filename: (
            content
            .replace("{{MODEL_ID}}", model_id)
            .replace("{{OPENAI_KEY}}", api_key_obj.litellm_key or "")
            .replace("{{OPENAI_BASE_URL}}", openai_base_url)
            .replace("{{YOUR_APP_ID}}", claw.qq_bot_id)
            .replace("{{YOUR_APP_SECRET}}", claw.qq_bot_secret)
        )
        for filename, content in config_template.items()
    }

    # Create K8s StatefulSet
    try:
        deployment_name = k8s_service.create_statefulset(
            claw_id=claw.id,
            image=image,
            config_files=config_files,
            command=command,
            user_email=current_user.email or "",
            namespace=settings.K8S_NAMESPACE,
        )
    except Exception as e:
        logger.error(f"Failed to create K8s statefulset for claw {claw.id}: {e}")
        # Roll back: 删除已创建的 API Key 和数据库记录
        try:
            await block_unified_api_key_async(session, current_user, api_key_obj.id)
            await delete_unified_api_key_async(session, current_user, api_key_obj.id)
        except Exception as delete_err:
            logger.error(f"Failed to rollback API key for claw {claw.id}: {delete_err}")
        session.delete(claw)
        session.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create K8s StatefulSet: {str(e)}"
        )

    # Update with deployment name and running status
    claw.k8s_deployment_name = deployment_name
    claw.status = ClawStatus.RUNNING
    claw.updated_at = datetime.utcnow()
    session.add(claw)
    session.commit()
    session.refresh(claw)
    return claw


def update_claw_name(session: Session, user_id: int, claw_id: int, data: ClawUpdate) -> Claw:
    """Update the name of a claw."""
    claw = get_user_claw_by_id(session, user_id, claw_id)
    claw.name = data.name
    claw.updated_at = datetime.utcnow()
    session.add(claw)
    session.commit()
    session.refresh(claw)
    return claw


async def delete_claw_async(session: Session, user_id: int, claw_id: int) -> None:
    """
    Delete a Claw:
    1. Delete the associated API Key
    2. Delete the K8s Deployment (404 is ignored)
    3. Delete the database record
    """
    claw = get_user_claw_by_id(session, user_id, claw_id)

    # Delete associated API Key first.
    # Important: null out the FK reference on claw BEFORE deleting the UnifiedAPIKey row,
    # otherwise the DELETE on unified_api_keys will fail with a FK violation because
    # claws.unified_api_key_id still points to it.
    api_key_id = claw.unified_api_key_id
    if api_key_id:
        claw.unified_api_key_id = None
        session.add(claw)
        session.commit()

        from api.services.unified_api_key_service import delete_unified_api_key_async
        user_stmt = select(User).where(User.id == user_id)
        current_user = session.exec(user_stmt).first()

        try:
            # 直接删除 API Key（不再需要先 block）
            await delete_unified_api_key_async(
                session=session,
                user=current_user,
                api_key_id=api_key_id
            )
        except Exception as e:
            logger.error(f"Error deleting API key for claw {claw.id}: {e}")
            session.rollback()  # 确保 session 处于干净状态，不阻止龙虾删除

    # Delete K8s StatefulSet
    if claw.k8s_deployment_name:
        try:
            k8s_service.delete_statefulset(claw.k8s_deployment_name, namespace=claw.k8s_namespace or "default")
        except Exception as e:
            # Log but do not block deletion of the database record
            logger.error(f"Error deleting K8s statefulset {claw.k8s_deployment_name}: {e}")

    session.delete(claw)
    session.commit()

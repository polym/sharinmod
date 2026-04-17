"""
Organization API routes for managing private workspaces
"""
import uuid
import httpx
import json
import urllib.parse
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from api.config import settings
from api.database import get_db
from api.dependencies.auth import get_current_user
from api.models.organization import Organization
from api.models.organization_invite import OrganizationInvite
from api.models.organization_member import OrganizationMember
from api.models.api_key_limit_history import APIKeyLimitHistory
from api.models.shared_api_key import SharedAPIKey
from api.models.unified_api_key import UnifiedAPIKey
from api.models.usage_log import UsageLog
from api.models.user import User
from api.schemas.organization import (
    MyOrganizationsResponse,
    OrgInviteInfoResponse,
    OrgInviteResponse,
    OrgMemberListResponse,
    OrgMemberStats,
    OrganizationCreate,
    OrganizationMemberResponse,
    OrganizationResponse,
    OrganizationSettingsResponse,
    OrganizationSettingsUpdate,
    generate_slug,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


def org_to_response(organization: Organization) -> OrganizationResponse:
    """Convert Organization model to OrganizationResponse"""
    return OrganizationResponse(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        created_at=organization.created_at,
        updated_at=organization.updated_at,
        is_personal=organization.is_personal,
    )


def _require_org_owner(org_id: int, current_user: User, db: Session) -> Organization:
    """Verify that current_user is the owner of org_id and return the organization."""
    organization = db.get(Organization, org_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="组织不存在")
    membership = db.exec(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.role == "owner",
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限操作此组织")
    return organization


def _toggle_user_org_keys(db: Session, user_id: int, org_id: int, block: bool) -> None:
    """Block or unblock all LiteLLM unified API keys for a user within an organization.

    When unblocking, skips keys with status=REVOKED to avoid resurrecting intentionally deleted keys.
    Also skips keys with empty litellm_key values.
    """
    from api.models.unified_api_key import UnifiedAPIKey, UnifiedAPIKeyStatus
    from api.services.unified_api_key_service import sync_block_litellm_key, sync_unlock_litellm_key

    conditions = [
        UnifiedAPIKey.user_id == user_id,
        UnifiedAPIKey.organization_id == org_id,
        UnifiedAPIKey.litellm_key.isnot(None),
        UnifiedAPIKey.litellm_key != "",
    ]
    if not block:
        # Never unblock keys that were explicitly revoked
        conditions.append(UnifiedAPIKey.status != UnifiedAPIKeyStatus.REVOKED)

    keys = db.exec(select(UnifiedAPIKey).where(*conditions)).all()
    action = sync_block_litellm_key if block else sync_unlock_litellm_key
    action_name = "block" if block else "unblock"
    for key in keys:
        try:
            action(key.litellm_key)
        except Exception as e:
            logger.error(f"Failed to {action_name} LiteLLM key for user {user_id} in org {org_id}: {e}")


@router.post("", status_code=status.HTTP_410_GONE)
def create_organization(
    organization_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create organization endpoint - disabled, system auto-creates personal org"""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="该功能已停用，系统将自动为您创建个人工作区"
    )


@router.get("/my", response_model=MyOrganizationsResponse)
def get_my_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all organizations related to the current user

    Returns organizations where user is owner or member.
    """
    memberships = db.exec(
        select(OrganizationMember).where(
            OrganizationMember.user_id == current_user.id
        )
    ).all()

    owned = []
    joined = []

    for membership in memberships:
        if membership.role != "owner" and membership.is_disabled:
            continue
        organization = db.get(Organization, membership.organization_id)
        if organization:
            org_response = org_to_response(organization)
            if membership.role == "owner":
                owned.append(org_response)
            else:
                joined.append(org_response)

    return MyOrganizationsResponse(owned=owned, joined=joined)


# --- Invite endpoints (no auth required for GET) ---

@router.get("/invite/{token}", response_model=OrgInviteInfoResponse)
def get_invite_info(token: str, db: Session = Depends(get_db)):
    """Get invite link preview info (public endpoint)"""
    invite = db.exec(
        select(OrganizationInvite).where(OrganizationInvite.token == token)
    ).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="邀请链接不存在")

    organization = db.get(Organization, invite.organization_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="组织不存在")

    # Get inviter email (handle case where inviter was deleted)
    inviter = db.get(User, invite.created_by_user_id)
    inviter_email = inviter.email if inviter else None

    now = datetime.now(timezone.utc)
    expires_at = invite.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    is_valid = invite.used_at is None and expires_at > now
    return OrgInviteInfoResponse(
        organization_name=organization.name,
        organization_slug=organization.slug,
        expires_at=invite.expires_at,
        is_valid=is_valid,
        inviter_email=inviter_email,
    )


@router.post("/invite/{token}/accept", response_model=OrganizationResponse)
def accept_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept an organization invite (auth required)"""
    # S-1: Lock the invite row to prevent concurrent double-accept race condition
    invite = db.exec(
        select(OrganizationInvite).where(OrganizationInvite.token == token).with_for_update()
    ).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="邀请链接不存在")

    now = datetime.now(timezone.utc)
    expires_at = invite.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if invite.used_at is not None or expires_at <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邀请链接已失效或已被使用")

    # B-4: Verify org exists before staging any session mutations
    organization = db.get(Organization, invite.organization_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="组织不存在")

    # Check if user already is a member of any org
    existing_member = db.exec(
        select(OrganizationMember).where(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.role == "member",
        )
    ).first()
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已加入私服，每个用户只能加入一个私服"
        )

    # Check if user is already in this specific org (e.g. the owner trying to join)
    already_in_org = db.exec(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == invite.organization_id,
            OrganizationMember.user_id == current_user.id,
        )
    ).first()
    if already_in_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已是该组织成员"
        )

    # Create membership and mark invite as used
    membership = OrganizationMember(
        organization_id=invite.organization_id,
        user_id=current_user.id,
        role="member",
    )
    db.add(membership)

    invite.used_at = now
    invite.used_by_user_id = current_user.id
    db.add(invite)

    try:
        db.commit()
    except IntegrityError:
        # B-2: Concurrent double-submit by the same user hits the unique constraint
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已加入私服，每个用户只能加入一个私服"
        )

    logger.info(f"User {current_user.id} accepted invite {token} to org {invite.organization_id}")
    return org_to_response(organization)


# --- Member management endpoints (org owner required) ---

@router.get("/{org_id}/members", response_model=OrgMemberListResponse)
def list_org_members(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all members of an organization with usage stats (org owner only)"""
    _require_org_owner(org_id, current_user, db)

    members = db.exec(
        select(OrganizationMember).where(OrganizationMember.organization_id == org_id)
    ).all()

    result = []
    for m in members:
        user = db.get(User, m.user_id)
        if not user:
            continue

        total_tokens = db.exec(
            select(func.sum(UsageLog.total_tokens)).where(
                UsageLog.user_id == m.user_id,
                UsageLog.organization_id == org_id,
            )
        ).one() or 0

        last_used_at = db.exec(
            select(func.max(UsageLog.created_at)).where(
                UsageLog.user_id == m.user_id,
                UsageLog.organization_id == org_id,
            )
        ).one()

        result.append(OrgMemberStats(
            user_id=user.id,
            email=user.email,
            name=user.name,
            role=m.role,
            is_disabled=m.is_disabled,
            org_total_tokens=total_tokens,
            last_used_at=last_used_at,
            joined_at=m.created_at,
        ))

    return OrgMemberListResponse(items=result)


@router.put("/{org_id}/members/{user_id}/disable")
def disable_org_member(
    org_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable an org member (org owner only)"""
    _require_org_owner(org_id, current_user, db)

    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能禁用自己")

    member = db.exec(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.role == "member",
        )
    ).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在")

    member.is_disabled = True
    db.add(member)
    db.commit()

    # Block all the member's unified API keys in LiteLLM so they can't be used
    _toggle_user_org_keys(db, user_id, org_id, block=True)

    return {"message": "成员已禁用"}


@router.put("/{org_id}/members/{user_id}/enable")
def enable_org_member(
    org_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable an org member (org owner only)"""
    _require_org_owner(org_id, current_user, db)

    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能操作自己")

    member = db.exec(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.role == "member",
        )
    ).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在")

    member.is_disabled = False
    db.add(member)
    db.commit()

    # Unblock all the member's unified API keys in LiteLLM
    _toggle_user_org_keys(db, user_id, org_id, block=False)

    return {"message": "成员已启用"}


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_org_member(
    org_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a member from the organization (org owner only, hard delete)"""
    _require_org_owner(org_id, current_user, db)

    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能移除自己")

    member = db.exec(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.role == "member",
        )
    ).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在")

    db.delete(member)
    db.commit()


@router.post("/{org_id}/invite", response_model=OrgInviteResponse)
def create_invite(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate an invite link for an organization (org owner only)"""
    organization = _require_org_owner(org_id, current_user, db)

    if organization.is_personal:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="个人组织不支持邀请成员")

    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    invite = OrganizationInvite(
        organization_id=org_id,
        token=token,
        created_by_user_id=current_user.id,
        expires_at=expires_at,
    )
    db.add(invite)
    db.commit()

    logger.info(f"Invite created for org {org_id} by user {current_user.id}")
    return OrgInviteResponse(token=token, expires_at=expires_at)


@router.get("/{org_id}/settings", response_model=OrganizationSettingsResponse)
def get_org_settings(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get organization settings (org owner only)"""
    organization = _require_org_owner(org_id, current_user, db)
    return OrganizationSettingsResponse(
        id=organization.id,
        name=organization.name,
        default_daily_token=organization.default_daily_token_limit
    )


@router.put("/{org_id}/settings", response_model=OrganizationSettingsResponse)
def update_org_settings(
    org_id: int,
    settings_data: OrganizationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update organization settings (org owner only)"""
    organization = _require_org_owner(org_id, current_user, db)
    organization.default_daily_token_limit = settings_data.default_daily_token
    organization.updated_at = datetime.now(timezone.utc)
    db.add(organization)
    db.commit()
    db.refresh(organization)

    logger.info(f"Organization {org_id} settings updated by user {current_user.id}")
    return OrganizationSettingsResponse(
        id=organization.id,
        name=organization.name,
        default_daily_token=organization.default_daily_token_limit
    )


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def destroy_organization(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Destroy an organization and clean up all associated resources (org owner only).

    NOTE: Uses async def to await LiteLLM HTTP calls. The synchronous DB session
    is a known project-wide pattern (FastAPI supports async routes + sync Sessions).

    Cleanup order: LiteLLM resources first, then DB records. DB commit is last.
    If the server crashes mid-way, LiteLLM resources may be orphaned but the DB
    records remain intact (the org still "exists"), which is safer than the reverse.
    """
    # F9 fix: reuse org returned by _require_org_owner instead of fetching twice
    organization = _require_org_owner(org_id, current_user, db)

    # Prevent deletion of personal organizations
    if organization.is_personal:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="个人组织不允许删除"
        )

    # --- Step 1: LiteLLM cleanup for SharedAPIKeys ---
    shared_keys = db.exec(
        select(SharedAPIKey).where(SharedAPIKey.organization_id == org_id)
    ).all()

    # F8 fix: single httpx client for ALL LiteLLM calls (shared + unified keys)
    async with httpx.AsyncClient(timeout=10.0) as client:
        for key in shared_keys:
            try:
                owner = db.get(User, key.user_id)
                if not owner:
                    # F6 fix: skip credential deletion if owner was already deleted
                    logger.warning(
                        f"[DESTROY] Owner user {key.user_id} not found for shared key {key.id}; "
                        "skipping LiteLLM credential cleanup"
                    )
                else:
                    credential_name = f"{key.provider}/{owner.email}/org-{org_id}"

                    # Delete litellm models first (must precede credential deletion)
                    model_ids: dict = {}
                    if key.litellm_model_ids:
                        try:
                            parsed = json.loads(key.litellm_model_ids)
                            # F5 fix: guard against non-dict JSON (list, string, etc.)
                            if isinstance(parsed, dict):
                                model_ids = parsed
                            else:
                                logger.warning(
                                    f"[DESTROY] litellm_model_ids for shared key {key.id} "
                                    f"is not a dict (got {type(parsed).__name__}), skipping"
                                )
                        except json.JSONDecodeError:
                            logger.warning(f"[DESTROY] Failed to parse litellm_model_ids for shared key {key.id}")

                    for model_name, litellm_model_id in model_ids.items():
                        try:
                            resp = await client.post(
                                f"{settings.LITELLM_BASE_URL}/model/delete",
                                json={"id": litellm_model_id},
                                headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                            )
                            # F4 fix: log non-2xx responses as warnings
                            if resp.status_code < 200 or resp.status_code >= 300:
                                logger.warning(
                                    f"[DESTROY] Delete model '{model_name}' returned {resp.status_code}: {resp.text}"
                                )
                            else:
                                logger.info(f"[DESTROY] Deleted model '{model_name}' (org {org_id})")
                        except Exception as e:
                            logger.error(f"[DESTROY] Failed to delete model '{model_name}': {e}")

                    # Handle legacy single litellm_model_id
                    if key.litellm_model_id and key.litellm_model_id not in model_ids.values():
                        try:
                            resp = await client.post(
                                f"{settings.LITELLM_BASE_URL}/model/delete",
                                json={"id": key.litellm_model_id},
                                headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                            )
                            if resp.status_code < 200 or resp.status_code >= 300:
                                logger.warning(
                                    f"[DESTROY] Delete legacy model returned {resp.status_code}: {resp.text}"
                                )
                            else:
                                logger.info(f"[DESTROY] Deleted legacy model for shared key {key.id}")
                        except Exception as e:
                            logger.error(f"[DESTROY] Failed to delete legacy model: {e}")

                    # Delete credential
                    try:
                        encoded_name = urllib.parse.quote(credential_name, safe="/")
                        resp = await client.delete(
                            f"{settings.LITELLM_BASE_URL}/credentials/{encoded_name}",
                            headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                        )
                        if resp.status_code < 200 or resp.status_code >= 300:
                            logger.warning(
                                f"[DESTROY] Delete credential '{credential_name}' returned {resp.status_code}: {resp.text}"
                            )
                        else:
                            logger.info(f"[DESTROY] Deleted credential '{credential_name}'")
                    except Exception as e:
                        logger.error(f"[DESTROY] Failed to delete credential '{credential_name}': {e}")

            except Exception as e:
                logger.error(f"[DESTROY] Unexpected error cleaning up shared key {key.id}: {e}")

        # --- Step 2: LiteLLM cleanup for UnifiedAPIKeys ---
        # F8 fix: inline deletion using the outer client instead of creating a new one
        unified_keys = db.exec(
            select(UnifiedAPIKey).where(UnifiedAPIKey.organization_id == org_id)
        ).all()

        for key in unified_keys:
            if key.litellm_key:
                try:
                    resp = await client.post(
                        f"{settings.LITELLM_BASE_URL}/key/delete",
                        json={"keys": [key.litellm_key]},
                        headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"}
                    )
                    if resp.status_code < 200 or resp.status_code >= 300:
                        logger.warning(
                            f"[DESTROY] Delete unified key {key.id} returned {resp.status_code}: {resp.text}"
                        )
                    else:
                        logger.info(f"[DESTROY] Deleted LiteLLM unified key for user {key.user_id}")
                except Exception as e:
                    logger.error(f"[DESTROY] Failed to delete LiteLLM unified key {key.id}: {e}")

    # F10 fix: all DB operations outside the httpx context manager
    # --- Step 3: Delete SharedAPIKey DB records ---
    for key in shared_keys:
        db.delete(key)

    # --- Step 4: Null usage_logs.unified_api_key_id and delete UnifiedAPIKey records ---
    for key in unified_keys:
        db.exec(
            update(UsageLog)
            .where(UsageLog.unified_api_key_id == key.id)
            .values(unified_api_key_id=None)
        )
        # Delete api_key_limit_history records first (NOT NULL FK, no DB cascade)
        limit_history_records = db.exec(
            select(APIKeyLimitHistory).where(APIKeyLimitHistory.unified_api_key_id == key.id)
        ).all()
        for record in limit_history_records:
            db.delete(record)
        db.delete(key)

    # --- Step 5: Null usage_logs.organization_id ---
    db.exec(
        update(UsageLog)
        .where(UsageLog.organization_id == org_id)
        .values(organization_id=None)
    )

    # --- Step 6: Delete Organization (CASCADE cleans members, invites, subscriptions) ---
    # F9 fix: reuse org fetched earlier, no second db.get()
    db.delete(organization)
    db.commit()
    logger.info(f"Organization {org_id} destroyed by user {current_user.id}")


@router.post("/{organization_id}/join", status_code=status.HTTP_200_OK)
def join_organization(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Join an existing organization (reserved for future implementation)

    Raises:
        HTTPException 501: Use invite link instead
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="加入私服功能需要邀请链接，请通过邀请链接加入"
    )

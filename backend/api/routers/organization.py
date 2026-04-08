"""
Organization API routes for managing private workspaces
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from api.database import get_db
from api.dependencies.auth import get_current_user
from api.models.organization import Organization
from api.models.organization_invite import OrganizationInvite
from api.models.organization_member import OrganizationMember
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
        updated_at=organization.updated_at
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


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    organization_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new organization for the current user

    Args:
        organization_data: Organization name
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created organization

    Raises:
        HTTPException 400: User already owns an organization
        HTTPException 400: Organization name (slug) already exists
    """
    # Check if user already owns an organization
    existing_owner = db.exec(
        select(OrganizationMember).where(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.role == "owner"
        )
    ).first()

    if existing_owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已创建私服，每个用户只能创建一个私服"
        )

    # Generate slug from name
    slug = generate_slug(organization_data.name)

    # Check if slug already exists
    existing_org = db.exec(
        select(Organization).where(Organization.slug == slug)
    ).first()

    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="组织名称已被使用"
        )

    # Create organization
    organization = Organization(
        name=organization_data.name,
        slug=slug
    )
    db.add(organization)
    db.commit()
    db.refresh(organization)

    # Create owner membership
    membership = OrganizationMember(
        organization_id=organization.id,
        user_id=current_user.id,
        role="owner"
    )
    db.add(membership)
    db.commit()

    logger.info(f"Organization created: {organization.id} ({organization.slug}) by user {current_user.id}")

    return org_to_response(organization)


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

    # Check if user already owns an org
    existing_owner = db.exec(
        select(OrganizationMember).where(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.role == "owner",
        )
    ).first()
    if existing_owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已拥有私服，无法加入其他私服"
        )

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
    _require_org_owner(org_id, current_user, db)

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

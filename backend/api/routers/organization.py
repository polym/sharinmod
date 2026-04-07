"""
Organization API routes for managing private workspaces
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from api.database import get_db
from api.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationMemberResponse,
    MyOrganizationsResponse,
    generate_slug
)
from api.models.organization import Organization
from api.models.organization_member import OrganizationMember
from api.models.user import User
from api.dependencies.auth import get_current_user
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

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of owned and joined organizations
    """
    # Get user's memberships
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


@router.post("/{organization_id}/join", status_code=status.HTTP_200_OK)
def join_organization(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Join an existing organization (reserved for future implementation)

    Args:
        organization_id: ID of the organization to join
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException 404: Organization not found
        HTTPException 400: User already joined an organization as member
    """
    # Check if organization exists
    organization = db.get(Organization, organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组织不存在"
        )

    # Check if user already joined as member
    existing_member = db.exec(
        select(OrganizationMember).where(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.role == "member"
        )
    ).first()

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已加入私服，每个用户只能加入一个私服"
        )

    # Create membership (currently disabled - needs invitation logic)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="加入私服功能暂未实现，需要邀请机制"
    )
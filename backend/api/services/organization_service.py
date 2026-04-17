"""
Organization service: utility functions for organization management
"""
import re
from datetime import datetime, timezone
from sqlmodel import Session, select

from api.models.organization import Organization
from api.models.organization_member import OrganizationMember
from api.models.user import User


def _sanitize_slug(text: str) -> str:
    """Convert text to URL-safe slug component (ASCII only, consistent with migration SQL)."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-') or 'user'


def create_personal_organization(db: Session, user: User) -> Organization:
    """Auto-create a personal org for user after registration.

    Idempotent: returns existing personal org if one already exists.
    Always uses slug-{user_id} form for guaranteed uniqueness without a race condition.
    """
    # Idempotency guard: return early if user already owns a personal org
    existing_membership = db.exec(
        select(OrganizationMember).where(
            OrganizationMember.user_id == user.id,
            OrganizationMember.role == "owner",
        )
    ).first()
    if existing_membership:
        existing_org = db.get(Organization, existing_membership.organization_id)
        if existing_org and existing_org.is_personal:
            return existing_org

    base_name = user.name or user.email.split('@')[0]
    org_name = f"{base_name}的个人工作区"
    # Always include user_id in slug for guaranteed global uniqueness (no SELECT-then-INSERT race)
    slug = _sanitize_slug(base_name) + f'-personal-{user.id}'

    org = Organization(
        name=org_name,
        slug=slug,
        is_personal=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(org)
    db.flush()  # Get org.id without committing

    membership = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role="owner",
    )
    db.add(membership)
    db.commit()
    db.refresh(org)
    return org

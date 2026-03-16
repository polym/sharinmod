"""
REST API endpoints for Claw (QQ bot) management
"""
from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from api.database import get_db
from api.dependencies.auth import get_current_user
from api.models.user import User
from api.schemas.claw import ClawCreate, ClawResponse, ClawUpdate, ClawList
from api.services.claw_service import (
    create_claw_async,
    get_user_claws,
    update_claw_name,
    delete_claw_async,
)

router = APIRouter(prefix="/api/claws", tags=["claws"])


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
    Delete a claw and its K8s Deployment

    - Deletes K8s Deployment first (ignores 404)
    - Then deletes database record
    - Returns 204 No Content
    """
    await delete_claw_async(session, current_user.id, claw_id)

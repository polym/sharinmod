from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from api.database import get_db
from api.dependencies.auth import get_current_user
from api.models.user import User
from api.schemas.token_discovery import TokenDiscoveryList
from api.services.token_discovery_service import get_available_tokens

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


@router.get("/discover", response_model=TokenDiscoveryList)
def discover_available_tokens(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Discover available shared tokens on the platform
    
    Returns list of shared tokens from other users that are available for consumption
    Excludes your own shared tokens
    Only shows active tokens
    
    Requires JWT authentication
    
    Response includes:
    - Vendor information (bigmodel, z.ai)
    - Provider username (anonymized - email prefix only)
    - Sharing duration (days since shared)
    - Usage statistics (total uses)
    
    Does NOT include:
    - Actual token values (security)
    - Provider's full email or personal information
    """
    items, total = get_available_tokens(db, current_user.id, page, page_size)
    
    return TokenDiscoveryList(
        page=page,
        page_size=page_size,
        total=total,
        items=items
    )

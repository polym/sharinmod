from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from api.database import get_db
from api.dependencies.auth import get_current_user
from api.models.user import User
from api.schemas.api_key_discovery import APIKeyDiscoveryList
from api.services.api_key_discovery_service import get_available_api_keys

router = APIRouter(prefix="/api/api-keys", tags=["api-keys"])


@router.get("/discover", response_model=APIKeyDiscoveryList)
def discover_available_api_keys(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Discover available shared API keys on the platform
    
    Returns list of shared API keys from other users that are available for consumption
    Excludes your own shared API keys
    Only shows active API keys
    
    Requires JWT authentication
    
    Response includes:
    - Provider information (bigmodel, z.ai)
    - Provider username (anonymized - email prefix only)
    - Sharing duration (days since shared)
    - Usage statistics (total uses)
    
    Does NOT include:
    - Actual API key values (security)
    - Provider's full email or personal information
    """
    items, total = get_available_api_keys(db, current_user.id, page, page_size)
    
    return APIKeyDiscoveryList(
        page=page,
        page_size=page_size,
        total=total,
        items=items
    )

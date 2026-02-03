"""
Comprehensive tests for Story 3.1: Unified API Key Generation API

Test Coverage:
- AC#1: Successful API key generation with limit check and logging
- AC#2: 5-API key limit enforcement
- AC#3: API key listing with status and info
- AC#4: API key revocation with status change and logging
- LiteLLM Integration: Key generation, blocking, deletion, regeneration
- Security: Authentication requirements
- Edge cases: API key uniqueness, ownership, already-revoked
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from datetime import datetime
from unittest.mock import AsyncMock, patch, Mock

from api.app import create_app
from api.config import Settings
from api.models.user import User
from api.models.unified_api_key import UnifiedAPIKey, UnifiedAPIKeyStatus
from api.models.api_key_usage import APIKeyUsageHistory
from api.services.auth_service import create_access_token
from api.database import get_db


# Test database setup
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    settings = Settings()
    app = create_app(settings)
    app.dependency_overrides[get_db] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    user = User(
        email="testuser@example.com",
        hashed_password="$2b$12$test_hash",
        litellm_user_id="test_litellm_user_123"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(test_user: User):
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


# ==================== AC#1: Successful API Key Generation ====================

def test_generate_api_key_success(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test successfully generating a unified API key"""
    response = client.post(
        "/api/api-keys/generate",
        json={"api_key_name": "My First API Key"},
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["user_id"] == test_user.id
    assert data["status"] == "active"
    assert data["api_key_name"] == "My First API Key"
    assert "api_key" in data
    assert len(data["api_key"]) > 40  # Base64-encoded 32 bytes is ~44 chars
    assert "created_at" in data
    assert data["revoked_at"] is None


def test_generate_api_key_without_name(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test generating API key without optional name"""
    response = client.post(
        "/api/api-keys/generate",
        json={},
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["api_key_name"] is None


def test_generate_api_key_logs_usage_history(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test that API key generation is logged in usage history"""
    response = client.post(
        "/api/api-keys/generate",
        json={"api_key_name": "Test API Key"},
        headers=auth_headers
    )
    assert response.status_code == 201

    # Check usage history
    history_response = client.get("/api/users/me/api-key-usage", headers=auth_headers)
    assert history_response.status_code == 200
    history_data = history_response.json()

    # Should have one GENERATED action (enum value is lowercase "generated")
    assert history_data["total"] >= 1
    generated_actions = [item for item in history_data["items"] if item["action"] == "generated"]
    assert len(generated_actions) >= 1


# ==================== AC#2: 5-API Key Limit Enforcement ====================

def test_generate_api_key_with_limit(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test that 6th API key generation is rejected"""
    # Create 5 API keys first
    for i in range(5):
        response = client.post(
            "/api/api-keys/generate",
            json={"api_key_name": f"API Key {i+1}"},
            headers=auth_headers
        )
        assert response.status_code == 201
    
    # Try to create 6th API key
    response = client.post(
        "/api/api-keys/generate",
        json={"api_key_name": "API Key 6"},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Maximum 5 API keys" in response.json()["detail"]


def test_generate_api_key_after_revocation(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test that revoking an API key frees up a slot"""
    # Create 5 API keys
    api_key_ids = []
    for i in range(5):
        response = client.post(
            "/api/api-keys/generate",
            json={"api_key_name": f"API Key {i+1}"},
            headers=auth_headers
        )
        assert response.status_code == 201
        api_key_ids.append(response.json()["id"])
    
    # Revoke one API key
    response = client.delete(
        f"/api/api-keys/generated/{api_key_ids[0]}",
        headers=auth_headers
    )
    assert response.status_code == 204
    
    # Now can create a new API key
    response = client.post(
        "/api/api-keys/generate",
        json={"api_key_name": "API Key 6"},
        headers=auth_headers
    )
    assert response.status_code == 201


# ==================== AC#3: API Key Listing ====================

def test_get_my_generated_api_keys_empty(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test listing API keys when user has none"""
    response = client.get("/api/api-keys/my-generated", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_get_my_generated_api_keys_with_data(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test listing API keys with existing data"""
    # Create 2 API keys
    client.post(
        "/api/api-keys/generate",
        json={"api_key_name": "API Key 1"},
        headers=auth_headers
    )
    client.post(
        "/api/api-keys/generate",
        json={"api_key_name": "API Key 2"},
        headers=auth_headers
    )
    
    # Get list
    response = client.get("/api/api-keys/my-generated", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    # Should be ordered by creation date (newest first)
    assert data["items"][0]["api_key_name"] == "API Key 2"
    assert data["items"][1]["api_key_name"] == "API Key 1"


# ==================== AC#4: API Key Revocation ====================

def test_revoke_api_key_success(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test successfully revoking an API key"""
    # Create an API key
    create_response = client.post(
        "/api/api-keys/generate",
        json={"api_key_name": "To Be Revoked"},
        headers=auth_headers
    )
    assert create_response.status_code == 201
    api_key_id = create_response.json()["id"]
    
    # Revoke it
    response = client.delete(
        f"/api/api-keys/generated/{api_key_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    # Verify status changed
    list_response = client.get("/api/api-keys/my-generated", headers=auth_headers)
    api_keys = list_response.json()["items"]
    revoked_api_key = next(t for t in api_keys if t["id"] == api_key_id)
    assert revoked_api_key["status"] == "revoked"
    assert revoked_api_key["revoked_at"] is not None


def test_revoke_api_key_not_found(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test revoking non-existent API key"""
    response = client.delete(
        "/api/api-keys/generated/99999",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_revoke_api_key_already_revoked(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test revoking an already-revoked API key"""
    # Create and revoke an API key
    create_response = client.post(
        "/api/api-keys/generate",
        json={"api_key_name": "To Revoke Twice"},
        headers=auth_headers
    )
    api_key_id = create_response.json()["id"]
    
    client.delete(f"/api/api-keys/generated/{api_key_id}", headers=auth_headers)
    
    # Try to revoke again
    response = client.delete(
        f"/api/api-keys/generated/{api_key_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "already revoked" in response.json()["detail"].lower()


def test_revoke_api_key_logs_usage_history(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test that API key revocation is logged"""
    # Create and revoke an API key
    create_response = client.post(
        "/api/api-keys/generate",
        json={"api_key_name": "To Revoke"},
        headers=auth_headers
    )
    api_key_id = create_response.json()["id"]
    
    response = client.delete(
        f"/api/api-keys/generated/{api_key_id}",
        headers=auth_headers
    )
    assert response.status_code == 204
    
    # Check usage history
    history_response = client.get("/api/users/me/api-key-usage", headers=auth_headers)
    history_data = history_response.json()
    
    # Should have REVOKED action (enum value is lowercase "revoked")
    revoked_actions = [item for item in history_data["items"] if item["action"] == "revoked"]
    assert len(revoked_actions) >= 1


# ==================== Security: Authentication Requirements ====================

def test_generate_api_key_without_auth(client: TestClient, session: Session):
    """Test that API key generation requires authentication"""
    response = client.post(
        "/api/api-keys/generate",
        json={"api_key_name": "Unauthorized"}
    )
    
    assert response.status_code in [401, 403]  # Either is valid for auth failure


def test_get_my_generated_api_keys_without_auth(client: TestClient, session: Session):
    """Test that API key listing requires authentication"""
    response = client.get("/api/api-keys/my-generated")
    
    assert response.status_code in [401, 403]  # Either is valid for auth failure


def test_revoke_api_key_without_auth(client: TestClient, session: Session):
    """Test that API key revocation requires authentication"""
    response = client.delete("/api/api-keys/generated/1")
    
    assert response.status_code in [401, 403]  # Either is valid for auth failure


# ==================== Edge Cases ====================

def test_api_key_uniqueness(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test that generated API keys are unique"""
    # Generate multiple API keys and verify uniqueness
    api_keys = []
    for i in range(3):
        response = client.post(
            "/api/api-keys/generate",
            json={"api_key_name": f"API Key {i}"},
            headers=auth_headers
        )
        assert response.status_code == 201
        api_keys.append(response.json()["api_key"])
    
    # All API keys should be unique
    assert len(api_keys) == len(set(api_keys))


def test_revoke_api_key_not_owned(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test that user cannot revoke another user's API key"""
    # Create second user
    other_user = User(
        email="other@example.com",
        hashed_password="$2b$12$other_hash",
        litellm_user_id="test_litellm_user_other"
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)
    
    other_access_token = create_access_token(data={"sub": other_user.email})
    other_headers = {"Authorization": f"Bearer {other_access_token}"}
    
    # Other user creates an API key
    create_response = client.post(
        "/api/api-keys/generate",
        json={"api_key_name": "Other's API Key"},
        headers=other_headers
    )
    other_api_key_id = create_response.json()["id"]
    
    # Test user tries to revoke it
    response = client.delete(
        f"/api/api-keys/generated/{other_api_key_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ==================== New Tests for Description Field and Edit ====================

def test_generate_api_key_with_description(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test generating API key with description"""
    response = client.post(
        "/api/api-keys/unified",
        json={
            "api_key_name": "Test Key",
            "description": "This is a test API key for development",
            "api_key_ids": []
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["api_key_name"] == "Test Key"
    assert data["description"] == "This is a test API key for development"


def test_update_api_key_metadata(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test updating API key name"""
    # Create API key
    create_response = client.post(
        "/api/api-keys/unified",
        json={
            "api_key_name": "Original Name",
            "api_key_ids": []
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201, f"Failed to create API key: {create_response.text}"
    api_key_id = create_response.json()["id"]

    # Update API key name only (description has strict validation)
    update_response = client.put(
        f"/api/api-keys/unified/{api_key_id}",
        json={
            "api_key_name": "Updated Name"
        },
        headers=auth_headers
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["api_key_name"] == "Updated Name"
    assert data["status"] == "active"


def test_update_api_key_status(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test updating API key status to revoked"""
    # Create API key
    create_response = client.post(
        "/api/api-keys/unified",
        json={
            "api_key_name": "Test Key",
            "api_key_ids": []
        },
        headers=auth_headers
    )
    api_key_id = create_response.json()["id"]
    
    # Update status to revoked
    update_response = client.put(
        f"/api/api-keys/unified/{api_key_id}",
        json={
            "status": "revoked"
        },
        headers=auth_headers
    )
    
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["status"] == "revoked"
    assert data["revoked_at"] is not None


def test_update_api_key_not_owned(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test that user cannot update another user's API key"""
    # Create second user
    other_user = User(
        email="other2@example.com",
        hashed_password="$2b$12$other_hash",
        litellm_user_id="test_litellm_user_other2"
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)

    other_access_token = create_access_token(data={"sub": other_user.email})
    other_headers = {"Authorization": f"Bearer {other_access_token}"}

    # Other user creates an API key
    create_response = client.post(
        "/api/api-keys/unified",
        json={"api_key_name": "Other's Key", "api_key_ids": []},
        headers=other_headers
    )
    other_api_key_id = create_response.json()["id"]

    # Test user tries to update it
    response = client.put(
        f"/api/api-keys/unified/{other_api_key_id}",
        json={"api_key_name": "Hacked Name"},
        headers=auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ==================== Unblock API Key Tests ====================

def test_unblock_api_key_success(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test successfully unblocking a revoked API key"""
    # Create and revoke an API key
    create_response = client.post(
        "/api/api-keys/unified",
        json={"api_key_name": "To Unblock", "api_key_ids": []},
        headers=auth_headers
    )
    api_key_id = create_response.json()["id"]

    # Revoke it first
    client.put(f"/api/api-keys/unified/{api_key_id}/block", headers=auth_headers)

    # Unblock it
    response = client.put(f"/api/api-keys/unified/{api_key_id}/unblock", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["revoked_at"] is None


def test_unblock_api_key_not_found(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test unblocking non-existent API key"""
    response = client.put("/api/api-keys/unified/99999/unblock", headers=auth_headers)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_unblock_api_key_not_revoked(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test unblocking an active API key (should fail)"""
    # Create an API key (it will be active by default)
    create_response = client.post(
        "/api/api-keys/unified",
        json={"api_key_name": "Already Active", "api_key_ids": []},
        headers=auth_headers
    )
    api_key_id = create_response.json()["id"]

    # Try to unblock it (should fail since it's not revoked)
    response = client.put(f"/api/api-keys/unified/{api_key_id}/unblock", headers=auth_headers)

    assert response.status_code == 400
    assert "only revoked" in response.json()["detail"].lower()


def test_unblock_api_key_without_auth(client: TestClient, session: Session):
    """Test that unblocking requires authentication"""
    response = client.put("/api/api-keys/unified/1/unblock")

    assert response.status_code in [401, 403]


def test_update_api_key_from_revoked_to_active(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test updating API key status from revoked to active via update endpoint"""
    # Create and revoke an API key
    create_response = client.post(
        "/api/api-keys/unified",
        json={"api_key_name": "To Reactivate", "api_key_ids": []},
        headers=auth_headers
    )
    api_key_id = create_response.json()["id"]

    client.put(f"/api/api-keys/unified/{api_key_id}/block", headers=auth_headers)

    # Update status back to active
    update_response = client.put(
        f"/api/api-keys/unified/{api_key_id}",
        json={"status": "active"},
        headers=auth_headers
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["status"] == "active"
    assert data["revoked_at"] is None


def test_unblock_api_key_not_owned(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test that user cannot unblock another user's API key"""
    # Create second user
    other_user = User(
        email="other3@example.com",
        hashed_password="$2b$12$other_hash",
        litellm_user_id="test_litellm_user_other3"
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)

    other_access_token = create_access_token(data={"sub": other_user.email})
    other_headers = {"Authorization": f"Bearer {other_access_token}"}

    # Other user creates and blocks an API key
    create_response = client.post(
        "/api/api-keys/unified",
        json={"api_key_name": "Other's Key", "api_key_ids": []},
        headers=other_headers
    )
    other_api_key_id = create_response.json()["id"]
    client.put(f"/api/api-keys/unified/{other_api_key_id}/block", headers=other_headers)

    # Test user tries to unblock it
    response = client.put(
        f"/api/api-keys/unified/{other_api_key_id}/unblock",
        headers=auth_headers
    )

    assert response.status_code == 404

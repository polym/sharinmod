"""
Comprehensive tests for Story 3.1: Unified Token Generation API

Test Coverage:
- AC#1: Successful token generation with limit check and logging
- AC#2: 5-token limit enforcement
- AC#3: Token listing with status and info
- AC#4: Token revocation with status change and logging
- Security: Authentication requirements
- Edge cases: Token uniqueness, ownership, already-revoked
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from datetime import datetime

from api.app import create_app
from api.config import Settings
from api.models.user import User
from api.models.unified_token import UnifiedToken, UnifiedTokenStatus
from api.models.token_usage import TokenUsageHistory
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
        hashed_password="$2b$12$test_hash"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(test_user: User):
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


# ==================== AC#1: Successful Token Generation ====================

def test_generate_token_success(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test successfully generating a unified token"""
    response = client.post(
        "/api/tokens/generate",
        json={"token_name": "My First Token"},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["user_id"] == test_user.id
    assert data["status"] == "active"
    assert data["token_name"] == "My First Token"
    assert "token" in data
    assert len(data["token"]) > 40  # Base64-encoded 32 bytes is ~44 chars
    assert "created_at" in data
    assert data["revoked_at"] is None


def test_generate_token_without_name(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test generating token without optional name"""
    response = client.post(
        "/api/tokens/generate",
        json={},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["token_name"] is None


def test_generate_token_logs_usage_history(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test that token generation is logged in usage history"""
    response = client.post(
        "/api/tokens/generate",
        json={"token_name": "Test Token"},
        headers=auth_headers
    )
    assert response.status_code == 201
    
    # Check usage history
    history_response = client.get("/api/users/me/token-usage", headers=auth_headers)
    assert history_response.status_code == 200
    history_data = history_response.json()
    
    # Should have one GENERATED action (enum value is lowercase "generated")
    assert history_data["total"] >= 1
    generated_actions = [item for item in history_data["items"] if item["action"] == "generated"]
    assert len(generated_actions) >= 1


# ==================== AC#2: 5-Token Limit Enforcement ====================

def test_generate_token_with_limit(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test that 6th token generation is rejected"""
    # Create 5 tokens first
    for i in range(5):
        response = client.post(
            "/api/tokens/generate",
            json={"token_name": f"Token {i+1}"},
            headers=auth_headers
        )
        assert response.status_code == 201
    
    # Try to create 6th token
    response = client.post(
        "/api/tokens/generate",
        json={"token_name": "Token 6"},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Maximum 5 tokens" in response.json()["detail"]


def test_generate_token_after_revocation(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test that revoking a token frees up a slot"""
    # Create 5 tokens
    token_ids = []
    for i in range(5):
        response = client.post(
            "/api/tokens/generate",
            json={"token_name": f"Token {i+1}"},
            headers=auth_headers
        )
        assert response.status_code == 201
        token_ids.append(response.json()["id"])
    
    # Revoke one token
    response = client.delete(
        f"/api/tokens/generated/{token_ids[0]}",
        headers=auth_headers
    )
    assert response.status_code == 204
    
    # Now can create a new token
    response = client.post(
        "/api/tokens/generate",
        json={"token_name": "Token 6"},
        headers=auth_headers
    )
    assert response.status_code == 201


# ==================== AC#3: Token Listing ====================

def test_get_my_generated_tokens_empty(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test listing tokens when user has none"""
    response = client.get("/api/tokens/my-generated", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_get_my_generated_tokens_with_data(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test listing tokens with existing data"""
    # Create 2 tokens
    client.post(
        "/api/tokens/generate",
        json={"token_name": "Token 1"},
        headers=auth_headers
    )
    client.post(
        "/api/tokens/generate",
        json={"token_name": "Token 2"},
        headers=auth_headers
    )
    
    # Get list
    response = client.get("/api/tokens/my-generated", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    # Should be ordered by creation date (newest first)
    assert data["items"][0]["token_name"] == "Token 2"
    assert data["items"][1]["token_name"] == "Token 1"


# ==================== AC#4: Token Revocation ====================

def test_revoke_token_success(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test successfully revoking a token"""
    # Create a token
    create_response = client.post(
        "/api/tokens/generate",
        json={"token_name": "To Be Revoked"},
        headers=auth_headers
    )
    assert create_response.status_code == 201
    token_id = create_response.json()["id"]
    
    # Revoke it
    response = client.delete(
        f"/api/tokens/generated/{token_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    # Verify status changed
    list_response = client.get("/api/tokens/my-generated", headers=auth_headers)
    tokens = list_response.json()["items"]
    revoked_token = next(t for t in tokens if t["id"] == token_id)
    assert revoked_token["status"] == "revoked"
    assert revoked_token["revoked_at"] is not None


def test_revoke_token_not_found(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test revoking non-existent token"""
    response = client.delete(
        "/api/tokens/generated/99999",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_revoke_token_already_revoked(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test revoking an already-revoked token"""
    # Create and revoke a token
    create_response = client.post(
        "/api/tokens/generate",
        json={"token_name": "To Revoke Twice"},
        headers=auth_headers
    )
    token_id = create_response.json()["id"]
    
    client.delete(f"/api/tokens/generated/{token_id}", headers=auth_headers)
    
    # Try to revoke again
    response = client.delete(
        f"/api/tokens/generated/{token_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "already revoked" in response.json()["detail"].lower()


def test_revoke_token_logs_usage_history(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test that token revocation is logged"""
    # Create and revoke a token
    create_response = client.post(
        "/api/tokens/generate",
        json={"token_name": "To Revoke"},
        headers=auth_headers
    )
    token_id = create_response.json()["id"]
    
    response = client.delete(
        f"/api/tokens/generated/{token_id}",
        headers=auth_headers
    )
    assert response.status_code == 204
    
    # Check usage history
    history_response = client.get("/api/users/me/token-usage", headers=auth_headers)
    history_data = history_response.json()
    
    # Should have REVOKED action (enum value is lowercase "revoked")
    revoked_actions = [item for item in history_data["items"] if item["action"] == "revoked"]
    assert len(revoked_actions) >= 1


# ==================== Security: Authentication Requirements ====================

def test_generate_token_without_auth(client: TestClient, session: Session):
    """Test that token generation requires authentication"""
    response = client.post(
        "/api/tokens/generate",
        json={"token_name": "Unauthorized"}
    )
    
    assert response.status_code in [401, 403]  # Either is valid for auth failure


def test_get_my_generated_tokens_without_auth(client: TestClient, session: Session):
    """Test that token listing requires authentication"""
    response = client.get("/api/tokens/my-generated")
    
    assert response.status_code in [401, 403]  # Either is valid for auth failure


def test_revoke_token_without_auth(client: TestClient, session: Session):
    """Test that token revocation requires authentication"""
    response = client.delete("/api/tokens/generated/1")
    
    assert response.status_code in [401, 403]  # Either is valid for auth failure


# ==================== Edge Cases ====================

def test_token_uniqueness(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test that generated tokens are unique"""
    # Generate multiple tokens and verify uniqueness
    tokens = []
    for i in range(3):
        response = client.post(
            "/api/tokens/generate",
            json={"token_name": f"Token {i}"},
            headers=auth_headers
        )
        assert response.status_code == 201
        tokens.append(response.json()["token"])
    
    # All tokens should be unique
    assert len(tokens) == len(set(tokens))


def test_revoke_token_not_owned(
    client: TestClient,
    session: Session,
    test_user: User,
    auth_headers: dict
):
    """Test that user cannot revoke another user's token"""
    # Create second user
    other_user = User(
        email="other@example.com",
        hashed_password="$2b$12$other_hash"
    )
    session.add(other_user)
    session.commit()
    session.refresh(other_user)
    
    other_token = create_access_token(data={"sub": other_user.email})
    other_headers = {"Authorization": f"Bearer {other_token}"}
    
    # Other user creates a token
    create_response = client.post(
        "/api/tokens/generate",
        json={"token_name": "Other's Token"},
        headers=other_headers
    )
    other_token_id = create_response.json()["id"]
    
    # Test user tries to revoke it
    response = client.delete(
        f"/api/tokens/generated/{other_token_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

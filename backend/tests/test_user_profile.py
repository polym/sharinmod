"""
Comprehensive test suite for user profile management functionality
Tests cover all acceptance criteria from Story 1.4
"""
import pytest
import time
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from api.app import create_app
from api.config import Settings
from api.database import get_db

# Set testing mode globally for this test file
import api.config
api.config.settings.TESTING = True


# Create in-memory SQLite database for testing
@pytest.fixture(name="session")
def session_fixture():
    """Create a fresh database for each test"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create test client with dependency override"""
    def get_session_override():
        return session

    settings = Settings()
    settings.TESTING = True  # Enable testing mode
    app = create_app(settings)
    app.dependency_overrides[get_db] = get_session_override
    
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="auth_token")
def auth_token_fixture(client: TestClient):
    """Create user and get auth token"""
    # Register
    register_response = client.post("/api/users/register", json={
        "email": "profiletest@example.com",
        "password": "TestPass123!"
    })
    assert register_response.status_code == 201
    # Login
    login_response = client.post("/api/auth/login", json={
        "email": "profiletest@example.com",
        "password": "TestPass123!"
    })
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


def test_get_profile_success(client: TestClient, auth_token):
    """
    AC #2: Test getting user profile with authentication
    Given authenticated user,
    When I get my profile information,
    Then I receive current profile data.
    """
    response = client.get(
        "/api/users/me/profile",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profiletest@example.com"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    # Profile fields should exist (may be null initially)
    assert "name" in data
    assert "avatar_url" in data
    assert "bio" in data


def test_get_profile_without_auth(client: TestClient):
    """
    AC #3: Test getting profile without authentication
    Given unauthenticated user,
    When I attempt to access profile,
    Then I receive 401/403 error.
    """
    response = client.get("/api/users/me/profile")
    assert response.status_code == 403  # No credentials provided


def test_update_profile_full(client: TestClient, auth_token):
    """
    AC #1: Test updating all profile fields
    Given authenticated user,
    When I update profile,
    Then changes are saved and returned.
    """
    response = client.patch(
        "/api/users/me/profile",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "name": "测试用户",
            "avatar_url": "https://example.com/avatar.jpg",
            "bio": "这是一个测试用户的简介"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试用户"
    assert data["avatar_url"] == "https://example.com/avatar.jpg"
    assert data["bio"] == "这是一个测试用户的简介"


def test_update_profile_partial(client: TestClient, auth_token):
    """
    AC #1: Test updating only some profile fields (PATCH semantics)
    """
    # First set all fields
    client.patch(
        "/api/users/me/profile",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "name": "原名字",
            "avatar_url": "https://example.com/old.jpg",
            "bio": "原简介"
        }
    )
    
    # Update only name
    response = client.patch(
        "/api/users/me/profile",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "新名字"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "新名字"
    # Other fields should remain unchanged
    assert data["avatar_url"] == "https://example.com/old.jpg"
    assert data["bio"] == "原简介"


def test_update_profile_without_auth(client: TestClient):
    """
    AC #3: Test updating profile without authentication
    Given unauthenticated user,
    When I attempt to update profile,
    Then I receive 401 Unauthorized error.
    """
    response = client.patch(
        "/api/users/me/profile",
        json={"name": "不应该成功"}
    )
    assert response.status_code == 403


def test_update_profile_invalid_token(client: TestClient):
    """
    AC #3: Test updating profile with invalid token
    """
    response = client.patch(
        "/api/users/me/profile",
        headers={"Authorization": "Bearer invalid-token"},
        json={"name": "不应该成功"}
    )
    assert response.status_code == 401


def test_update_profile_empty_data(client: TestClient, auth_token):
    """
    Test updating profile with empty data (should succeed, no changes)
    """
    response = client.patch(
        "/api/users/me/profile",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={}
    )
    assert response.status_code == 200


def test_update_profile_field_too_long(client: TestClient, auth_token):
    """
    Test validation for fields exceeding max length
    """
    response = client.patch(
        "/api/users/me/profile",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "x" * 101}  # Exceeds max_length=100
    )
    assert response.status_code == 422  # Validation error


def test_profile_persistence(client: TestClient, auth_token):
    """
    Test that profile changes persist across requests
    """
    # Update profile
    client.patch(
        "/api/users/me/profile",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"bio": "持久化测试"}
    )
    
    # Get profile in new request
    response = client.get(
        "/api/users/me/profile",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["bio"] == "持久化测试"


def test_updated_at_changes(client: TestClient, auth_token):
    """
    Test that updated_at timestamp changes on profile update
    """
    # Get initial profile
    response1 = client.get(
        "/api/users/me/profile",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    initial_updated_at = response1.json()["updated_at"]
    
    # Small delay to ensure timestamp difference
    time.sleep(1)
    
    # Update profile
    client.patch(
        "/api/users/me/profile",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "更新时间测试"}
    )
    
    # Get updated profile
    response2 = client.get(
        "/api/users/me/profile",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    updated_updated_at = response2.json()["updated_at"]
    
    # updated_at should have changed
    assert updated_updated_at > initial_updated_at


def test_avatar_url_validation(client: TestClient, auth_token):
    """
    Test that avatar_url field accepts valid URLs
    """
    response = client.patch(
        "/api/users/me/profile",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"avatar_url": "https://cdn.example.com/user/avatar.png"}
    )
    assert response.status_code == 200
    assert response.json()["avatar_url"] == "https://cdn.example.com/user/avatar.png"

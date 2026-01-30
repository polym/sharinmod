"""
Tests for user registration API endpoint
Following TDD approach: write tests first, then implementation
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

# Import will be available after implementation
from api.app import create_app
from api.config import Settings
from api.database import get_db
from api.models.user import User  # Import User model to create tables

# Create test app
settings = Settings()
app = create_app(settings)

# Setup test database
@pytest.fixture(name="session")
def session_fixture():
    """Create a fresh database for each test"""
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
    """Create test client with overridden database dependency"""
    def get_session_override():
        return session
    
    app.dependency_overrides[get_db] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

# AC #1: Successful registration
def test_register_user_success(client: TestClient, mocker):
    """Test successful user registration with valid email and password"""
    # Mock LiteLLM API success
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"user_id": "test@example.com"}
    mock_response.raise_for_status.return_value = None
    
    mocker.patch('httpx.AsyncClient.post', return_value=mock_response)
    
    response = client.post("/api/users/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "created_at" in data
    # Password should NOT be in response
    assert "password" not in data
    assert "hashed_password" not in data

# AC #2: Duplicate email rejection
def test_register_duplicate_email(client: TestClient, mocker):
    """Test registration with duplicate email returns 409 Conflict"""
    # Mock LiteLLM API success for both calls
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"user_id": "duplicate@example.com"}
    mock_response.raise_for_status.return_value = None
    
    mock_post = mocker.patch('httpx.AsyncClient.post', return_value=mock_response)
    
    # First registration should succeed
    response1 = client.post("/api/users/register", json={
        "email": "duplicate@example.com",
        "password": "SecurePass123!"
    })
    assert response1.status_code == 201
    
    # Duplicate registration should fail with 409
    response2 = client.post("/api/users/register", json={
        "email": "duplicate@example.com",
        "password": "AnotherPass123!"
    })
    assert response2.status_code == 409, f"Expected 409, got {response2.status_code}"
    assert "already registered" in response2.json()["detail"].lower() or "already exists" in response2.json()["detail"].lower()
    
    # LiteLLM should be called twice (both attempts try to create user in LiteLLM, but second fails on db commit)
    assert mock_post.call_count == 2

# AC #3: Invalid email format
def test_register_invalid_email(client: TestClient):
    """Test registration with invalid email format returns validation error"""
    invalid_emails = [
        "not-an-email",
        "missing@domain",
        "@nodomain.com",
        "spaces in@email.com"
    ]
    
    for invalid_email in invalid_emails:
        response = client.post("/api/users/register", json={
            "email": invalid_email,
            "password": "SecurePass123!"
        })
        assert response.status_code == 422, f"Email '{invalid_email}' should fail validation"

# AC #3: Weak password validation
def test_register_weak_password_no_uppercase(client: TestClient):
    """Test password must contain uppercase letter"""
    response = client.post("/api/users/register", json={
        "email": "test1@example.com",
        "password": "nouppercase1!"
    })
    assert response.status_code == 422
    assert "uppercase" in str(response.json()).lower() or "大写" in str(response.json())

def test_register_weak_password_no_lowercase(client: TestClient):
    """Test password must contain lowercase letter"""
    response = client.post("/api/users/register", json={
        "email": "test2@example.com",
        "password": "NOLOWERCASE1!"
    })
    assert response.status_code == 422
    assert "lowercase" in str(response.json()).lower() or "小写" in str(response.json())

def test_register_weak_password_no_digit(client: TestClient):
    """Test password must contain digit"""
    response = client.post("/api/users/register", json={
        "email": "test3@example.com",
        "password": "NoDigitsHere!"
    })
    assert response.status_code == 422
    assert "digit" in str(response.json()).lower() or "数字" in str(response.json())

def test_register_weak_password_no_special(client: TestClient):
    """Test password must contain special character"""
    response = client.post("/api/users/register", json={
        "email": "test4@example.com",
        "password": "NoSpecial123"
    })
    assert response.status_code == 422
    assert "special" in str(response.json()).lower() or "特殊" in str(response.json())

def test_register_weak_password_too_short(client: TestClient):
    """Test password must be at least 8 characters"""
    response = client.post("/api/users/register", json={
        "email": "test5@example.com",
        "password": "Short1!"
    })
    assert response.status_code == 422
    assert "8" in str(response.json()) or "length" in str(response.json()).lower()

# AC 1: Successful registration with LiteLLM integration
def test_register_user_success_with_litellm(client: TestClient, mocker):
    """Test successful user registration with LiteLLM integration"""
    # Mock LiteLLM API success
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"user_id": "test@example.com"}
    mock_response.raise_for_status.return_value = None
    
    mock_post = mocker.patch('httpx.AsyncClient.post', return_value=mock_response)
    
    response = client.post("/api/users/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "created_at" in data
    # Password should NOT be in response
    assert "password" not in data
    assert "hashed_password" not in data
    
    # Verify LiteLLM API was called
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[1]['json'] == {"user_id": "test@example.com"}
    assert "Authorization" in call_args[1]['headers']

# AC 2: LiteLLM API failure
def test_register_user_litellm_failure(client: TestClient, mocker):
    """Test registration fails when LiteLLM API returns error"""
    # Mock LiteLLM API failure
    mock_post = mocker.patch('httpx.AsyncClient.post', side_effect=Exception("API Error"))
    
    response = client.post("/api/users/register", json={
        "email": "fail@example.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 500, f"Expected 500, got {response.status_code}"
    assert "LiteLLM" in response.json()["detail"]
    
    # Verify API was called
    mock_post.assert_called_once()

# AC 2: LiteLLM timeout
def test_register_user_litellm_timeout(client: TestClient, mocker):
    """Test registration fails on LiteLLM API timeout"""
    import httpx
    # Mock timeout
    mock_post = mocker.patch('httpx.AsyncClient.post', side_effect=httpx.TimeoutException("Timeout"))
    
    response = client.post("/api/users/register", json={
        "email": "timeout@example.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 500, f"Expected 500, got {response.status_code}"
    assert "LiteLLM" in response.json()["detail"]
    
    # Verify API was called
    mock_post.assert_called_once()

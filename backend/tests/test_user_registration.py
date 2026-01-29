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
def test_register_user_success(client: TestClient):
    """Test successful user registration with valid email and password"""
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
def test_register_duplicate_email(client: TestClient):
    """Test registration with duplicate email returns 409 Conflict"""
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

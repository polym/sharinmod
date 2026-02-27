"""Test dynamic provider support - database first lookup"""
import sys
sys.path.insert(0, "/app")

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from api.app import create_app
from api.config import settings
from api.database import get_db
from api.models.provider_config import ProviderConfig, ProviderModel
from api.models.shared_api_key import APIKeyProvider
from api.models.user import User
from api.utils.security import hash_password

# Enable testing mode
settings.TESTING = True


def test_dynamic_provider_from_database():
    """
    Test that providers in database but NOT in enum can still return models.
    
    This is the key fix: database lookup happens before enum validation.
    """
    # Create in-memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    
    def get_test_db():
        with Session(engine) as session:
            yield session
    
    app = create_app(settings)
    app.dependency_overrides[get_db] = get_test_db
    
    client = TestClient(app)
    session = next(get_test_db())
    
    # Create test user
    test_user = User(
        username="testuser_dynamic",
        email="test_dynamic@example.com",
        hashed_password=hash_password("testpass"),
        is_active=True
    )
    session.add(test_user)
    session.commit()
    session.refresh(test_user)
    
    # Login to get token (use email, not username)
    response = client.post("/api/auth/login", json={
        "email": "test_dynamic@example.com",
        "password": "testpass"
    })
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code} - {response.text}")
        return False
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a provider that is NOT in APIKeyProvider enum
    test_provider = ProviderConfig(
        provider_key="test_dynamic_provider",
        name="Test Dynamic Provider",
        website="https://test.example.com",
        logo_path="/providers/test-logo.png",
        is_enabled=True
    )
    session.add(test_provider)
    session.commit()
    session.refresh(test_provider)
    
    # Add a model for this provider
    test_model = ProviderModel(
        provider_config_id=test_provider.id,
        model_key="test-model-1",
        display_name="Test Model 1",
        context_length="128000",
        max_output_length="4096",
        is_enabled=True
    )
    session.add(test_model)
    session.commit()
    
    # Now test: this provider should return models from database
    response = client.get(
        "/api/api-keys/providers/test_dynamic_provider/models",
        headers=headers
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    # Assert: should return 200 with model from database
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["provider"] == "test_dynamic_provider"
    assert "test-model-1" in data["supported_models"]
    
    print("PASSED: Dynamic provider test")
    return True


if __name__ == "__main__":
    try:
        test_dynamic_provider_from_database()
    except Exception as e:
        import traceback
        print(f"FAILED: {e}")
        traceback.print_exc()

"""
Shared pytest fixtures and configuration for backend tests
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch


@pytest.fixture(name="mock_litellm_client", autouse=True)
def mock_litellm_client_fixture():
    """
    Auto-use fixture that mocks httpx.AsyncClient for LiteLLM API calls.

    This prevents real HTTP calls to LiteLLM during testing.
    Tests can override this fixture if needed.
    """
    with patch('api.services.unified_api_key_service.httpx.AsyncClient') as mock:
        # Mock the async context manager
        mock_instance = AsyncMock()

        # Create mock response for key generation
        mock_generate_response = Mock()
        mock_generate_response.status_code = 200
        mock_generate_response.json = Mock(return_value={
            "key": "sk-litellm-mock-test-key",
            "token_id": "sk-litellm-mock-test-key"
        })
        mock_generate_response.raise_for_status = Mock()

        # Create mock response for block/unlock/delete operations
        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.raise_for_status = Mock()

        # Make post async return the mock response directly (not wrapped)
        async def mock_post(*args, **kwargs):
            # Check if this is a generate request
            if args and 'generate' in str(args[-1]):
                return mock_generate_response
            return mock_success_response

        mock_instance.post = mock_post
        mock.return_value.__aenter__.return_value = mock_instance
        yield mock

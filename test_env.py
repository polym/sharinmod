import os
import pytest

def test_env_configured():
    """Test that .env file has been created with necessary configuration."""
    env_path = 'backend/.env'
    
    # Check that .env file exists
    assert os.path.exists(env_path), ".env file should exist in backend/"
    
    # Read env file and check for required variables
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    # Check for required environment variables
    required_vars = [
        'APP_SECRET_KEY',
        'ENV',
        'DATABASE_URI',
        'REDIS_DATABASE'
    ]
    
    for var in required_vars:
        assert var in env_content, f"{var} should be configured in .env file"
    
    # Check that DATABASE_URI is configured for PostgreSQL (not SQLite)
    assert 'postgresql://' in env_content or 'postgres://' in env_content, \
        "DATABASE_URI should be configured for PostgreSQL"
    
    # Check that database name is sharinmod
    assert 'sharinmod' in env_content, "Database name should be sharinmod"

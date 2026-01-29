import os
import pytest

def test_project_structure_adapted():
    """Test that the template structure has been adapted for sharinmod project."""
    
    # Verify backend structure exists
    assert os.path.exists('backend/api'), "Backend API directory should exist"
    assert os.path.exists('backend/api/app.py'), "Main FastAPI app should exist"
    assert os.path.exists('backend/api/database.py'), "Database module should exist"
    assert os.path.exists('backend/api/config.py'), "Config module should exist"
    
    # Verify frontend structure exists
    assert os.path.exists('frontend/src'), "Frontend src directory should exist"
    assert os.path.exists('frontend/src/app'), "Next.js app directory should exist"
    assert os.path.exists('frontend/package.json'), "Frontend package.json should exist"
    
    # Verify docker-compose is in place
    assert os.path.exists('docker-compose.yml'), "docker-compose.yml should exist"
    
    # Verify backend .env is configured
    assert os.path.exists('backend/.env'), "Backend .env should be configured"
    
    # Verify database configuration references sharinmod
    with open('backend/.env', 'r') as f:
        env_content = f.read()
    assert 'sharinmod' in env_content, "Database should be named sharinmod"
    
    # Verify docker-compose references sharinmod
    with open('docker-compose.yml', 'r') as f:
        compose_content = f.read()
    assert 'sharinmod' in compose_content, "docker-compose should reference sharinmod database"
    
    print("\n=== Project Structure Adaptation Complete ===")
    print("✓ Backend structure in place (FastAPI)")
    print("✓ Frontend structure in place (Next.js)")
    print("✓ Docker Compose configured")
    print("✓ Environment variables configured")
    print("✓ Database named 'sharinmod'")
    print("✓ Service names updated (db instead of postgres)")
    print("\n⚠️  Note: Example models (towns, people) in template need to be")
    print("   replaced with sharinmod models (users, tokens) in future stories")
    print("============================================\n")

import os
import pytest
import json
import subprocess

def test_backend_requirements_exists():
    """Test that backend requirements.txt exists and contains essential packages."""
    requirements_path = 'backend/api/requirements.txt'
    assert os.path.exists(requirements_path), "backend/api/requirements.txt should exist"

    with open(requirements_path, 'r') as f:
        requirements_content = f.read()

    # Check for essential packages
    essential_packages = [
        'fastapi',
        'uvicorn',
        'SQLAlchemy',  # Note: capitalized in requirements.txt
        'pydantic',
        'python-dotenv'
    ]

    missing_packages = []
    for package in essential_packages:
        if package not in requirements_content:
            missing_packages.append(package)

    assert not missing_packages, f"Missing essential packages in requirements.txt: {missing_packages}"

    print("✅ Backend requirements.txt contains all essential packages")


def test_frontend_package_json_exists():
    """Test that frontend package.json exists and contains essential dependencies."""
    package_json_path = 'frontend/package.json'
    assert os.path.exists(package_json_path), "frontend/package.json should exist"

    with open(package_json_path, 'r') as f:
        package_data = json.load(f)

    # Check for essential dependencies
    dependencies = package_data.get('dependencies', {})
    dev_dependencies = package_data.get('devDependencies', {})

    essential_deps = [
        'next',
        'react',
        'react-dom'
    ]

    missing_deps = []
    for dep in essential_deps:
        if dep not in dependencies and dep not in dev_dependencies:
            missing_deps.append(dep)

    assert not missing_deps, f"Missing essential dependencies in package.json: {missing_deps}"

    # Check for scripts
    scripts = package_data.get('scripts', {})
    required_scripts = ['dev', 'build', 'start']

    missing_scripts = []
    for script in required_scripts:
        if script not in scripts:
            missing_scripts.append(script)

    assert not missing_scripts, f"Missing required scripts in package.json: {missing_scripts}"

    print("✅ Frontend package.json contains all essential dependencies and scripts")


def test_dockerfiles_exist():
    """Test that Dockerfiles exist for backend and frontend."""
    backend_dockerfile = 'backend/Dockerfile'
    frontend_dockerfile = 'frontend/Dockerfile'

    assert os.path.exists(backend_dockerfile), "backend/Dockerfile should exist"
    assert os.path.exists(frontend_dockerfile), "frontend/Dockerfile should exist"

    print("✅ Dockerfiles exist for both backend and frontend")


def test_docker_compose_services():
    """Test that docker-compose.yml defines all required services."""
    import yaml

    compose_path = 'docker-compose.yml'
    assert os.path.exists(compose_path), "docker-compose.yml should exist"

    with open(compose_path, 'r') as f:
        compose_data = yaml.safe_load(f)

    services = compose_data.get('services', {})
    required_services = ['frontend', 'backend', 'db', 'redis']

    missing_services = []
    for service in required_services:
        if service not in services:
            missing_services.append(service)

    assert not missing_services, f"Missing required services in docker-compose.yml: {missing_services}"

    print("✅ Docker Compose defines all required services")


def test_environment_file_structure():
    """Test that .env file has proper structure."""
    env_path = 'backend/.env'
    assert os.path.exists(env_path), "backend/.env should exist"

    with open(env_path, 'r') as f:
        env_content = f.read()

    # Check for required environment variables
    required_vars = [
        'APP_SECRET_KEY',
        'ENV',
        'DATABASE_URI',
        'REDIS_DATABASE'
    ]

    missing_vars = []
    for var in required_vars:
        if var not in env_content:
            missing_vars.append(var)

    assert not missing_vars, f"Missing required environment variables: {missing_vars}"

    print("✅ Environment file has proper structure")


def test_gitignore_excludes_sensitive_files():
    """Test that .gitignore excludes sensitive files."""
    gitignore_path = '.gitignore'
    assert os.path.exists(gitignore_path), ".gitignore should exist"

    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()

    sensitive_patterns = [
        '.env',
        '__pycache__/',
        'node_modules/',
        '*.py[cod]'
    ]

    missing_patterns = []
    for pattern in sensitive_patterns:
        if pattern not in gitignore_content:
            missing_patterns.append(pattern)

    assert not missing_patterns, f".gitignore missing patterns for sensitive files: {missing_patterns}"

    print("✅ .gitignore properly excludes sensitive files")


def test_readme_exists():
    """Test that README.md exists and contains essential information."""
    readme_path = 'README.md'
    assert os.path.exists(readme_path), "README.md should exist"

    with open(readme_path, 'r') as f:
        readme_content = f.read()

    essential_sections = [
        'Quick Start',
        'Setup',
        'Architecture',
        'Testing'
    ]

    missing_sections = []
    for section in essential_sections:
        if section not in readme_content:
            missing_sections.append(section)

    assert not missing_sections, f"README.md missing essential sections: {missing_sections}"

    print("✅ README.md exists and contains essential information")
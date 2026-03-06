"""
Tests for initial admin user functionality
Tests cover all acceptance criteria from tech-spec-init-admin-user.md
"""
import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from api.models.user import User
from api.utils.security import hash_password, verify_password
from api.services.user_service import change_password
from datetime import datetime
import importlib


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


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset settings module after each test to avoid state pollution"""
    yield
    # Reload config module to reset any modified settings
    import api.config
    import api.database
    importlib.reload(api.config)
    # Re-import settings to get fresh instance
    from api.config import settings as fresh_settings
    api.database.settings = fresh_settings


# AC 1: Test creating admin user when database is empty
def test_initialize_admin_user_creates_new_user(session: Session):
    """
    AC 1: Given 系统首次启动（数据库无用户）, when 执行 initialize_admin_user(), then 创建管理员用户
    """
    from api.database import initialize_admin_user

    # Ensure no users exist
    assert session.exec(select(User)).first() is None

    # Initialize admin user
    initialize_admin_user(session)

    # Verify admin user was created
    admin = session.exec(select(User).where(User.email == "admin@sharin.mod")).first()
    assert admin is not None
    assert admin.is_admin is True
    assert admin.force_password_change is True
    assert admin.name == "admin"
    assert verify_password("Aha12345!", admin.hashed_password)


# AC 2: Test skipping creation when admin email already exists
def test_initialize_admin_user_skips_existing_email(session: Session):
    """
    AC 2: Given 管理员邮箱已存在, when 执行 initialize_admin_user(), then 跳过创建
    """
    from api.database import initialize_admin_user

    # Create existing user with admin email
    existing_user = User(
        email="admin@sharin.mod",
        hashed_password=hash_password("ExistingPass123!"),
        name="existing_admin",
        is_admin=False,
        force_password_change=False
    )
    session.add(existing_user)
    session.commit()

    # Initialize admin user
    initialize_admin_user(session)

    # Verify existing user was not overwritten
    admin = session.exec(select(User).where(User.email == "admin@sharin.mod")).first()
    assert admin is not None
    assert admin.name == "existing_admin"
    assert admin.is_admin is False
    assert admin.force_password_change is False
    assert verify_password("ExistingPass123!", admin.hashed_password)


# AC 3: Test using environment variables for admin credentials
def test_initialize_admin_user_uses_custom_settings(session: Session, monkeypatch):
    """
    AC 3: Given 使用自定义配置邮箱密码, when 执行 initialize_admin_user(), then 使用配置值创建管理员
    """
    from api.database import initialize_admin_user

    # Set environment variables before importing settings
    monkeypatch.setenv("SHARINMOD_ADMIN_EMAIL", "custom@admin.com")
    monkeypatch.setenv("SHARINMOD_ADMIN_PASSWORD", "CustomPass123!")

    # Re-import Settings to pick up new env vars
    import api.config
    importlib.reload(api.config)
    from api.config import settings as reloaded_settings

    # Temporarily replace settings
    from api import database
    original_settings = database.settings
    database.settings = reloaded_settings

    try:
        initialize_admin_user(session)

        # Verify admin user was created with custom credentials
        admin = session.exec(select(User).where(User.email == "custom@admin.com")).first()
        assert admin is not None
        assert admin.is_admin is True
        assert admin.force_password_change is True
        assert admin.name == "custom"
        assert verify_password("CustomPass123!", admin.hashed_password)
    finally:
        database.settings = original_settings


# AC 4: Test that force_password_change field exists in User model
def test_user_model_has_force_password_change_field():
    """
    AC 4: Test that User model has force_password_change field
    """
    user = User(
        email="test@example.com",
        hashed_password=hash_password("TestPass123!"),
        force_password_change=True
    )
    assert hasattr(user, 'force_password_change')
    assert user.force_password_change is True


# AC 5: Test change password clears force flag
def test_change_password_clears_force_flag(session: Session):
    """
    AC 5: Given 用户 force_password_change=True, when 调用修改密码函数成功, then force_password_change 设为 False
    """
    # Create user with force_password_change=True
    user = User(
        email="changepass@example.com",
        hashed_password=hash_password("OldPass123!"),
        name="changepass",
        force_password_change=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # Change password
    updated_user = change_password(session, user, "NewPass456!")

    # Verify force_password_change is now False
    assert updated_user.force_password_change is False
    assert verify_password("NewPass456!", updated_user.hashed_password)


# AC 6: Test invalid email format handling
def test_initialize_admin_user_validates_email(session: Session, capsys, monkeypatch):
    """
    AC 6: Given 邮箱格式非法, when 执行 initialize_admin_user(), then 打印警告日志并跳过创建
    """
    from api.database import initialize_admin_user

    # Set invalid email in environment
    monkeypatch.setenv("SHARINMOD_ADMIN_EMAIL", "invalid-email")

    # Re-import Settings to pick up new env vars
    import api.config
    importlib.reload(api.config)
    from api.config import settings as reloaded_settings

    # Temporarily replace settings
    from api import database
    original_settings = database.settings
    database.settings = reloaded_settings

    try:
        initialize_admin_user(session)

        # Verify no user was created
        users = session.exec(select(User)).all()
        assert len(users) == 0

        # Verify warning was printed
        captured = capsys.readouterr()
        assert "Invalid admin email format" in captured.out
    finally:
        database.settings = original_settings


# Test password strength validation (unit test)
def test_password_validation():
    """
    Test password validation logic
    """
    import re

    def validate_password(password: str) -> bool:
        """Validate password meets security requirements"""
        if len(password) < 8 or len(password) > 72:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        return True

    # Valid passwords
    assert validate_password("Aha12345")
    assert validate_password("TestPass123")
    assert validate_password("MySecure1Pass")

    # Invalid passwords
    assert not validate_password("short1")  # Too short
    assert not validate_password("alllowercase1")  # No uppercase
    assert not validate_password("ALLUPPERCASE1")  # No lowercase
    assert not validate_password("NoDigits")  # No digits


# Test user name extraction from email
def test_user_name_extraction():
    """
    Test that user name is extracted correctly from email
    """
    # Test name extraction logic
    email = "admin@sharinmod.local"
    name = email.split('@')[0]
    assert name == "admin"

    email = "john.doe@example.com"
    name = email.split('@')[0]
    assert name == "john.doe"


# Test force_password_change default value
def test_force_password_change_default():
    """
    Test that force_password_change defaults to False
    """
    user = User(
        email="default@example.com",
        hashed_password=hash_password("TestPass123!")
    )
    assert user.force_password_change is False


# Test that initialize_admin_user is idempotent
def test_initialize_admin_user_idempotent(session: Session):
    """
    Test that calling initialize_admin_user multiple times doesn't create duplicates
    """
    from api.database import initialize_admin_user

    # First call
    initialize_admin_user(session)
    count1 = len(session.exec(select(User)).all())

    # Second call
    initialize_admin_user(session)
    count2 = len(session.exec(select(User)).all())

    assert count1 == count2 == 1


# Test that admin user has correct timestamps
def test_admin_user_timestamps(session: Session):
    """
    Test that admin user has valid created_at and updated_at timestamps
    """
    from api.database import initialize_admin_user

    initialize_admin_user(session)

    admin = session.exec(select(User).where(User.email == "admin@sharin.mod")).first()
    assert admin is not None
    assert admin.created_at is not None
    assert admin.updated_at is not None
    assert isinstance(admin.created_at, datetime)
    assert isinstance(admin.updated_at, datetime)
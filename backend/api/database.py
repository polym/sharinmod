from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.ext.asyncio import session

from api.config import settings
# Import models so SQLModel knows about them
from api.models.user import User  # noqa: F401
from api.models.api_key_usage import APIKeyUsageHistory  # noqa: F401
from api.models.shared_api_key import SharedAPIKey  # noqa: F401
from api.models.unified_api_key import UnifiedAPIKey  # noqa: F401
from api.models.subscription import Subscription  # noqa: F401
from api.models.usage_log import UsageLog  # noqa: F401
from api.models.provider_config import GlobalModel, ProviderConfig, ProviderModel  # noqa: F401
from api.models.claw import Claw  # noqa: F401

# connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URI, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_db():
    with Session(engine) as session:
        yield session


def initialize_sharinmod_data(db: Session):
    """
    Initialize sharinmod-specific data on startup.
    - Import providers and models from YAML configuration
    - Sync global models from built-in catalog (deprecated, kept for backward compatibility)
    """
    import os
    from api.config import settings
    from api.services.provider_config_service import import_providers_from_yaml

    # Import providers from YAML configuration
    # YAML file is expected to be in the same directory as config.yaml
    config_path = settings.CONFIG_PATH
    if config_path:
        config_dir = os.path.dirname(os.path.abspath(config_path))
        providers_yaml_path = os.path.join(config_dir, "providers.yaml")

        try:
            stats = import_providers_from_yaml(db, providers_yaml_path)
            if stats.get("providers_created") or stats.get("providers_updated"):
                print(f"✓ Imported {stats['providers_created']} new providers, "
                      f"{stats['providers_updated']} updated providers from YAML")
                print(f"✓ Imported {stats['models_created']} new models, "
                      f"{stats['models_updated']} updated models from YAML")
        except Exception as e:
            print(f"⚠ Failed to import providers from YAML: {e}")
            # Continue startup even if YAML import fails


def initialize_admin_user(db: Session):
    """
    Initialize admin user on startup.

    Creates a default admin user if the configured email doesn't exist.
    Uses environment variables for configuration:
    - SHARINMOD_ADMIN_EMAIL: Admin email (default: admin@sharin.mod)
    - SHARINMOD_ADMIN_PASSWORD: Admin password (default: Aha12345!)

    The user will be created with:
    - is_admin=True
    - force_password_change=True (requires password change on first login)
    """
    from api.models.user import User
    from api.utils.security import hash_password
    from api.config import settings
    import re

    email = settings.SHARINMOD_ADMIN_EMAIL
    password = settings.SHARINMOD_ADMIN_PASSWORD

    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        print(f"⚠ Invalid admin email format: {email}. Skipping admin user initialization.")
        return

    # Check if user already exists
    existing_user = db.exec(
        __import__('sqlmodel', fromlist=['select']).select(User).where(User.email == email)
    ).first()

    if existing_user:
        print(f"✓ Admin user already exists: {email}")
        return

    # Extract name from email (part before @)
    name = email.split('@')[0]

    # Create admin user
    admin_user = User(
        email=email,
        hashed_password=hash_password(password),
        name=name,
        is_admin=True,
        force_password_change=True
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    # Print prominent message
    print("\n" + "╔" + "═" * 60 + "╗")
    print("║" + "  初始管理员账户已创建".center(56) + "║")
    print("║" + f"  邮箱: {email}".ljust(59) + "║")
    print("║" + f"  密码: {password}".ljust(59) + "║")
    print("║" + "  请登录后立即修改密码！".center(56) + "║")
    print("╚" + "═" * 60 + "╝\n")

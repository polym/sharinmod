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

# connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URI, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_db():
    with Session(engine) as session:
        yield session


# TODO: Replace with sharinmod-specific initialization (users, tokens)
# This function will be updated when implementing user and token management
def initialize_sharinmod_data(db: Session):
    """
    Initialize sharinmod-specific data structures.
    Currently a placeholder - will be implemented in future stories.
    """
    pass

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi_pagination import  add_pagination
from sqlalchemy.exc import IntegrityError

from api.config import Settings
from api.database import create_db_and_tables, initialize_sharinmod_data, get_db

from alembic.config import Config
from alembic import command
from api.public.routes import public_router
from api.routers.user import router as user_router
from api.routers.auth import router as auth_router
from api.routers.api_key_usage import router as api_key_usage_router
from api.routers.shared_api_key import router as shared_api_key_router
from api.routers.unified_api_key import router as unified_api_key_router
from api.routers.api_key_discovery import router as api_key_discovery_router
from api.routers.models import router as models_router
from api.routers.webhooks import router as webhooks_router
from api.routers.usage import router as usage_router
from api.routers.oauth import router as oauth_router
from api.middleware.ip_whitelist import ip_whitelist_middleware
from api.utils import *
from prometheus_fastapi_instrumentator import Instrumentator
import redis.asyncio as redis
from fastapi import FastAPI
from dotenv import load_dotenv
import os
from fastapi_limiter import FastAPILimiter

env_path = "../.env"
load_dotenv(env_path)

REDIS_ENV = os.getenv("REDIS_DATABASE" ,"redis://redis:6379/")


def run_alembic_migrations():
    """运行 Alembic 数据库迁移"""
    try:
        alembic_dir = os.path.join(os.path.dirname(__file__), "alembic")
        alembic_ini = os.path.join(os.path.dirname(__file__), "alembic.ini")
        config = Config(alembic_ini)
        config.set_main_option("script_location", alembic_dir)
        # 使用环境变量中的 DATABASE_URI
        database_uri = os.getenv("DATABASE_URI")
        if database_uri:
            config.set_main_option("sqlalchemy.url", database_uri)
        command.upgrade(config, "head")
        print("✓ Alembic migrations applied successfully")
    except Exception as e:
        print(f"⚠ Alembic migration warning: {e}")
        # 迁移失败不阻止应用启动，后续会使用 create_db_and_tables 作为兜底


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 首先运行 Alembic 迁移
    run_alembic_migrations()

    db = next(get_db())  # Fetching the database session
    create_db_and_tables()  # 作为兜底，创建任何可能缺失的表
    redis_connection= redis.from_url(REDIS_ENV, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_connection)
    try:
        initialize_sharinmod_data(db)
        yield
    except (IntegrityError, Exception) as e:
        yield


def create_app(settings: Settings):
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        docs_url="/docs",
        description=settings.DESCRIPTION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://frontend:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add SessionMiddleware for OAuth
    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    # Add IP whitelist middleware for webhooks
    app.middleware("http")(ip_whitelist_middleware)

    # Health check endpoint
    @app.get("/")
    async def health_check():
        return {"status": "healthy", "service": "sharinmod-backend"}

    app.include_router(public_router)
    app.include_router(user_router)
    app.include_router(auth_router)
    app.include_router(oauth_router)
    app.include_router(api_key_usage_router)
    app.include_router(shared_api_key_router)
    app.include_router(unified_api_key_router)
    app.include_router(api_key_discovery_router)
    app.include_router(models_router)
    app.include_router(webhooks_router)
    app.include_router(usage_router)
    Instrumentator().instrument(app).expose(app)
    add_pagination(app)
    return app

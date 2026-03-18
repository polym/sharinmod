from contextlib import asynccontextmanager
import logging
import os
import traceback

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi_pagination import add_pagination
from sqlalchemy.exc import IntegrityError

# 日志由 asgi.py 统一配置；此处只获取模块 logger
# 若在非 asgi 上下文中使用，basicConfig 作为兜底
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from api.config import Settings
from api.database import create_db_and_tables, initialize_sharinmod_data, initialize_admin_user, get_db

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
from api.routers.admin import router as admin_router
from api.routers.claw import router as claw_router
from api.middleware.ip_whitelist import ip_whitelist_middleware
from api.utils import *
from prometheus_fastapi_instrumentator import Instrumentator
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter


def run_alembic_migrations(settings: Settings):
    """运行 Alembic 数据库迁移"""
    try:
        alembic_dir = os.path.join(os.path.dirname(__file__), "alembic")
        alembic_ini = os.path.join(os.path.dirname(__file__), "alembic.ini")
        config = Config(alembic_ini)
        config.set_main_option("script_location", alembic_dir)
        # 使用 settings 中的 DATABASE_URI
        if settings.DATABASE_URI:
            config.set_main_option("sqlalchemy.url", settings.DATABASE_URI)
        command.upgrade(config, "head")
        logger.info("✓ Alembic migrations applied successfully")
    except Exception as e:
        logger.warning(f"⚠ Alembic migration warning: {e}")
        # 迁移失败不阻止应用启动，后续会使用 create_db_and_tables 作为兜底


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 首先运行 Alembic 迁移
    run_alembic_migrations(app.state.settings)

    db = next(get_db())  # Fetching the database session
    create_db_and_tables()  # 作为兜底，创建任何可能缺失的表
    redis_connection = redis.from_url(
        app.state.settings.REDIS_DATABASE,
        encoding="utf-8",
        decode_responses=True
    )
    await FastAPILimiter.init(redis_connection)
    try:
        initialize_sharinmod_data(db)
        initialize_admin_user(db)
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
    # Store settings in app state for access in lifespan
    app.state.settings = settings

    # 添加全局异常处理器
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            f"Unhandled exception on {request.method} {request.url}: {str(exc)}\n{traceback.format_exc()}"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "error": str(exc)}
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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
    app.include_router(admin_router)
    app.include_router(claw_router)
    Instrumentator().instrument(app).expose(app)
    add_pagination(app)
    return app

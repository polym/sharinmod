from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import  add_pagination
from sqlalchemy.exc import IntegrityError

from api.config import Settings
from api.database import create_db_and_tables, initialize_sharinmod_data, get_db
from api.public.routes import public_router
from api.routers.user import router as user_router
from api.routers.auth import router as auth_router
from api.routers.token_usage import router as token_usage_router
from api.routers.shared_token import router as shared_token_router
from api.routers.unified_token import router as unified_token_router
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = next(get_db())  # Fetching the database session
    create_db_and_tables()
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

    # Health check endpoint
    @app.get("/")
    async def health_check():
        return {"status": "healthy", "service": "sharinmod-backend"}

    app.include_router(public_router)
    app.include_router(user_router)
    app.include_router(auth_router)
    app.include_router(token_usage_router)
    app.include_router(shared_token_router)
    app.include_router(unified_token_router)
    Instrumentator().instrument(app).expose(app)
    add_pagination(app)
    return app

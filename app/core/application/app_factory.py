import logging

from fastapi import FastAPI, status, Depends
from fastapi.openapi.utils import get_openapi
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from config import settings
from app.core.exceptions import ErrorCode, setup_exception_handlers
from app.core.middleware import JWTAuthMiddleware
from app.auth.routers.auth_router import router as auth_router
from scheduler import shutdown_scheduler, start_scheduler
from app.question.routers.question_router import router as question_router
from app.users.routers.users_router import router as users_router
from app.vote.routers.vote_router import router as vote_router
from app.core.database import engine
from app.core.observability import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.core.cache import RedisClient
from app.base.response import BaseResponse, api_errors, apply_error_code_responses

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    setup_logging(settings.log_level)

    auth_header = APIKeyHeader(name="Authorization", auto_error=False)

    app = FastAPI(
        title="Selec Backend API",
        description=f"Selec Backend API - {settings.active_profile.upper()} Environment",
        debug=settings.debug,
        version="1.0.0",
        dependencies=[Depends(auth_header)],
    )

    setup_exception_handlers(app)

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        JWTAuthMiddleware,
        allow_paths=(
            "/api/auth/**",
            "/actuator/**",
        ),
    )

    app.add_middleware(RequestLoggingMiddleware)

    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(question_router)
    app.include_router(vote_router)

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
        )
        app.openapi_schema = apply_error_code_responses(openapi_schema)
        return app.openapi_schema

    app.openapi = custom_openapi

    @app.get(
        "/actuator/health",
        response_model=BaseResponse[dict],
        status_code=status.HTTP_200_OK,
        responses={
            **api_errors(ErrorCode.INTERNAL_SERVER_ERROR),
        },
    )
    async def health_check():
        health_data = {"status": "healthy", "environment": settings.active_profile}
        return BaseResponse.of_success(status.HTTP_200_OK, health_data)

    @app.on_event("startup")
    async def startup_event():
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info(
                "DB connection succeeded",
            )
        except Exception as e:
            logger.warning(
                "DB connection failed",
                extra={"error": str(e)},
            )

        try:
            await RedisClient.get_client()
            logger.info(
                "Redis connection succeeded",
                extra={
                    "redis_host": settings.redis_host,
                    "redis_port": settings.redis_port,
                },
            )
        except Exception as e:
            logger.warning(
                "Redis connection failed",
                extra={"error": str(e)},
            )

        start_scheduler()

        logger.info(
            "Selec Backend started",
            extra={
                "debug": settings.debug,
                "log_level": settings.log_level,
                "scheduler_enabled": settings.scheduler_enabled,
            },
        )

    @app.on_event("shutdown")
    async def shutdown_event():
        shutdown_scheduler()
        await RedisClient.close()
        logger.info("Redis connection closed")

    return app

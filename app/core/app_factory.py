import logging

from fastapi import FastAPI, status, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from config import settings
from app.core.exception import setup_exception_handlers
from app.core.jwt_filter import JWTAuthMiddleware
from app.auth.routers.auth_router import router as auth_router
from app.question.routers.question_router import router as question_router
from app.users.routers.users_router import router as users_router
from app.vote.routers.vote_router import router as vote_router
from app.core.connection_config import engine
from app.core.logging_config import setup_logging
from app.core.redis_config import RedisClient
from app.base.base_response import BaseResponse
from app.base.openapi_responses import ERROR_500

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    setup_logging(settings.log_level, settings.active_profile)

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

    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(question_router)
    app.include_router(vote_router)

    @app.get(
        "/actuator/health",
        response_model=BaseResponse[dict],
        status_code=status.HTTP_200_OK,
        responses={500: ERROR_500},
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
                extra={"event": "db_connection_succeeded"},
            )
        except Exception as e:
            logger.warning(
                "DB connection failed",
                extra={"event": "db_connection_failed", "error": str(e)},
            )

        try:
            await RedisClient.get_client()
            logger.info(
                "Redis connection succeeded",
                extra={
                    "event": "redis_connection_succeeded",
                    "redis_host": settings.redis_host,
                    "redis_port": settings.redis_port,
                },
            )
        except Exception as e:
            logger.warning(
                "Redis connection failed",
                extra={"event": "redis_connection_failed", "error": str(e)},
            )

        logger.info(
            "Selec Backend started",
            extra={
                "event": "application_started",
                "debug": settings.debug,
                "log_level": settings.log_level,
            },
        )

    @app.on_event("shutdown")
    async def shutdown_event():
        await RedisClient.close()
        logger.info("Redis connection closed", extra={"event": "redis_connection_closed"})

    return app

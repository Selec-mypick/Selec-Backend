from fastapi import FastAPI, status, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from app.core.exception import setup_exception_handlers
from app.core.jwt_filter import JWTAuthMiddleware
from app.auth.routers.auth_router import router as auth_router
from app.question.routers.question_router import router as question_router
from app.vote.routers.vote_router import router as vote_router
from app.core.migration import auto_update_schema
from app.core.redis_config import RedisClient
from app.base.base_response import BaseResponse
from app.base.openapi_responses import ERROR_500


def create_app() -> FastAPI:
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
            "/auth/**",
            "/actuator/**",
        ),
    )

    app.include_router(auth_router)
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
        print("🔄 자동 스키마 업데이트 시작...")
        await auto_update_schema()

        try:
            await RedisClient.get_client()
            if settings.debug:
                print(f"✅ Redis 연결 성공: {settings.redis_host}:{settings.redis_port}")
        except Exception as e:
            print(f"⚠️ Redis 연결 실패: {str(e)}")

        if settings.debug:
            print(f"🚀 Selec Backend 시작됨 - 환경: {settings.active_profile}")
            print(f"📊 데이터베이스: {settings.database_url}")
            print(f"🐛 디버그 모드: {settings.debug}")
            print(f"📝 로그 레벨: {settings.log_level}")
        else:
            print(f"AdEdge Backend started - Environment: {settings.active_profile}")

    @app.on_event("shutdown")
    async def shutdown_event():
        await RedisClient.close()
        if settings.debug:
            print("🔌 Redis 연결 종료됨")

    return app

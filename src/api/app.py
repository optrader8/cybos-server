"""
FastAPI Application - FastAPI 앱 생성

REST API 서버 애플리케이션을 생성합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os

from .routes import (
    health_router, stocks_router, prices_router,
    pairs_router, signals_router, cointegration_router, trading_router,
    websocket_router, start_price_streaming
)
from .middleware.cors import setup_cors
from .middleware.logging import LoggingMiddleware, setup_logging


def create_app() -> FastAPI:
    """
    FastAPI 애플리케이션 생성

    Returns:
        FastAPI 애플리케이션 인스턴스
    """
    # 로깅 설정
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(log_level)

    # FastAPI 앱 생성
    app = FastAPI(
        title="Cybos Plus REST API Server",
        description="실시간 국내 주식 시세 API 서버",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # CORS 설정
    setup_cors(app)

    # 로깅 미들웨어 추가
    app.add_middleware(LoggingMiddleware)

    # 라우터 등록
    app.include_router(health_router)
    app.include_router(stocks_router)
    app.include_router(prices_router)
    app.include_router(pairs_router)
    app.include_router(signals_router)
    app.include_router(cointegration_router)
    app.include_router(trading_router)
    app.include_router(websocket_router)

    # Startup 이벤트
    @app.on_event("startup")
    async def startup_event():
        """애플리케이션 시작 시 실행"""
        # WebSocket 실시간 스트리밍 시작
        await start_price_streaming()

        # Signal Generator 시작 (환경변수에서 활성화 여부 확인)
        if os.getenv("SIGNAL_GENERATOR_ENABLED", "false").lower() == "true":
            from ...services import start_monitor
            await start_monitor()
            print("✅ Signal generator started")

    # 루트 엔드포인트
    @app.get("/")
    async def root():
        """루트 엔드포인트"""
        return {
            "service": "cybos-server",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
            "health": "/api/health",
            "websocket": "/ws/prices"
        }

    # 에러 핸들러
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """전역 예외 처리"""
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
                "path": str(request.url)
            }
        )

    print("✅ FastAPI application created successfully")
    print(f"   - Docs: http://localhost:8000/docs")
    print(f"   - Health: http://localhost:8000/api/health")
    print(f"   - WebSocket Prices: ws://localhost:8000/ws/prices")
    print(f"   - WebSocket Signals: ws://localhost:8000/ws/signals")

    return app

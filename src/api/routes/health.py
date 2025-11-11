"""
Health Check Router - 헬스체크 API

시스템 상태를 확인하는 API 엔드포인트를 제공합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Any
import os
import sqlite3

from ...cybos.connection.validator import validate_connection
from ...database.connection import get_connection_context
from ...database.models.stock import StockTable, MarketKind

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """
    기본 헬스체크

    시스템이 정상적으로 동작하는지 확인합니다.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "cybos-server",
        "version": "1.0.0"
    }


@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health_check():
    """
    상세 헬스체크

    Cybos Plus 연결, 데이터베이스, 시스템 리소스 등을 확인합니다.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "cybos-server",
        "version": "1.0.0",
        "components": {}
    }

    # 1. Cybos Plus 연결 상태 확인
    try:
        validation_result = validate_connection()
        health_status["components"]["cybos"] = {
            "status": "healthy" if validation_result["is_connected"] else "unhealthy",
            "connected": validation_result["is_connected"],
            "details": validation_result
        }
    except Exception as e:
        health_status["components"]["cybos"] = {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # 2. 데이터베이스 연결 확인
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")
    try:
        with get_connection_context(db_path) as conn:
            # 데이터베이스 기본 정보 조회
            cursor = conn.cursor()

            # 전체 종목 수
            kospi_stocks = StockTable.get_stocks_by_market(conn, MarketKind.KOSPI)
            kosdaq_stocks = StockTable.get_stocks_by_market(conn, MarketKind.KOSDAQ)

            # 최근 시세 데이터 확인
            cursor.execute("SELECT COUNT(*) FROM prices")
            price_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT MAX(created_at)
                FROM prices
            """)
            latest_price = cursor.fetchone()[0]

            health_status["components"]["database"] = {
                "status": "healthy",
                "path": db_path,
                "exists": os.path.exists(db_path),
                "size_mb": os.path.getsize(db_path) / (1024 * 1024) if os.path.exists(db_path) else 0,
                "statistics": {
                    "total_stocks": len(kospi_stocks) + len(kosdaq_stocks),
                    "kospi_stocks": len(kospi_stocks),
                    "kosdaq_stocks": len(kosdaq_stocks),
                    "price_records": price_count,
                    "latest_price_at": latest_price
                }
            }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # 3. 시스템 리소스 확인
    try:
        import psutil
        health_status["components"]["system"] = {
            "status": "healthy",
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
    except ImportError:
        health_status["components"]["system"] = {
            "status": "unavailable",
            "message": "psutil not installed"
        }
    except Exception as e:
        health_status["components"]["system"] = {
            "status": "error",
            "error": str(e)
        }

    return health_status


@router.get("/ready", response_model=Dict[str, bool])
async def readiness_check():
    """
    Readiness 체크

    서비스가 트래픽을 받을 준비가 되었는지 확인합니다.
    """
    try:
        # Cybos Plus 연결 확인
        validation_result = validate_connection()
        if not validation_result["is_connected"]:
            raise HTTPException(status_code=503, detail="Cybos Plus not connected")

        # 데이터베이스 확인
        db_path = os.getenv("DATABASE_PATH", "data/cybos.db")
        if not os.path.exists(db_path):
            raise HTTPException(status_code=503, detail="Database not found")

        return {"ready": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


@router.get("/live", response_model=Dict[str, bool])
async def liveness_check():
    """
    Liveness 체크

    서비스가 살아있는지 확인합니다.
    """
    return {"alive": True}

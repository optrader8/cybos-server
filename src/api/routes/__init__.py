"""
API Routes - REST API 엔드포인트

FastAPI 라우터를 정의합니다.
"""

from .health import router as health_router
from .stocks import router as stocks_router
from .prices import router as prices_router
from .pairs import router as pairs_router
from .signals import router as signals_router
from .cointegration import router as cointegration_router
from .trading import router as trading_router
from .websocket import router as websocket_router, start_price_streaming

__all__ = [
    "health_router",
    "stocks_router",
    "prices_router",
    "pairs_router",
    "signals_router",
    "cointegration_router",
    "trading_router",
    "websocket_router",
    "start_price_streaming"
]

"""
API Schemas - Pydantic 스키마 정의

REST API 요청/응답 스키마를 정의합니다.
"""

from .stock import (
    StockResponse,
    StockListResponse,
    StockSyncRequest,
    StockSyncResponse
)
from .price import (
    PriceResponse,
    PriceListResponse,
    HistoricalPriceResponse,
    HistoricalPriceListResponse
)
from .pair import (
    PairResponse,
    PairListResponse,
    PairCreateRequest,
    PairUpdateRequest,
    PairAnalysisRequest,
    PairAnalysisResponse
)
from .signal import (
    SignalResponse,
    SignalListResponse,
    SignalCreateRequest,
    SignalUpdateRequest,
    SignalExecuteRequest,
    SignalExecuteResponse
)
from .cointegration import (
    CointegrationResponse,
    CointegrationListResponse,
    CointegrationAnalyzeRequest,
    CointegrationAnalyzeResponse
)
from .trading import (
    BacktestRequest,
    BacktestResponse,
    PortfolioResponse,
    TradeExecutionRequest,
    TradeExecutionResponse,
    PerformanceResponse
)

__all__ = [
    # Stock schemas
    "StockResponse",
    "StockListResponse",
    "StockSyncRequest",
    "StockSyncResponse",
    # Price schemas
    "PriceResponse",
    "PriceListResponse",
    "HistoricalPriceResponse",
    "HistoricalPriceListResponse",
    # Pair schemas
    "PairResponse",
    "PairListResponse",
    "PairCreateRequest",
    "PairUpdateRequest",
    "PairAnalysisRequest",
    "PairAnalysisResponse",
    # Signal schemas
    "SignalResponse",
    "SignalListResponse",
    "SignalCreateRequest",
    "SignalUpdateRequest",
    "SignalExecuteRequest",
    "SignalExecuteResponse",
    # Cointegration schemas
    "CointegrationResponse",
    "CointegrationListResponse",
    "CointegrationAnalyzeRequest",
    "CointegrationAnalyzeResponse",
    # Trading schemas
    "BacktestRequest",
    "BacktestResponse",
    "PortfolioResponse",
    "TradeExecutionRequest",
    "TradeExecutionResponse",
    "PerformanceResponse"
]

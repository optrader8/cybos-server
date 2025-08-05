"""
Core Types - 시스템 전반에서 사용되는 타입 정의

Cybos Plus 시세 서버에서 사용하는 핵심 데이터 타입들을 정의합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from typing import Dict, List, Optional, Union, Tuple, Any, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


class MarketType(Enum):
    """시장 구분"""
    KOSPI = "KOSPI"
    KOSDAQ = "KOSDAQ"
    KONEX = "KONEX"
    ETF = "ETF"
    ETN = "ETN"


class StockStatus(Enum):
    """종목 상태"""
    NORMAL = "정상"
    SUSPENDED = "거래정지"
    DELISTED = "상장폐지"
    HALT = "거래중단"


class PriceType(Enum):
    """가격 유형"""
    CURRENT = "현재가"
    OPEN = "시가"
    HIGH = "고가"
    LOW = "저가"
    CLOSE = "종가"


class OrderType(Enum):
    """주문 유형"""
    BUY = "매수"
    SELL = "매도"


@dataclass
class StockInfo:
    """주식 기본 정보"""
    code: str
    name: str
    market_type: MarketType
    status: StockStatus
    industry_code: Optional[str] = None
    margin_rate: Optional[float] = None
    min_trading_unit: Optional[int] = None
    
    def __post_init__(self):
        """데이터 검증"""
        if not self.code or len(self.code) < 6:
            raise ValueError("Invalid stock code")
        if not self.name:
            raise ValueError("Stock name is required")


@dataclass
class PriceInfo:
    """시세 정보"""
    code: str
    timestamp: datetime
    current_price: Decimal
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    volume: Optional[int] = None
    amount: Optional[Decimal] = None
    change: Optional[Decimal] = None
    change_rate: Optional[float] = None
    
    def __post_init__(self):
        """데이터 검증"""
        if not self.code:
            raise ValueError("Stock code is required")
        if self.current_price <= 0:
            raise ValueError("Price must be positive")


@dataclass
class ConnectionStatus:
    """연결 상태 정보"""
    is_connected: bool
    server_type: int
    last_check: datetime
    error_message: Optional[str] = None
    
    @property
    def is_healthy(self) -> bool:
        """연결 상태가 정상인지 확인"""
        return self.is_connected and self.server_type > 0


@dataclass
class ApiLimitInfo:
    """API 호출 제한 정보"""
    limit_type: str
    remaining_count: int
    remaining_time: int  # milliseconds
    
    @property
    def can_request(self) -> bool:
        """요청 가능 여부"""
        return self.remaining_count > 0


# 타입 별칭들
StockCode = str
StockName = str
Price = Decimal
Volume = int
Timestamp = datetime

# 복합 타입들
StockDict = Dict[StockCode, StockInfo]
PriceDict = Dict[StockCode, PriceInfo]
ApiResponse = Dict[str, Any]

# 콜백 함수 타입들
PriceCallback = Callable[[PriceInfo], None]
ConnectionCallback = Callable[[ConnectionStatus], None]
ErrorCallback = Callable[[Exception], None]


class DatabaseConfig:
    """데이터베이스 설정"""
    
    def __init__(self, path: str = "./data/cybos.db"):
        self.path = path
        self.timeout = 30
        self.check_same_thread = False
        
    @property
    def connection_string(self) -> str:
        return f"sqlite:///{self.path}"


class ApiConfig:
    """API 서버 설정"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.debug = False
        self.cors_origins = ["*"]
        
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class RemoteConfig:
    """원격 서버 설정"""
    
    def __init__(self, url: str = None, api_key: str = None):
        self.url = url
        self.api_key = api_key
        self.timeout = 10
        self.retry_count = 3
        
    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.api_key)


# 상수들을 위한 기본 설정
DEFAULT_REQUEST_TIMEOUT = 5000  # milliseconds
DEFAULT_RETRY_COUNT = 3
DEFAULT_BATCH_SIZE = 100
MAX_CONCURRENT_REQUESTS = 10

# 로깅 관련 타입
from typing import Literal
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogMessage = str

"""
Core Constants - 시스템 전반에서 사용되는 상수 정의

Cybos Plus 시세 서버에서 사용하는 모든 상수들을 정의합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from typing import Dict, List

# === Cybos Plus COM 객체 관련 상수 ===

# COM 객체 ProgID
COM_CYBOS = "CpUtil.CpCybos"
COM_CODE_MGR = "CpUtil.CpCodeMgr"
COM_STOCK_CODE = "CpUtil.CpStockCode"

# 서버 타입
SERVER_TYPE_DISCONNECTED = 0
SERVER_TYPE_CYBOSPLUS = 1
SERVER_TYPE_HTS_NORMAL = 2

# API 제한 타입
LIMIT_TYPE_TRADE = 0      # 주문 관련 요청
LIMIT_TYPE_NONTRADE = 1   # 시세 관련 요청
LIMIT_TYPE_SUBSCRIBE = 2  # 실시간 구독

# === 시장 관련 상수 ===

# 시장 구분 코드
MARKET_CODE_KOSPI = "1"
MARKET_CODE_KOSDAQ = "2"
MARKET_CODE_FREEBOARD = "3"
MARKET_CODE_KRX = "4"

# 거래소 코드 매핑
MARKET_NAME_MAP = {
    "1": "KOSPI",
    "2": "KOSDAQ", 
    "3": "FREEBOARD",
    "4": "KRX"
}

# === 종목 관련 상수 ===

# 종목 코드 길이
STOCK_CODE_LENGTH = 6
FULL_STOCK_CODE_LENGTH = 8

# 종목 상태 코드
STOCK_STATUS_NORMAL = "0"
STOCK_STATUS_SUSPENDED = "1"
STOCK_STATUS_DELISTED = "2"
STOCK_STATUS_HALT = "3"

# === 시세 관련 상수 ===

# 시세 필드 ID (Cybos Plus)
FIELD_CODE = 0           # 종목코드
FIELD_NAME = 1           # 종목명
FIELD_TIME = 2           # 시간
FIELD_CURRENT_PRICE = 3  # 현재가
FIELD_CHANGE = 4         # 대비
FIELD_OPEN = 5          # 시가
FIELD_HIGH = 6          # 고가
FIELD_LOW = 7           # 저가
FIELD_VOLUME = 8        # 거래량
FIELD_AMOUNT = 9        # 거래대금

# 시세 데이터 포맷
PRICE_FIELD_MAP = {
    FIELD_CODE: "code",
    FIELD_NAME: "name", 
    FIELD_TIME: "time",
    FIELD_CURRENT_PRICE: "current_price",
    FIELD_CHANGE: "change",
    FIELD_OPEN: "open_price",
    FIELD_HIGH: "high_price",
    FIELD_LOW: "low_price",
    FIELD_VOLUME: "volume",
    FIELD_AMOUNT: "amount"
}

# === 데이터베이스 관련 상수 ===

# 테이블 이름
TABLE_STOCKS = "stocks"
TABLE_PRICES = "prices"
TABLE_PRICE_HISTORY = "price_history"
TABLE_METADATA = "metadata"

# 데이터베이스 설정
DB_TIMEOUT = 30
DB_MAX_CONNECTIONS = 10
DB_BATCH_SIZE = 1000

# SQL 쿼리 제한
MAX_QUERY_RESULTS = 10000
DEFAULT_PAGE_SIZE = 100

# === API 관련 상수 ===

# HTTP 상태 코드
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_ERROR = 500

# API 엔드포인트
API_PREFIX = "/api"
API_VERSION = "v1"

# API 경로
API_STOCKS = f"{API_PREFIX}/stocks"
API_PRICES = f"{API_PREFIX}/prices"
API_HEALTH = f"{API_PREFIX}/health"
API_STATUS = f"{API_PREFIX}/status"

# 요청 제한
API_RATE_LIMIT = 200  # requests per minute
API_REQUEST_TIMEOUT = 30  # seconds
API_MAX_CONCURRENT = 10

# === 시간 관련 상수 ===

# 시간대
TIMEZONE_KST = "Asia/Seoul"

# 거래 시간 (KST 기준)
MARKET_OPEN_TIME = "09:00:00"
MARKET_CLOSE_TIME = "15:30:00"

# 시간 포맷
TIME_FORMAT_ISO = "%Y-%m-%dT%H:%M:%S"
TIME_FORMAT_KST = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

# === 로깅 관련 상수 ===

# 로그 레벨
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"

# 로그 포맷
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 로그 파일 설정
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# === 성능 관련 상수 ===

# 요청 제한 (Cybos Plus)
CYBOS_REQUEST_LIMIT = 200  # per minute
CYBOS_REQUEST_INTERVAL = 300  # milliseconds

# 배치 처리
DEFAULT_BATCH_SIZE = 100
MAX_BATCH_SIZE = 1000

# 메모리 제한
MAX_CACHE_SIZE = 10000
CACHE_TTL = 300  # seconds

# === 파일 경로 관련 상수 ===

# 기본 디렉토리
DEFAULT_DATA_DIR = "./data"
DEFAULT_LOG_DIR = "./logs"
DEFAULT_CONFIG_DIR = "./config"

# 파일 확장자
DB_EXTENSION = ".db"
LOG_EXTENSION = ".log"
CONFIG_EXTENSION = ".py"

# === 네트워크 관련 상수 ===

# 연결 설정
DEFAULT_TIMEOUT = 10  # seconds
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 1  # seconds

# 원격 전송
REMOTE_BATCH_SIZE = 50
REMOTE_RETRY_INTERVAL = 5  # seconds

# === 환경 변수 키 ===

ENV_DATABASE_PATH = "DATABASE_PATH"
ENV_API_HOST = "API_HOST"
ENV_API_PORT = "API_PORT"
ENV_LOG_LEVEL = "LOG_LEVEL"
ENV_LOG_FILE = "LOG_FILE"
ENV_REMOTE_URL = "REMOTE_SERVER_URL"
ENV_REMOTE_API_KEY = "REMOTE_API_KEY"

# === 기본값들 ===

DEFAULT_VALUES = {
    ENV_DATABASE_PATH: f"{DEFAULT_DATA_DIR}/cybos.db",
    ENV_API_HOST: "0.0.0.0",
    ENV_API_PORT: "8000",
    ENV_LOG_LEVEL: LOG_LEVEL_INFO,
    ENV_LOG_FILE: f"{DEFAULT_LOG_DIR}/cybos-server.log",
}

# === 검증 규칙 ===

# 종목 코드 패턴 (정규식)
STOCK_CODE_PATTERN = r"^[A-Z]\d{6}$"
NUMERIC_CODE_PATTERN = r"^\d{6}$"

# 가격 범위
MIN_STOCK_PRICE = 1
MAX_STOCK_PRICE = 10000000  # 천만원

# 거래량 범위
MIN_VOLUME = 0
MAX_VOLUME = 999999999

# === 메시지 템플릿 ===

MESSAGE_TEMPLATES = {
    "connection_success": "Successfully connected to Cybos Plus (Server Type: {server_type})",
    "connection_failed": "Failed to connect to Cybos Plus: {reason}",
    "stock_updated": "Stock {code} ({name}) price updated: {price}",
    "api_limit_warning": "API limit warning: {remaining} requests remaining",
    "database_error": "Database error in {operation}: {error}",
    "remote_sent": "Data sent to remote server: {count} records",
}

# === 기타 설정 ===

# 애플리케이션 정보
APP_NAME = "Cybos Server"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Real-time stock price server based on Cybos Plus"

# 지원 플랫폼
SUPPORTED_PLATFORMS = ["win32"]
REQUIRED_PYTHON_VERSION = (3, 9)
REQUIRED_ARCHITECTURE = "32bit"

# 파일 크기 제한 (극단적 모듈화)
MAX_FILE_LINES = 300
MAX_FUNCTION_LINES = 50
MAX_CLASS_METHODS = 10

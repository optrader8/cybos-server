"""
Core Exceptions - 시스템 전반에서 사용되는 예외 정의

Cybos Plus 시세 서버에서 발생할 수 있는 모든 예외들을 정의합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from typing import Optional, Any, Dict


class CybosServerError(Exception):
    """모든 Cybos Server 예외의 기본 클래스"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Code: {self.error_code}, Details: {self.details})"
        return f"{self.message} (Code: {self.error_code})"


# === Connection 관련 예외 ===

class ConnectionError(CybosServerError):
    """Cybos Plus 연결 관련 예외"""
    pass


class NotConnectedError(ConnectionError):
    """Cybos Plus에 연결되지 않은 상태에서 작업 시도"""
    
    def __init__(self, message: str = "Cybos Plus is not connected"):
        super().__init__(message, "NOT_CONNECTED")


class ConnectionTimeoutError(ConnectionError):
    """연결 시간 초과"""
    
    def __init__(self, timeout_seconds: int):
        message = f"Connection timeout after {timeout_seconds} seconds"
        super().__init__(message, "CONNECTION_TIMEOUT", {"timeout": timeout_seconds})


class InvalidServerTypeError(ConnectionError):
    """잘못된 서버 타입"""
    
    def __init__(self, server_type: int):
        message = f"Invalid server type: {server_type}"
        super().__init__(message, "INVALID_SERVER_TYPE", {"server_type": server_type})


# === API 제한 관련 예외 ===

class ApiLimitError(CybosServerError):
    """API 호출 제한 관련 예외"""
    pass


class RequestLimitExceededError(ApiLimitError):
    """요청 한도 초과"""
    
    def __init__(self, limit_type: str, remaining_time: int):
        message = f"Request limit exceeded for {limit_type}. Wait {remaining_time}ms"
        super().__init__(message, "REQUEST_LIMIT_EXCEEDED", {
            "limit_type": limit_type,
            "remaining_time": remaining_time
        })


class TooManyRequestsError(ApiLimitError):
    """너무 많은 요청"""
    
    def __init__(self, retry_after: Optional[int] = None):
        message = "Too many requests"
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, "TOO_MANY_REQUESTS", details)


# === 데이터 관련 예외 ===

class DataError(CybosServerError):
    """데이터 관련 예외"""
    pass


class InvalidStockCodeError(DataError):
    """잘못된 종목 코드"""
    
    def __init__(self, code: str):
        message = f"Invalid stock code: {code}"
        super().__init__(message, "INVALID_STOCK_CODE", {"code": code})


class StockNotFoundError(DataError):
    """종목을 찾을 수 없음"""
    
    def __init__(self, code: str):
        message = f"Stock not found: {code}"
        super().__init__(message, "STOCK_NOT_FOUND", {"code": code})


class InvalidPriceDataError(DataError):
    """잘못된 시세 데이터"""
    
    def __init__(self, code: str, reason: str):
        message = f"Invalid price data for {code}: {reason}"
        super().__init__(message, "INVALID_PRICE_DATA", {"code": code, "reason": reason})


class DataValidationError(DataError):
    """데이터 검증 실패"""
    
    def __init__(self, field: str, value: Any, reason: str):
        message = f"Validation failed for {field}={value}: {reason}"
        super().__init__(message, "DATA_VALIDATION_ERROR", {
            "field": field,
            "value": value,
            "reason": reason
        })


# === 데이터베이스 관련 예외 ===

class DatabaseError(CybosServerError):
    """데이터베이스 관련 예외"""
    pass


class DatabaseConnectionError(DatabaseError):
    """데이터베이스 연결 실패"""
    
    def __init__(self, db_path: str, reason: str):
        message = f"Database connection failed: {reason}"
        super().__init__(message, "DB_CONNECTION_ERROR", {"db_path": db_path, "reason": reason})


class DatabaseQueryError(DatabaseError):
    """데이터베이스 쿼리 실패"""
    
    def __init__(self, query: str, error: str):
        message = f"Database query failed: {error}"
        super().__init__(message, "DB_QUERY_ERROR", {"query": query, "error": error})


class DatabaseMigrationError(DatabaseError):
    """데이터베이스 마이그레이션 실패"""
    
    def __init__(self, version: str, reason: str):
        message = f"Database migration to version {version} failed: {reason}"
        super().__init__(message, "DB_MIGRATION_ERROR", {"version": version, "reason": reason})


# === COM 객체 관련 예외 ===

class ComObjectError(CybosServerError):
    """COM 객체 관련 예외"""
    pass


class ComObjectCreateError(ComObjectError):
    """COM 객체 생성 실패"""
    
    def __init__(self, prog_id: str, reason: str):
        message = f"Failed to create COM object '{prog_id}': {reason}"
        super().__init__(message, "COM_OBJECT_CREATE_ERROR", {"prog_id": prog_id, "reason": reason})


class ComObjectMethodError(ComObjectError):
    """COM 객체 메서드 호출 실패"""
    
    def __init__(self, prog_id: str, method: str, reason: str):
        message = f"COM method '{method}' failed on '{prog_id}': {reason}"
        super().__init__(message, "COM_METHOD_ERROR", {
            "prog_id": prog_id,
            "method": method,
            "reason": reason
        })


# === 원격 전송 관련 예외 ===

class RemoteError(CybosServerError):
    """원격 서버 관련 예외"""
    pass


class RemoteConnectionError(RemoteError):
    """원격 서버 연결 실패"""
    
    def __init__(self, url: str, reason: str):
        message = f"Remote connection failed to {url}: {reason}"
        super().__init__(message, "REMOTE_CONNECTION_ERROR", {"url": url, "reason": reason})


class RemoteTransmissionError(RemoteError):
    """원격 전송 실패"""
    
    def __init__(self, url: str, data_type: str, reason: str):
        message = f"Failed to transmit {data_type} to {url}: {reason}"
        super().__init__(message, "REMOTE_TRANSMISSION_ERROR", {
            "url": url,
            "data_type": data_type,
            "reason": reason
        })


# === 설정 관련 예외 ===

class ConfigurationError(CybosServerError):
    """설정 관련 예외"""
    pass


class MissingConfigError(ConfigurationError):
    """필수 설정 누락"""
    
    def __init__(self, config_key: str):
        message = f"Missing required configuration: {config_key}"
        super().__init__(message, "MISSING_CONFIG", {"config_key": config_key})


class InvalidConfigError(ConfigurationError):
    """잘못된 설정값"""
    
    def __init__(self, config_key: str, value: Any, reason: str):
        message = f"Invalid configuration {config_key}={value}: {reason}"
        super().__init__(message, "INVALID_CONFIG", {
            "config_key": config_key,
            "value": value,
            "reason": reason
        })


# === 시스템 관련 예외 ===

class SystemError(CybosServerError):
    """시스템 관련 예외"""
    pass


class PlatformNotSupportedError(SystemError):
    """지원되지 않는 플랫폼"""
    
    def __init__(self, platform: str):
        message = f"Platform not supported: {platform}. Windows 32bit Python required."
        super().__init__(message, "PLATFORM_NOT_SUPPORTED", {"platform": platform})


class DependencyError(SystemError):
    """의존성 누락"""
    
    def __init__(self, dependency: str, reason: str):
        message = f"Missing dependency '{dependency}': {reason}"
        super().__init__(message, "DEPENDENCY_ERROR", {"dependency": dependency, "reason": reason})


# 예외 매핑 딕셔너리 (에러 코드 -> 예외 클래스)
ERROR_CODE_MAP = {
    "NOT_CONNECTED": NotConnectedError,
    "CONNECTION_TIMEOUT": ConnectionTimeoutError,
    "INVALID_SERVER_TYPE": InvalidServerTypeError,
    "REQUEST_LIMIT_EXCEEDED": RequestLimitExceededError,
    "TOO_MANY_REQUESTS": TooManyRequestsError,
    "INVALID_STOCK_CODE": InvalidStockCodeError,
    "STOCK_NOT_FOUND": StockNotFoundError,
    "INVALID_PRICE_DATA": InvalidPriceDataError,
    "DATA_VALIDATION_ERROR": DataValidationError,
}


def create_exception_from_code(error_code: str, message: str, details: Optional[Dict[str, Any]] = None) -> CybosServerError:
    """에러 코드로부터 적절한 예외 객체 생성"""
    exception_class = ERROR_CODE_MAP.get(error_code, CybosServerError)
    return exception_class(message, error_code, details)

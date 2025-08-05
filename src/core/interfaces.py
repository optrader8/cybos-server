"""
Core Interfaces - 시스템 전반에서 사용되는 인터페이스 정의

Cybos Plus 시세 서버의 핵심 인터페이스들을 정의합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime

from .types import (
    StockInfo, PriceInfo, ConnectionStatus, ApiLimitInfo,
    StockCode, PriceCallback, ConnectionCallback, ErrorCallback
)


class ICybosConnector(ABC):
    """Cybos Plus 연결 관리 인터페이스"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Cybos Plus에 연결"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """연결 해제"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        pass
    
    @abstractmethod
    def get_connection_status(self) -> ConnectionStatus:
        """상세 연결 상태 조회"""
        pass
    
    @abstractmethod
    def get_limit_info(self, limit_type: int) -> ApiLimitInfo:
        """API 제한 정보 조회"""
        pass


class IStockCodeManager(ABC):
    """종목 코드 관리 인터페이스"""
    
    @abstractmethod
    def get_stock_info(self, code: StockCode) -> Optional[StockInfo]:
        """종목 정보 조회"""
        pass
    
    @abstractmethod
    def get_all_stocks(self) -> List[StockInfo]:
        """전체 종목 목록 조회"""
        pass
    
    @abstractmethod
    def code_to_name(self, code: StockCode) -> Optional[str]:
        """종목 코드를 종목명으로 변환"""
        pass
    
    @abstractmethod
    def name_to_code(self, name: str) -> Optional[StockCode]:
        """종목명을 종목 코드로 변환"""
        pass
    
    @abstractmethod
    def update_stock_list(self) -> int:
        """종목 목록 업데이트"""
        pass


class IPriceProvider(ABC):
    """시세 데이터 제공 인터페이스"""
    
    @abstractmethod
    def get_current_price(self, code: StockCode) -> Optional[PriceInfo]:
        """현재가 조회"""
        pass
    
    @abstractmethod
    def get_price_history(self, code: StockCode, days: int = 30) -> List[PriceInfo]:
        """과거 시세 조회"""
        pass
    
    @abstractmethod
    def subscribe_realtime(self, code: StockCode, callback: PriceCallback) -> bool:
        """실시간 시세 구독"""
        pass
    
    @abstractmethod
    def unsubscribe_realtime(self, code: StockCode) -> bool:
        """실시간 시세 구독 해제"""
        pass
    
    @abstractmethod
    def get_subscribed_codes(self) -> List[StockCode]:
        """구독 중인 종목 목록"""
        pass


class IRepository(ABC):
    """기본 리포지토리 인터페이스"""
    
    @abstractmethod
    def create(self, entity: Any) -> Any:
        """엔티티 생성"""
        pass
    
    @abstractmethod
    def get_by_id(self, id: Any) -> Optional[Any]:
        """ID로 엔티티 조회"""
        pass
    
    @abstractmethod
    def update(self, entity: Any) -> bool:
        """엔티티 업데이트"""
        pass
    
    @abstractmethod
    def delete(self, id: Any) -> bool:
        """엔티티 삭제"""
        pass
    
    @abstractmethod
    def get_all(self, limit: Optional[int] = None) -> List[Any]:
        """전체 엔티티 조회"""
        pass


class IStockRepository(IRepository):
    """주식 정보 리포지토리 인터페이스"""
    
    @abstractmethod
    def get_by_code(self, code: StockCode) -> Optional[StockInfo]:
        """종목 코드로 주식 정보 조회"""
        pass
    
    @abstractmethod
    def get_by_name(self, name: str) -> Optional[StockInfo]:
        """종목명으로 주식 정보 조회"""
        pass
    
    @abstractmethod
    def get_by_market(self, market_type: str) -> List[StockInfo]:
        """시장별 주식 목록 조회"""
        pass
    
    @abstractmethod
    def bulk_upsert(self, stocks: List[StockInfo]) -> int:
        """주식 정보 일괄 삽입/업데이트"""
        pass


class IPriceRepository(IRepository):
    """시세 정보 리포지토리 인터페이스"""
    
    @abstractmethod
    def get_latest_price(self, code: StockCode) -> Optional[PriceInfo]:
        """최신 시세 조회"""
        pass
    
    @abstractmethod
    def get_price_history(self, code: StockCode, start_date: datetime, end_date: datetime) -> List[PriceInfo]:
        """기간별 시세 조회"""
        pass
    
    @abstractmethod
    def save_price(self, price: PriceInfo) -> bool:
        """시세 정보 저장"""
        pass
    
    @abstractmethod
    def bulk_save_prices(self, prices: List[PriceInfo]) -> int:
        """시세 정보 일괄 저장"""
        pass


class IRemoteClient(ABC):
    """원격 클라이언트 인터페이스"""
    
    @abstractmethod
    def connect(self) -> bool:
        """원격 서버에 연결"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """연결 해제"""
        pass
    
    @abstractmethod
    def send_data(self, data: Dict[str, Any]) -> bool:
        """데이터 전송"""
        pass
    
    @abstractmethod
    def send_batch(self, data_list: List[Dict[str, Any]]) -> int:
        """배치 데이터 전송"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        pass


class IDataFormatter(ABC):
    """데이터 포맷터 인터페이스"""
    
    @abstractmethod
    def format_stock_info(self, stock: StockInfo) -> Dict[str, Any]:
        """주식 정보 포맷팅"""
        pass
    
    @abstractmethod
    def format_price_info(self, price: PriceInfo) -> Dict[str, Any]:
        """시세 정보 포맷팅"""
        pass
    
    @abstractmethod
    def format_batch_data(self, data_list: List[Any]) -> Dict[str, Any]:
        """배치 데이터 포맷팅"""
        pass


class ILogger(ABC):
    """로거 인터페이스"""
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """디버그 로그"""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """정보 로그"""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """경고 로그"""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """에러 로그"""
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """치명적 에러 로그"""
        pass


class IConfigManager(ABC):
    """설정 관리 인터페이스"""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """설정값 조회"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """설정값 설정"""
        pass
    
    @abstractmethod
    def get_database_config(self) -> Dict[str, Any]:
        """데이터베이스 설정 조회"""
        pass
    
    @abstractmethod
    def get_api_config(self) -> Dict[str, Any]:
        """API 설정 조회"""
        pass
    
    @abstractmethod
    def get_remote_config(self) -> Dict[str, Any]:
        """원격 서버 설정 조회"""
        pass


class IEventBus(ABC):
    """이벤트 버스 인터페이스"""
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """이벤트 구독"""
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """이벤트 구독 해제"""
        pass
    
    @abstractmethod
    def publish(self, event_type: str, data: Any) -> None:
        """이벤트 발행"""
        pass


class IService(ABC):
    """기본 서비스 인터페이스"""
    
    @abstractmethod
    def start(self) -> bool:
        """서비스 시작"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """서비스 중지"""
        pass
    
    @abstractmethod
    def is_running(self) -> bool:
        """실행 상태 확인"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """서비스 상태 조회"""
        pass


class IStockService(IService):
    """주식 서비스 인터페이스"""
    
    @abstractmethod
    def get_stock_info(self, code: StockCode) -> Optional[StockInfo]:
        pass
    
    @abstractmethod
    def sync_stock_codes(self) -> int:
        pass


class IPriceService(IService):
    """시세 서비스 인터페이스"""
    
    @abstractmethod
    def get_current_price(self, code: StockCode) -> Optional[PriceInfo]:
        pass
    
    @abstractmethod
    def start_realtime_monitoring(self, codes: List[StockCode]) -> bool:
        pass
    
    @abstractmethod
    def stop_realtime_monitoring(self) -> None:
        pass

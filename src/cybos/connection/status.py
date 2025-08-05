"""
Connection Status - Cybos Plus 연결 상태 확인

Cybos Plus의 연결 상태를 확인하고 모니터링하는 기능을 제공합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import win32com.client
from datetime import datetime
from typing import Optional

from ...core.types import ConnectionStatus
from ...core.constants import (
    COM_CYBOS, 
    SERVER_TYPE_DISCONNECTED, 
    SERVER_TYPE_CYBOSPLUS, 
    SERVER_TYPE_HTS_NORMAL
)
from ...core.exceptions import (
    ComObjectCreateError, 
    ComObjectMethodError,
    NotConnectedError
)


class CybosConnectionStatus:
    """Cybos Plus 연결 상태 관리 클래스"""
    
    def __init__(self):
        self._cybos_obj: Optional[object] = None
        self._last_check: Optional[datetime] = None
        
    def _get_cybos_object(self) -> object:
        """Cybos COM 객체 생성/반환"""
        if self._cybos_obj is None:
            try:
                self._cybos_obj = win32com.client.Dispatch(COM_CYBOS)
            except Exception as e:
                raise ComObjectCreateError(COM_CYBOS, str(e))
        return self._cybos_obj
    
    def check_connection(self) -> ConnectionStatus:
        """현재 연결 상태 확인"""
        try:
            cybos = self._get_cybos_object()
            is_connected = bool(cybos.IsConnect)
            server_type = int(cybos.ServerType)
            
            self._last_check = datetime.now()
            
            return ConnectionStatus(
                is_connected=is_connected,
                server_type=server_type,
                last_check=self._last_check,
                error_message=None
            )
            
        except Exception as e:
            return ConnectionStatus(
                is_connected=False,
                server_type=SERVER_TYPE_DISCONNECTED,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    def is_connected(self) -> bool:
        """간단한 연결 상태 확인"""
        try:
            cybos = self._get_cybos_object()
            return bool(cybos.IsConnect)
        except:
            return False
    
    def get_server_type(self) -> int:
        """서버 타입 조회"""
        try:
            cybos = self._get_cybos_object()
            return int(cybos.ServerType)
        except:
            return SERVER_TYPE_DISCONNECTED
    
    def get_server_type_name(self) -> str:
        """서버 타입명 조회"""
        server_type = self.get_server_type()
        
        type_names = {
            SERVER_TYPE_DISCONNECTED: "연결 끊김",
            SERVER_TYPE_CYBOSPLUS: "CybosPlus 서버",
            SERVER_TYPE_HTS_NORMAL: "HTS 일반 서버"
        }
        
        return type_names.get(server_type, f"알 수 없음 ({server_type})")
    
    def validate_connection(self) -> None:
        """연결 상태 검증 (예외 발생)"""
        status = self.check_connection()
        
        if not status.is_connected:
            raise NotConnectedError("Cybos Plus가 연결되지 않았습니다")
        
        if status.server_type == SERVER_TYPE_DISCONNECTED:
            raise NotConnectedError("서버 연결이 끊어졌습니다")
    
    def get_detailed_status(self) -> dict:
        """상세 연결 상태 정보"""
        status = self.check_connection()
        
        return {
            "is_connected": status.is_connected,
            "server_type": status.server_type,
            "server_type_name": self.get_server_type_name(),
            "last_check": status.last_check.isoformat() if status.last_check else None,
            "error_message": status.error_message,
            "is_healthy": status.is_healthy
        }
    
    def wait_for_connection(self, timeout_seconds: int = 30) -> bool:
        """연결될 때까지 대기"""
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            if self.is_connected():
                return True
            time.sleep(1)
        
        return False
    
    def refresh_connection(self) -> ConnectionStatus:
        """연결 상태 새로고침"""
        # COM 객체 재생성
        self._cybos_obj = None
        return self.check_connection()


# 전역 연결 상태 관리자 인스턴스
_connection_status = CybosConnectionStatus()


def get_connection_status() -> ConnectionStatus:
    """전역 연결 상태 조회"""
    return _connection_status.check_connection()


def is_connected() -> bool:
    """전역 연결 상태 확인"""
    return _connection_status.is_connected()


def validate_connection() -> None:
    """전역 연결 상태 검증"""
    _connection_status.validate_connection()


def get_server_type() -> int:
    """전역 서버 타입 조회"""
    return _connection_status.get_server_type()


def get_server_type_name() -> str:
    """전역 서버 타입명 조회"""
    return _connection_status.get_server_type_name()


def wait_for_connection(timeout_seconds: int = 30) -> bool:
    """전역 연결 대기"""
    return _connection_status.wait_for_connection(timeout_seconds)


def refresh_connection() -> ConnectionStatus:
    """전역 연결 상태 새로고침"""
    return _connection_status.refresh_connection()


def get_detailed_status() -> dict:
    """전역 상세 연결 상태"""
    return _connection_status.get_detailed_status()

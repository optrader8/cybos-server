"""
Connection Module - Cybos Plus 연결 관리

Cybos Plus의 연결 상태 확인 및 유효성 검증 기능을 제공합니다.
"""

from .status import *
from .validator import *

__all__ = [
    # Status functions
    "get_connection_status",
    "is_connected", 
    "validate_connection",
    "get_server_type",
    "get_server_type_name",
    "wait_for_connection",
    "refresh_connection",
    "get_detailed_status",
    
    # Validator functions
    "validate_platform",
    "validate_dependencies", 
    "validate_all",
    "generate_validation_report",
    "quick_validate"
]

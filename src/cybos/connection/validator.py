"""
Connection Validator - Cybos Plus 연결 유효성 검증

Cybos Plus 연결의 유효성을 검증하고 요구사항을 확인합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import platform
import sys
from typing import List, Dict, Any

from ...core.exceptions import (
    PlatformNotSupportedError,
    DependencyError,
    InvalidServerTypeError
)
from ...core.constants import (
    SUPPORTED_PLATFORMS,
    REQUIRED_PYTHON_VERSION,
    REQUIRED_ARCHITECTURE,
    SERVER_TYPE_CYBOSPLUS,
    SERVER_TYPE_HTS_NORMAL
)
from .status import get_connection_status, get_server_type


class ConnectionValidator:
    """Cybos Plus 연결 유효성 검증 클래스"""
    
    def __init__(self):
        self._validation_results: Dict[str, Any] = {}
    
    def validate_platform(self) -> bool:
        """플랫폼 검증 (Windows 32bit만 지원)"""
        current_platform = platform.system().lower()
        
        if current_platform not in [p.lower() for p in SUPPORTED_PLATFORMS]:
            raise PlatformNotSupportedError(current_platform)
        
        # 32bit Python 확인
        architecture = platform.architecture()[0]
        if "32" not in architecture and platform.machine().lower() != "x86":
            raise PlatformNotSupportedError(f"64bit Python detected: {architecture}")
        
        return True
    
    def validate_python_version(self) -> bool:
        """Python 버전 검증"""
        current_version = sys.version_info[:2]
        
        if current_version != REQUIRED_PYTHON_VERSION:
            required_str = f"{REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]}"
            current_str = f"{current_version[0]}.{current_version[1]}"
            
            raise DependencyError(
                f"Python {required_str}",
                f"Current version: {current_str}"
            )
        
        return True
    
    def validate_dependencies(self) -> bool:
        """필수 모듈 검증"""
        required_modules = [
            "win32com.client",
            "pywin32"
        ]
        
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            raise DependencyError(
                ", ".join(missing_modules),
                "Install with: pip install pywin32"
            )
        
        return True
    
    def validate_server_type(self) -> bool:
        """서버 타입 검증"""
        server_type = get_server_type()
        
        valid_types = [SERVER_TYPE_CYBOSPLUS, SERVER_TYPE_HTS_NORMAL]
        
        if server_type not in valid_types:
            raise InvalidServerTypeError(server_type)
        
        return True
    
    def validate_connection_health(self) -> bool:
        """연결 상태 건강성 검증"""
        status = get_connection_status()
        
        if not status.is_healthy:
            error_msg = status.error_message or "Connection is not healthy"
            raise ConnectionError(f"Connection validation failed: {error_msg}")
        
        return True
    
    def validate_all(self) -> Dict[str, Any]:
        """전체 검증 수행"""
        results = {
            "platform": False,
            "python_version": False,
            "dependencies": False,
            "server_type": False,
            "connection_health": False,
            "errors": [],
            "warnings": []
        }
        
        # 플랫폼 검증
        try:
            results["platform"] = self.validate_platform()
        except Exception as e:
            results["errors"].append(f"Platform validation failed: {e}")
        
        # Python 버전 검증
        try:
            results["python_version"] = self.validate_python_version()
        except Exception as e:
            results["errors"].append(f"Python version validation failed: {e}")
        
        # 의존성 검증
        try:
            results["dependencies"] = self.validate_dependencies()
        except Exception as e:
            results["errors"].append(f"Dependencies validation failed: {e}")
        
        # 서버 타입 검증
        try:
            results["server_type"] = self.validate_server_type()
        except Exception as e:
            results["errors"].append(f"Server type validation failed: {e}")
        
        # 연결 상태 검증
        try:
            results["connection_health"] = self.validate_connection_health()
        except Exception as e:
            results["errors"].append(f"Connection health validation failed: {e}")
        
        # 전체 성공 여부
        results["is_valid"] = all([
            results["platform"],
            results["python_version"], 
            results["dependencies"],
            results["server_type"],
            results["connection_health"]
        ])
        
        return results
    
    def get_system_info(self) -> Dict[str, Any]:
        """시스템 정보 수집"""
        return {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "architecture": platform.architecture(),
                "processor": platform.processor()
            },
            "python": {
                "version": sys.version,
                "version_info": sys.version_info,
                "executable": sys.executable,
                "platform": sys.platform,
                "maxsize": sys.maxsize
            },
            "cybos": {
                "connection_status": get_connection_status().__dict__,
                "server_type": get_server_type()
            }
        }
    
    def generate_report(self) -> str:
        """검증 보고서 생성"""
        validation_results = self.validate_all()
        system_info = self.get_system_info()
        
        report_lines = [
            "=== Cybos Plus Connection Validation Report ===",
            "",
            "## Validation Results:",
        ]
        
        for check, result in validation_results.items():
            if check not in ["errors", "warnings", "is_valid"]:
                status = "✅ PASS" if result else "❌ FAIL"
                report_lines.append(f"  - {check}: {status}")
        
        if validation_results["errors"]:
            report_lines.extend([
                "",
                "## Errors:",
            ])
            for error in validation_results["errors"]:
                report_lines.append(f"  - {error}")
        
        if validation_results["warnings"]:
            report_lines.extend([
                "",
                "## Warnings:",
            ])
            for warning in validation_results["warnings"]:
                report_lines.append(f"  - {warning}")
        
        report_lines.extend([
            "",
            "## System Information:",
            f"  - Platform: {system_info['platform']['system']} {system_info['platform']['architecture'][0]}",
            f"  - Python: {system_info['python']['version_info']}",
            f"  - Cybos Server Type: {system_info['cybos']['server_type']}",
        ])
        
        overall_status = "✅ VALID" if validation_results["is_valid"] else "❌ INVALID"
        report_lines.extend([
            "",
            f"## Overall Status: {overall_status}",
            ""
        ])
        
        return "\n".join(report_lines)


# 전역 검증자 인스턴스
_validator = ConnectionValidator()


def validate_platform() -> bool:
    """전역 플랫폼 검증"""
    return _validator.validate_platform()


def validate_dependencies() -> bool:
    """전역 의존성 검증"""
    return _validator.validate_dependencies()


def validate_all() -> Dict[str, Any]:
    """전역 전체 검증"""
    return _validator.validate_all()


def generate_validation_report() -> str:
    """전역 검증 보고서 생성"""
    return _validator.generate_report()


def quick_validate() -> bool:
    """빠른 검증 (예외 발생 시 False 반환)"""
    try:
        results = validate_all()
        return results["is_valid"]
    except:
        return False

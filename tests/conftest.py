"""
Test Configuration - 테스트 설정

pytest 실행을 위한 설정과 픽스처를 정의합니다.
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 테스트용 임포트
from src.database.connection import DatabaseManager


@pytest.fixture(scope="session")
def test_db_path():
    """테스트용 임시 데이터베이스 경로"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_cybos.db"
        yield str(db_path)


@pytest.fixture(scope="session") 
def production_db_path():
    """실제 운영 데이터베이스 경로"""
    return "data/cybos.db"


@pytest.fixture
def db_manager(test_db_path):
    """테스트용 데이터베이스 매니저"""
    manager = DatabaseManager(test_db_path)
    manager.initialize_database()
    return manager


@pytest.fixture
def production_db_manager(production_db_path):
    """운영 데이터베이스 매니저 (읽기 전용)"""
    db_file = Path(production_db_path)
    if not db_file.exists():
        pytest.skip(f"Production database not found: {production_db_path}")
    
    return DatabaseManager(production_db_path)


def pytest_configure(config):
    """pytest 설정"""
    # 사용자 정의 마커 등록
    config.addinivalue_line(
        "markers", "cybos: marks tests that require Cybos Plus connection"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """테스트 수집 후 수정"""
    # Cybos Plus 마커가 있는 테스트는 자동으로 integration으로 표시
    for item in items:
        if "cybos" in item.keywords:
            item.add_marker(pytest.mark.integration)
        
        # 느린 테스트 자동 표시
        if "integration" in item.keywords or "slow" in item.keywords:
            item.add_marker(pytest.mark.slow)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """테스트 환경 설정 (모든 테스트에 자동 적용)"""
    # 테스트 시작 전 설정
    original_path = sys.path.copy()
    
    yield
    
    # 테스트 종료 후 정리
    sys.path = original_path


def pytest_report_header(config):
    """테스트 보고서 헤더"""
    return [
        "Cybos Plus Stock Server Tests",
        "================================",
        f"Python version: {sys.version}",
        f"Platform: {sys.platform}",
    ]

"""
Database Connection Manager - SQLite 연결 관리

SQLite 데이터베이스 연결을 관리하고 초기화하는 모듈입니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional, List
from contextlib import contextmanager

from .models.stock import StockTable
from .models.price import PriceTable
from .models.history import HistoryTable
from .models.pair import PairTable
from .models.cointegration import CointegrationTable
from .models.signal import SignalTable


class DatabaseManager:
    """데이터베이스 연결 및 관리 클래스"""
    
    def __init__(self, db_path: str = "cybos.db"):
        self.db_path = Path(db_path)
        self._ensure_db_directory()
    
    def _ensure_db_directory(self) -> None:
        """DB 디렉토리 생성"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return conn
    
    @contextmanager
    def get_connection_context(self):
        """컨텍스트 매니저로 연결 관리"""
        conn = self.get_connection()
        try:
            yield conn
        finally:
            conn.close()
    
    def initialize_database(self) -> None:
        """데이터베이스 초기화 (테이블 생성)"""
        with self.get_connection_context() as conn:
            # 주식 테이블 생성
            StockTable.create_table(conn)
            StockTable.create_indexes(conn)

            # 시세 테이블 생성
            PriceTable.create_table(conn)
            PriceTable.create_indexes(conn)

            # 히스토리 테이블 생성
            HistoryTable.create_table(conn)
            HistoryTable.create_indexes(conn)

            # 페어 트레이딩 테이블 생성
            PairTable.create_table(conn)
            PairTable.create_indexes(conn)

            CointegrationTable.create_table(conn)
            CointegrationTable.create_indexes(conn)

            SignalTable.create_table(conn)
            SignalTable.create_indexes(conn)

            print(f"Database initialized at: {self.db_path}")
            print("✅ All tables created: stocks, prices, historical_prices, pairs, cointegration_results, pair_signals")
    
    def get_db_info(self) -> dict:
        """데이터베이스 정보 조회"""
        with self.get_connection_context() as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            info = {
                "db_path": str(self.db_path),
                "db_size": self.db_path.stat().st_size if self.db_path.exists() else 0,
                "tables": tables
            }
            
            # 각 테이블의 레코드 수 조회
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                info[f"{table}_count"] = cursor.fetchone()[0]
            
            return info
    
    def vacuum_database(self) -> None:
        """데이터베이스 최적화"""
        with self.get_connection_context() as conn:
            conn.execute("VACUUM")
            print("Database vacuumed successfully")
    
    def backup_database(self, backup_path: str) -> None:
        """데이터베이스 백업"""
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self.get_connection_context() as source:
            with sqlite3.connect(str(backup_path)) as backup:
                source.backup(backup)
        
        print(f"Database backed up to: {backup_path}")
    
    def restore_database(self, backup_path: str) -> None:
        """데이터베이스 복원"""
        backup_path = Path(backup_path)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # 기존 DB 파일 삭제
        if self.db_path.exists():
            self.db_path.unlink()
        
        # 백업에서 복원
        with sqlite3.connect(str(backup_path)) as backup:
            with self.get_connection_context() as target:
                backup.backup(target)
        
        print(f"Database restored from: {backup_path}")


# 전역 데이터베이스 매니저
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(db_path: str = "data/cybos.db") -> DatabaseManager:
    """전역 데이터베이스 매니저 반환"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager


def get_connection() -> sqlite3.Connection:
    """편의 함수: 데이터베이스 연결 반환"""
    return get_db_manager().get_connection()


@contextmanager
def get_connection_context(db_path: str = "data/cybos.db"):
    """편의 함수: 컨텍스트 매니저로 연결 관리"""
    with get_db_manager(db_path).get_connection_context() as conn:
        yield conn


def initialize_database(db_path: str = "data/cybos.db") -> None:
    """편의 함수: 데이터베이스 초기화"""
    get_db_manager(db_path).initialize_database()


def get_db_info(db_path: str = "data/cybos.db") -> dict:
    """편의 함수: 데이터베이스 정보 조회"""
    return get_db_manager(db_path).get_db_info()

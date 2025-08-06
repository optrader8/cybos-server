"""
History Model - 시세 이력 데이터 모델

일간, 주간, 월간 등 집계된 시세 이력(OHLCV)을 저장하는 SQLite 모델입니다.
시계열 분석을 위한 효율적인 데이터 조회를 목적으로 합니다.
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

class HistoryTimeframe(str, Enum):
    """
    시세 이력의 타임프레임 구분
    str을 상속하여 DB에 값을 직접 저장할 수 있도록 함
    """
    DAILY = 'D'
    WEEKLY = 'W'
    MONTHLY = 'M'

@dataclass
class HistoryInfo:
    """시세 이력 정보 데이터클래스 (OHLCV)"""
    
    # 식별 정보
    code: str                           # 종목코드
    timeframe: HistoryTimeframe         # 데이터 주기 (일/주/월)
    date: str                           # 기준 날짜 (YYYY-MM-DD)
    
    # 가격 정보 (OHLC)
    open_price: int = 0                 # 시가
    high_price: int = 0                 # 고가
    low_price: int = 0                  # 저가
    close_price: int = 0                # 종가
    
    # 거래량 정보
    volume: int = 0                     # 거래량 (주)
    amount: int = 0                     # 거래대금 (천원)
    
    # 메타데이터
    updated_at: Optional[str] = None    # 수정일시

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryInfo':
        """딕셔너리에서 생성"""
        return cls(**data)

class HistoryTable:
    """시세 이력 정보 테이블 관리 클래스"""
    
    TABLE_NAME = "historical_prices"
    
    CREATE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        code TEXT NOT NULL,
        timeframe TEXT NOT NULL,
        date TEXT NOT NULL,
        open_price INTEGER DEFAULT 0,
        high_price INTEGER DEFAULT 0,
        low_price INTEGER DEFAULT 0,
        close_price INTEGER DEFAULT 0,
        volume INTEGER DEFAULT 0,
        amount INTEGER DEFAULT 0,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (code, timeframe, date)
    )
    """
    
    @classmethod
    def create_table(cls, conn: sqlite3.Connection) -> None:
        """테이블 생성"""
        conn.execute(cls.CREATE_SQL)
        conn.commit()

    @classmethod
    def create_indexes(cls, conn: sqlite3.Connection) -> None:
        """시계열 분석을 위한 인덱스 생성"""
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_date ON {cls.TABLE_NAME}(date)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_code_date ON {cls.TABLE_NAME}(code, date)",
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        conn.commit()

    @classmethod
    def upsert_history(cls, conn: sqlite3.Connection, history: HistoryInfo) -> None:
        """
        시세 이력 정보 삽입 또는 업데이트 (UPSERT)
        복합 기본 키를 이용하여 데이터가 존재하면 교체(REPLACE)합니다.
        """
        history.updated_at = datetime.now().isoformat()
        
        history_dict = history.to_dict()
        
        placeholders = ", ".join([f":{k}" for k in history_dict.keys()])
        columns = ", ".join(history_dict.keys())
        
        sql = f"INSERT OR REPLACE INTO {cls.TABLE_NAME} ({columns}) VALUES ({placeholders})"
        conn.execute(sql, history_dict)

    @classmethod
    def get_history(
        cls, 
        conn: sqlite3.Connection, 
        code: str, 
        timeframe: HistoryTimeframe, 
        start_date: str, 
        end_date: str
    ) -> List[HistoryInfo]:
        """기간별 시세 이력 조회"""
        cursor = conn.execute(f"""
            SELECT * FROM {cls.TABLE_NAME} 
            WHERE code = ? 
              AND timeframe = ?
              AND date BETWEEN ? AND ?
            ORDER BY date ASC
        """, (code, timeframe.value, start_date, end_date))
        
        history_list = []
        columns = [desc[0] for desc in cursor.description]
        
        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            history_list.append(HistoryInfo.from_dict(data))
        
        return history_list

    @classmethod
    def get_latest_date(
        cls, 
        conn: sqlite3.Connection, 
        code: str, 
        timeframe: HistoryTimeframe
    ) -> Optional[str]:
        """특정 종목의 가장 최신 데이터 날짜 조회"""
        cursor = conn.execute(f"""
            SELECT MAX(date) FROM {cls.TABLE_NAME}
            WHERE code = ? AND timeframe = ?
        """, (code, timeframe.value))
        
        result = cursor.fetchone()
        return result[0] if result and result[0] else None
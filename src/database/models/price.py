"""
Price Model - 시세 데이터 모델

Cybos Plus에서 제공하는 시세 정보를 저장하는 SQLite 모델입니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import IntEnum


class PriceStatus(IntEnum):
    """시세 상태 구분"""
    UPPER_LIMIT = 1     # 상한
    RISE = 2            # 상승
    UNCHANGED = 3       # 보합
    LOWER_LIMIT = 4     # 하한
    FALL = 5            # 하락
    STRONG_UPPER = 6    # 기세상한
    STRONG_RISE = 7     # 기세상승
    STRONG_LOWER = 8    # 기세하한
    STRONG_FALL = 9     # 기세하락


class MarketPhase(IntEnum):
    """장 구분"""
    PRE_MARKET = 1      # 동시호가
    REGULAR = 2         # 장중


@dataclass
class PriceInfo:
    """시세 정보 데이터클래스"""
    
    # 기본 정보
    code: str                           # 종목코드
    name: str                           # 종목명
    time: str                           # 시간 (HHMM)
    
    # 가격 정보
    current_price: int = 0              # 현재가
    change: int = 0                     # 전일대비
    change_rate: float = 0.0            # 등락률
    status: int = 3                     # 상태구분 (기본: 보합)
    
    # OHLC
    open_price: int = 0                 # 시가
    high_price: int = 0                 # 고가
    low_price: int = 0                  # 저가
    prev_close: int = 0                 # 전일종가
    
    # 호가 정보
    ask_price: int = 0                  # 매도호가
    bid_price: int = 0                  # 매수호가
    
    # 거래량 정보
    volume: int = 0                     # 거래량 (주)
    amount: int = 0                     # 거래대금 (천원)
    total_ask_volume: int = 0           # 총매도잔량
    total_bid_volume: int = 0           # 총매수잔량
    
    # 기타 정보
    listed_shares: int = 0              # 상장주식수
    foreign_ratio: float = 0.0          # 외국인보유비율
    prev_volume: int = 0                # 전일거래량
    
    # 예상체결 정보
    expected_price: int = 0             # 예상체결가
    expected_change: int = 0            # 예상체결가 전일대비
    expected_status: int = 3            # 예상체결가 상태구분
    expected_volume: int = 0            # 예상체결가 거래량
    
    # 메타데이터
    market_phase: int = 2               # 장구분 (기본: 장중)
    created_at: Optional[str] = None    # 생성일시
    updated_at: Optional[str] = None    # 수정일시
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceInfo':
        """딕셔너리에서 생성"""
        return cls(**data)
    
    def get_change_rate(self) -> float:
        """등락률 계산"""
        if self.prev_close > 0:
            return (self.change / self.prev_close) * 100
        return 0.0
    
    def get_status_name(self) -> str:
        """상태명 반환"""
        status_names = {
            1: "상한", 2: "상승", 3: "보합", 4: "하한", 5: "하락",
            6: "기세상한", 7: "기세상승", 8: "기세하한", 9: "기세하락"
        }
        return status_names.get(self.status, "알 수 없음")


class PriceTable:
    """시세 정보 테이블 관리 클래스"""
    
    TABLE_NAME = "prices"
    
    CREATE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        time TEXT NOT NULL,
        current_price INTEGER DEFAULT 0,
        change INTEGER DEFAULT 0,
        change_rate REAL DEFAULT 0.0,
        status INTEGER DEFAULT 3,
        open_price INTEGER DEFAULT 0,
        high_price INTEGER DEFAULT 0,
        low_price INTEGER DEFAULT 0,
        prev_close INTEGER DEFAULT 0,
        ask_price INTEGER DEFAULT 0,
        bid_price INTEGER DEFAULT 0,
        volume INTEGER DEFAULT 0,
        amount INTEGER DEFAULT 0,
        total_ask_volume INTEGER DEFAULT 0,
        total_bid_volume INTEGER DEFAULT 0,
        listed_shares INTEGER DEFAULT 0,
        foreign_ratio REAL DEFAULT 0.0,
        prev_volume INTEGER DEFAULT 0,
        expected_price INTEGER DEFAULT 0,
        expected_change INTEGER DEFAULT 0,
        expected_status INTEGER DEFAULT 3,
        expected_volume INTEGER DEFAULT 0,
        market_phase INTEGER DEFAULT 2,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    @classmethod
    def create_table(cls, conn: sqlite3.Connection) -> None:
        """테이블 생성"""
        conn.execute(cls.CREATE_SQL)
        conn.commit()
    
    @classmethod
    def create_indexes(cls, conn: sqlite3.Connection) -> None:
        """인덱스 생성"""
        indexes = [
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_code ON {cls.TABLE_NAME}(code)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_time ON {cls.TABLE_NAME}(time)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_code_time ON {cls.TABLE_NAME}(code, time)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_created_at ON {cls.TABLE_NAME}(created_at)",
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        conn.commit()
    
    @classmethod
    def insert_price(cls, conn: sqlite3.Connection, price: PriceInfo) -> None:
        """시세 정보 삽입"""
        now = datetime.now().isoformat()
        price.created_at = now
        price.updated_at = now
        price.change_rate = price.get_change_rate()
        
        # id 필드 제외하고 삽입
        price_dict = price.to_dict()
        price_dict.pop('id', None)  # id 필드가 있다면 제거
        
        placeholders = ", ".join(["?" for _ in range(len(price_dict))])
        columns = ", ".join(price_dict.keys())
        
        sql = f"INSERT INTO {cls.TABLE_NAME} ({columns}) VALUES ({placeholders})"
        conn.execute(sql, list(price_dict.values()))
    
    @classmethod
    def get_latest_price(cls, conn: sqlite3.Connection, code: str) -> Optional[PriceInfo]:
        """최신 시세 정보 조회"""
        cursor = conn.execute(f"""
            SELECT * FROM {cls.TABLE_NAME} 
            WHERE code = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (code,))
        
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            data = dict(zip(columns, row))
            return PriceInfo.from_dict(data)
        
        return None
    
    @classmethod
    def get_prices_by_time(cls, conn: sqlite3.Connection, time_from: str, time_to: str) -> list[PriceInfo]:
        """시간대별 시세 조회"""
        cursor = conn.execute(f"""
            SELECT * FROM {cls.TABLE_NAME} 
            WHERE created_at BETWEEN ? AND ?
            ORDER BY code, created_at
        """, (time_from, time_to))
        
        prices = []
        columns = [desc[0] for desc in cursor.description]
        
        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            prices.append(PriceInfo.from_dict(data))
        
        return prices
    
    @classmethod
    def cleanup_old_data(cls, conn: sqlite3.Connection, days: int = 30) -> int:
        """오래된 데이터 정리"""
        cursor = conn.execute(f"""
            DELETE FROM {cls.TABLE_NAME} 
            WHERE created_at < datetime('now', '-{days} days')
        """)
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count

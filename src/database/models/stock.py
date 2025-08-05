"""
Stock Model - 주식 종목 정보 모델

Cybos Plus에서 제공하는 모든 종목 정보를 저장하는 SQLite 모델입니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import IntEnum


class MarketKind(IntEnum):
    """시장 구분"""
    NULL = 0          # 구분없음
    KOSPI = 1         # 거래소
    KOSDAQ = 2        # 코스닥
    FREEBOARD = 3     # 프리보드
    KRX = 4           # KRX


class ControlKind(IntEnum):
    """감리 구분"""
    NONE = 0          # 정상
    ATTENTION = 1     # 주의
    WARNING = 2       # 경고
    DANGER_NOTICE = 3 # 위험예고
    DANGER = 4        # 위험


class SupervisionKind(IntEnum):
    """관리 구분"""
    NONE = 0          # 일반종목
    NORMAL = 1        # 관리


class StockStatusKind(IntEnum):
    """주식 상태"""
    NORMAL = 0        # 정상
    STOP = 1          # 거래정지
    BREAK = 2         # 거래중단


class CapitalSize(IntEnum):
    """자본금 규모"""
    NULL = 0          # 제외
    LARGE = 1         # 대
    MIDDLE = 2        # 중
    SMALL = 3         # 소


class SectionKind(IntEnum):
    """부 구분"""
    NULL = 0          # 구분없음
    ST = 1            # 주권
    MF = 2            # 투자회사
    RT = 3            # 부동산투자회사
    SC = 4            # 선박투자회사
    IF = 5            # 사회간접자본투융자회사
    DR = 6            # 주식예탁증서
    SW = 7            # 신수인수권증권
    SR = 8            # 신주인수권증서
    ELW = 9           # 주식워런트증권
    ETF = 10          # 상장지수펀드
    BC = 11           # 수익증권
    FETF = 12         # 해외ETF
    FOREIGN = 13      # 외국주권
    FU = 14           # 선물
    OP = 15           # 옵션


@dataclass
class StockInfo:
    """주식 정보 데이터클래스"""
    
    # 기본 정보
    code: str                           # 종목코드
    name: str                           # 종목명
    market_kind: int                    # 시장구분
    section_kind: int                   # 부구분
    
    # 관리/감리 정보
    control_kind: int = 0               # 감리구분
    supervision_kind: int = 0           # 관리구분
    stock_status_kind: int = 0          # 주식상태
    
    # 가격 정보
    std_price: int = 0                  # 기준가
    max_price: int = 0                  # 상한가
    min_price: int = 0                  # 하한가
    par_price: int = 0                  # 액면가
    yd_open_price: int = 0              # 전일시가
    
    # 기업 정보
    capital_size: int = 0               # 자본금규모
    fiscal_month: int = 0               # 결산기
    group_code: str = ""                # 그룹코드
    industry_code: str = ""             # 업종코드
    kospi200_kind: int = 0              # KOSPI200구분
    
    # 거래 정보
    margin_rate: float = 0.0            # 증거금율
    meme_min: int = 0                   # 거래단위
    lac_kind: int = 0                   # 락구분
    listed_date: int = 0                # 상장일
    
    # 메타데이터
    created_at: Optional[str] = None    # 생성일시
    updated_at: Optional[str] = None    # 수정일시
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StockInfo':
        """딕셔너리에서 생성"""
        return cls(**data)


class StockTable:
    """주식 정보 테이블 관리 클래스"""
    
    TABLE_NAME = "stocks"
    
    CREATE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        market_kind INTEGER NOT NULL,
        section_kind INTEGER NOT NULL,
        control_kind INTEGER DEFAULT 0,
        supervision_kind INTEGER DEFAULT 0,
        stock_status_kind INTEGER DEFAULT 0,
        std_price INTEGER DEFAULT 0,
        max_price INTEGER DEFAULT 0,
        min_price INTEGER DEFAULT 0,
        par_price INTEGER DEFAULT 0,
        yd_open_price INTEGER DEFAULT 0,
        capital_size INTEGER DEFAULT 0,
        fiscal_month INTEGER DEFAULT 0,
        group_code TEXT DEFAULT '',
        industry_code TEXT DEFAULT '',
        kospi200_kind INTEGER DEFAULT 0,
        margin_rate REAL DEFAULT 0.0,
        meme_min INTEGER DEFAULT 0,
        lac_kind INTEGER DEFAULT 0,
        listed_date INTEGER DEFAULT 0,
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
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_market ON {cls.TABLE_NAME}(market_kind)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_section ON {cls.TABLE_NAME}(section_kind)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_name ON {cls.TABLE_NAME}(name)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_status ON {cls.TABLE_NAME}(stock_status_kind)",
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        conn.commit()
    
    @classmethod
    def insert_stock(cls, conn: sqlite3.Connection, stock: StockInfo) -> None:
        """주식 정보 삽입"""
        now = datetime.now().isoformat()
        stock.created_at = now
        stock.updated_at = now
        
        placeholders = ", ".join(["?" for _ in range(len(asdict(stock)))])
        columns = ", ".join(asdict(stock).keys())
        
        sql = f"INSERT OR REPLACE INTO {cls.TABLE_NAME} ({columns}) VALUES ({placeholders})"
        conn.execute(sql, list(asdict(stock).values()))
    
    @classmethod
    def update_stock(cls, conn: sqlite3.Connection, code: str, updates: Dict[str, Any]) -> None:
        """주식 정보 업데이트"""
        updates["updated_at"] = datetime.now().isoformat()
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        sql = f"UPDATE {cls.TABLE_NAME} SET {set_clause} WHERE code = ?"
        
        conn.execute(sql, list(updates.values()) + [code])
    
    @classmethod
    def get_stock(cls, conn: sqlite3.Connection, code: str) -> Optional[StockInfo]:
        """주식 정보 조회"""
        cursor = conn.execute(f"SELECT * FROM {cls.TABLE_NAME} WHERE code = ?", (code,))
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            data = dict(zip(columns, row))
            return StockInfo.from_dict(data)
        
        return None
    
    @classmethod
    def get_stocks_by_market(cls, conn: sqlite3.Connection, market_kind: int) -> list[StockInfo]:
        """시장별 주식 목록 조회"""
        cursor = conn.execute(
            f"SELECT * FROM {cls.TABLE_NAME} WHERE market_kind = ? ORDER BY code",
            (market_kind,)
        )
        
        stocks = []
        columns = [desc[0] for desc in cursor.description]
        
        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            stocks.append(StockInfo.from_dict(data))
        
        return stocks
    
    @classmethod
    def count_stocks(cls, conn: sqlite3.Connection) -> Dict[str, int]:
        """시장별 종목 수 조회"""
        cursor = conn.execute(f"""
            SELECT 
                market_kind,
                COUNT(*) as count
            FROM {cls.TABLE_NAME}
            GROUP BY market_kind
        """)
        
        result = {"total": 0}
        for market_kind, count in cursor.fetchall():
            if market_kind == MarketKind.KOSPI:
                result["kospi"] = count
            elif market_kind == MarketKind.KOSDAQ:
                result["kosdaq"] = count
            else:
                result[f"market_{market_kind}"] = count
            result["total"] += count
        
        return result

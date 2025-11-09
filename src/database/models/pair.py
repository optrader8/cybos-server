"""
Pair Model - 페어 트레이딩 페어 정보 모델

N-way 페어 트레이딩을 지원하는 데이터 모델입니다.
2개, 3개, 4개... N개 종목으로 구성된 페어를 관리합니다.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field
from enum import Enum


class PairStatus(str, Enum):
    """페어 상태"""
    ACTIVE = "ACTIVE"           # 활성 (거래 가능)
    INACTIVE = "INACTIVE"       # 비활성
    MONITORING = "MONITORING"   # 모니터링 중
    SUSPENDED = "SUSPENDED"     # 일시 중지


class PairType(str, Enum):
    """페어 타입"""
    TWO_WAY = "2-WAY"           # 2개 종목 페어
    THREE_WAY = "3-WAY"         # 3개 종목 페어
    FOUR_WAY = "4-WAY"          # 4개 종목 페어
    N_WAY = "N-WAY"             # N개 종목 페어


@dataclass
class PairInfo:
    """페어 정보 데이터클래스"""

    # 페어 식별
    pair_id: str                        # 페어 고유 ID (예: "005930_000660")
    pair_type: PairType                 # 페어 타입
    stock_codes: List[str]              # 종목 코드 리스트 (정렬됨)

    # 페어 상태
    status: PairStatus = PairStatus.MONITORING

    # 메타데이터
    name: Optional[str] = None          # 페어 이름
    description: Optional[str] = None   # 설명

    # 공적분 정보
    cointegration_score: float = 0.0    # 공적분 점수 (p-value)
    half_life: float = 0.0              # 반감기 (일)
    hedge_ratios: List[float] = field(default_factory=list)  # 헤지 비율

    # 통계 정보
    correlation: float = 0.0            # 상관계수
    spread_mean: float = 0.0            # 스프레드 평균
    spread_std: float = 0.0             # 스프레드 표준편차

    # 성과 정보
    sharpe_ratio: float = 0.0           # 샤프 비율
    max_drawdown: float = 0.0           # 최대 낙폭
    win_rate: float = 0.0               # 승률
    total_trades: int = 0               # 총 거래 횟수

    # 시간 정보
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_analyzed_at: Optional[str] = None

    def __post_init__(self):
        """데이터 검증 및 초기화"""
        # 종목 코드 정렬 (일관성 보장)
        self.stock_codes = sorted(self.stock_codes)

        # pair_id 자동 생성
        if not self.pair_id:
            self.pair_id = "_".join(self.stock_codes)

        # pair_type 자동 설정
        n = len(self.stock_codes)
        if n == 2:
            self.pair_type = PairType.TWO_WAY
        elif n == 3:
            self.pair_type = PairType.THREE_WAY
        elif n == 4:
            self.pair_type = PairType.FOUR_WAY
        else:
            self.pair_type = PairType.N_WAY

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        # List를 JSON 문자열로 변환
        data['stock_codes'] = json.dumps(self.stock_codes)
        data['hedge_ratios'] = json.dumps(self.hedge_ratios)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PairInfo':
        """딕셔너리에서 생성"""
        # JSON 문자열을 List로 변환
        if isinstance(data.get('stock_codes'), str):
            data['stock_codes'] = json.loads(data['stock_codes'])
        if isinstance(data.get('hedge_ratios'), str):
            data['hedge_ratios'] = json.loads(data['hedge_ratios'])
        return cls(**data)

    def get_stock_count(self) -> int:
        """페어를 구성하는 종목 수"""
        return len(self.stock_codes)

    def is_valid_for_trading(self) -> bool:
        """거래 가능 여부"""
        return (
            self.status == PairStatus.ACTIVE and
            self.cointegration_score < 0.05 and  # p-value < 0.05
            self.half_life > 0
        )


class PairTable:
    """페어 정보 테이블 관리 클래스"""

    TABLE_NAME = "pairs"

    CREATE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        pair_id TEXT PRIMARY KEY,
        pair_type TEXT NOT NULL,
        stock_codes TEXT NOT NULL,
        status TEXT DEFAULT 'MONITORING',
        name TEXT,
        description TEXT,
        cointegration_score REAL DEFAULT 0.0,
        half_life REAL DEFAULT 0.0,
        hedge_ratios TEXT,
        correlation REAL DEFAULT 0.0,
        spread_mean REAL DEFAULT 0.0,
        spread_std REAL DEFAULT 0.0,
        sharpe_ratio REAL DEFAULT 0.0,
        max_drawdown REAL DEFAULT 0.0,
        win_rate REAL DEFAULT 0.0,
        total_trades INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_analyzed_at TEXT
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
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_status ON {cls.TABLE_NAME}(status)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_type ON {cls.TABLE_NAME}(pair_type)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_score ON {cls.TABLE_NAME}(cointegration_score)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_sharpe ON {cls.TABLE_NAME}(sharpe_ratio)",
        ]

        for index_sql in indexes:
            conn.execute(index_sql)

        conn.commit()

    @classmethod
    def upsert_pair(cls, conn: sqlite3.Connection, pair: PairInfo) -> None:
        """페어 정보 삽입 또는 업데이트"""
        pair.updated_at = datetime.now().isoformat()
        if not pair.created_at:
            pair.created_at = pair.updated_at

        pair_dict = pair.to_dict()

        placeholders = ", ".join([f":{k}" for k in pair_dict.keys()])
        columns = ", ".join(pair_dict.keys())

        sql = f"INSERT OR REPLACE INTO {cls.TABLE_NAME} ({columns}) VALUES ({placeholders})"
        conn.execute(sql, pair_dict)

    @classmethod
    def get_pair(cls, conn: sqlite3.Connection, pair_id: str) -> Optional[PairInfo]:
        """페어 조회"""
        cursor = conn.execute(f"SELECT * FROM {cls.TABLE_NAME} WHERE pair_id = ?", (pair_id,))
        row = cursor.fetchone()

        if row:
            columns = [desc[0] for desc in cursor.description]
            data = dict(zip(columns, row))
            return PairInfo.from_dict(data)

        return None

    @classmethod
    def get_active_pairs(cls, conn: sqlite3.Connection, pair_type: Optional[PairType] = None) -> List[PairInfo]:
        """활성 페어 목록 조회"""
        if pair_type:
            sql = f"""
                SELECT * FROM {cls.TABLE_NAME}
                WHERE status = 'ACTIVE' AND pair_type = ?
                ORDER BY sharpe_ratio DESC
            """
            cursor = conn.execute(sql, (pair_type.value,))
        else:
            sql = f"""
                SELECT * FROM {cls.TABLE_NAME}
                WHERE status = 'ACTIVE'
                ORDER BY sharpe_ratio DESC
            """
            cursor = conn.execute(sql)

        pairs = []
        columns = [desc[0] for desc in cursor.description]

        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            pairs.append(PairInfo.from_dict(data))

        return pairs

    @classmethod
    def get_pairs_by_stock(cls, conn: sqlite3.Connection, stock_code: str) -> List[PairInfo]:
        """특정 종목이 포함된 페어 조회"""
        # stock_codes에 해당 종목이 포함된 페어 검색
        # JSON 배열 내 검색을 위해 LIKE 사용
        sql = f"""
            SELECT * FROM {cls.TABLE_NAME}
            WHERE stock_codes LIKE ?
            ORDER BY sharpe_ratio DESC
        """
        cursor = conn.execute(sql, (f'%"{stock_code}"%',))

        pairs = []
        columns = [desc[0] for desc in cursor.description]

        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            pair = PairInfo.from_dict(data)
            # 실제로 해당 종목이 포함되어 있는지 확인
            if stock_code in pair.stock_codes:
                pairs.append(pair)

        return pairs

    @classmethod
    def get_top_pairs(cls, conn: sqlite3.Connection, limit: int = 20,
                      min_sharpe: float = 0.5) -> List[PairInfo]:
        """상위 페어 조회"""
        sql = f"""
            SELECT * FROM {cls.TABLE_NAME}
            WHERE sharpe_ratio >= ? AND status != 'SUSPENDED'
            ORDER BY sharpe_ratio DESC
            LIMIT ?
        """
        cursor = conn.execute(sql, (min_sharpe, limit))

        pairs = []
        columns = [desc[0] for desc in cursor.description]

        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            pairs.append(PairInfo.from_dict(data))

        return pairs

    @classmethod
    def count_pairs_by_type(cls, conn: sqlite3.Connection) -> Dict[str, int]:
        """타입별 페어 개수 조회"""
        sql = f"""
            SELECT pair_type, COUNT(*) as count
            FROM {cls.TABLE_NAME}
            GROUP BY pair_type
        """
        cursor = conn.execute(sql)

        result = {}
        for pair_type, count in cursor.fetchall():
            result[pair_type] = count

        return result

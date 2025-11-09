"""
Signal Model - 페어 트레이딩 신호 모델

페어 트레이딩 진입/청산 신호를 저장하고 관리하는 모델입니다.
Z-score 기반 신호 생성 및 추적을 지원합니다.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field
from enum import Enum


class SignalType(str, Enum):
    """신호 타입"""
    ENTRY_LONG = "ENTRY_LONG"       # 롱 진입
    ENTRY_SHORT = "ENTRY_SHORT"     # 숏 진입
    EXIT_LONG = "EXIT_LONG"         # 롱 청산
    EXIT_SHORT = "EXIT_SHORT"       # 숏 청산
    STOP_LOSS = "STOP_LOSS"         # 손절
    TAKE_PROFIT = "TAKE_PROFIT"     # 익절


class SignalStatus(str, Enum):
    """신호 상태"""
    ACTIVE = "ACTIVE"               # 활성
    EXECUTED = "EXECUTED"           # 실행됨
    CANCELLED = "CANCELLED"         # 취소됨
    EXPIRED = "EXPIRED"             # 만료됨


@dataclass
class PairSignal:
    """페어 트레이딩 신호 데이터클래스"""

    # 식별 정보
    signal_id: str                              # 신호 ID
    pair_id: str                                # 페어 ID
    stock_codes: List[str]                      # 종목 코드 리스트

    # 신호 정보
    signal_type: SignalType                     # 신호 타입
    status: SignalStatus = SignalStatus.ACTIVE  # 상태

    # 가격 정보
    current_prices: Dict[str, float] = field(default_factory=dict)  # 현재가
    entry_prices: Dict[str, float] = field(default_factory=dict)    # 진입가
    target_prices: Dict[str, float] = field(default_factory=dict)   # 목표가
    stop_prices: Dict[str, float] = field(default_factory=dict)     # 손절가

    # 스프레드 정보
    spread: float = 0.0                         # 현재 스프레드
    spread_mean: float = 0.0                    # 스프레드 평균
    spread_std: float = 0.0                     # 스프레드 표준편차
    z_score: float = 0.0                        # Z-score

    # 포지션 정보
    position_sizes: Dict[str, int] = field(default_factory=dict)    # 포지션 크기 (주)
    hedge_ratios: List[float] = field(default_factory=list)         # 헤지 비율

    # 시간 정보
    created_at: Optional[str] = None            # 생성일시
    executed_at: Optional[str] = None           # 실행일시
    expired_at: Optional[str] = None            # 만료일시

    # 메타데이터
    confidence: float = 0.0                     # 신호 신뢰도 (0-1)
    expected_return: float = 0.0                # 기대 수익률
    risk_level: int = 1                         # 위험도 (1-5)
    notes: str = ""                             # 메모

    def __post_init__(self):
        """데이터 검증 및 초기화"""
        if not self.signal_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")
            self.signal_id = f"{self.pair_id}_{timestamp}"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        # 복잡한 타입을 JSON 문자열로 변환
        data['stock_codes'] = json.dumps(self.stock_codes)
        data['current_prices'] = json.dumps(self.current_prices)
        data['entry_prices'] = json.dumps(self.entry_prices)
        data['target_prices'] = json.dumps(self.target_prices)
        data['stop_prices'] = json.dumps(self.stop_prices)
        data['position_sizes'] = json.dumps(self.position_sizes)
        data['hedge_ratios'] = json.dumps(self.hedge_ratios)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PairSignal':
        """딕셔너리에서 생성"""
        # JSON 문자열을 객체로 변환
        json_fields = ['stock_codes', 'current_prices', 'entry_prices',
                      'target_prices', 'stop_prices', 'position_sizes', 'hedge_ratios']
        for field in json_fields:
            if isinstance(data.get(field), str):
                data[field] = json.loads(data[field])
        return cls(**data)

    def is_entry_signal(self) -> bool:
        """진입 신호 여부"""
        return self.signal_type in [SignalType.ENTRY_LONG, SignalType.ENTRY_SHORT]

    def is_exit_signal(self) -> bool:
        """청산 신호 여부"""
        return self.signal_type in [SignalType.EXIT_LONG, SignalType.EXIT_SHORT,
                                   SignalType.STOP_LOSS, SignalType.TAKE_PROFIT]


class SignalTable:
    """신호 테이블 관리 클래스"""

    TABLE_NAME = "pair_signals"

    CREATE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        signal_id TEXT PRIMARY KEY,
        pair_id TEXT NOT NULL,
        stock_codes TEXT NOT NULL,
        signal_type TEXT NOT NULL,
        status TEXT DEFAULT 'ACTIVE',
        current_prices TEXT,
        entry_prices TEXT,
        target_prices TEXT,
        stop_prices TEXT,
        spread REAL DEFAULT 0.0,
        spread_mean REAL DEFAULT 0.0,
        spread_std REAL DEFAULT 0.0,
        z_score REAL DEFAULT 0.0,
        position_sizes TEXT,
        hedge_ratios TEXT,
        confidence REAL DEFAULT 0.0,
        expected_return REAL DEFAULT 0.0,
        risk_level INTEGER DEFAULT 1,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        executed_at TEXT,
        expired_at TEXT
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
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_pair ON {cls.TABLE_NAME}(pair_id)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_status ON {cls.TABLE_NAME}(status)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_type ON {cls.TABLE_NAME}(signal_type)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_zscore ON {cls.TABLE_NAME}(z_score)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_created ON {cls.TABLE_NAME}(created_at)",
        ]

        for index_sql in indexes:
            conn.execute(index_sql)

        conn.commit()

    @classmethod
    def insert_signal(cls, conn: sqlite3.Connection, signal: PairSignal) -> None:
        """신호 삽입"""
        if not signal.created_at:
            signal.created_at = datetime.now().isoformat()

        signal_dict = signal.to_dict()

        placeholders = ", ".join([f":{k}" for k in signal_dict.keys()])
        columns = ", ".join(signal_dict.keys())

        sql = f"INSERT INTO {cls.TABLE_NAME} ({columns}) VALUES ({placeholders})"
        conn.execute(sql, signal_dict)

    @classmethod
    def update_signal_status(cls, conn: sqlite3.Connection,
                            signal_id: str, status: SignalStatus) -> None:
        """신호 상태 업데이트"""
        executed_at = datetime.now().isoformat() if status == SignalStatus.EXECUTED else None

        sql = f"""
            UPDATE {cls.TABLE_NAME}
            SET status = ?, executed_at = ?
            WHERE signal_id = ?
        """
        conn.execute(sql, (status.value, executed_at, signal_id))

    @classmethod
    def get_active_signals(cls, conn: sqlite3.Connection,
                          pair_id: Optional[str] = None) -> List[PairSignal]:
        """활성 신호 조회"""
        if pair_id:
            sql = f"""
                SELECT * FROM {cls.TABLE_NAME}
                WHERE status = 'ACTIVE' AND pair_id = ?
                ORDER BY created_at DESC
            """
            cursor = conn.execute(sql, (pair_id,))
        else:
            sql = f"""
                SELECT * FROM {cls.TABLE_NAME}
                WHERE status = 'ACTIVE'
                ORDER BY z_score DESC
            """
            cursor = conn.execute(sql)

        signals = []
        columns = [desc[0] for desc in cursor.description]

        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            signals.append(PairSignal.from_dict(data))

        return signals

    @classmethod
    def get_signals_by_pair(cls, conn: sqlite3.Connection, pair_id: str,
                           limit: int = 50) -> List[PairSignal]:
        """페어별 신호 이력 조회"""
        sql = f"""
            SELECT * FROM {cls.TABLE_NAME}
            WHERE pair_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        cursor = conn.execute(sql, (pair_id, limit))

        signals = []
        columns = [desc[0] for desc in cursor.description]

        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            signals.append(PairSignal.from_dict(data))

        return signals

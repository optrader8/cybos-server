"""
Cointegration Model - 공적분 분석 결과 모델

페어 트레이딩을 위한 공적분 분석 결과를 저장하는 모델입니다.
Engle-Granger 검정, Johansen 검정 등의 결과를 관리합니다.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field
from enum import Enum


class CointegrationMethod(str, Enum):
    """공적분 검정 방법"""
    ENGLE_GRANGER = "ENGLE_GRANGER"     # 2개 종목용
    JOHANSEN = "JOHANSEN"               # N개 종목용
    ADF = "ADF"                         # Augmented Dickey-Fuller


class CointegrationSignificance(str, Enum):
    """통계적 유의성"""
    HIGHLY_SIGNIFICANT = "HIGHLY_SIG"   # p < 0.01
    SIGNIFICANT = "SIGNIFICANT"          # p < 0.05
    MARGINAL = "MARGINAL"                # p < 0.10
    NOT_SIGNIFICANT = "NOT_SIG"          # p >= 0.10


@dataclass
class CointegrationResult:
    """공적분 분석 결과 데이터클래스"""

    # 식별 정보
    result_id: str                              # 결과 ID
    pair_id: str                                # 페어 ID
    stock_codes: List[str]                      # 종목 코드 리스트

    # 분석 정보
    method: CointegrationMethod                 # 검정 방법
    test_statistic: float                       # 검정 통계량
    p_value: float                              # p-value
    critical_values: Dict[str, float] = field(default_factory=dict)  # 임계값

    # 공적분 벡터 및 계수
    cointegration_vector: List[float] = field(default_factory=list)  # 공적분 벡터
    hedge_ratios: List[float] = field(default_factory=list)          # 헤지 비율
    intercept: float = 0.0                      # 절편

    # 잔차(Residual) 정보
    residuals_mean: float = 0.0                 # 잔차 평균
    residuals_std: float = 0.0                  # 잔차 표준편차
    half_life: float = 0.0                      # 반감기 (일)

    # 추가 통계
    adf_statistic: float = 0.0                  # ADF 통계량
    adf_p_value: float = 0.0                    # ADF p-value

    # 데이터 정보
    sample_size: int = 0                        # 샘플 크기
    start_date: Optional[str] = None            # 분석 시작일
    end_date: Optional[str] = None              # 분석 종료일

    # 메타데이터
    significance: Optional[CointegrationSignificance] = None
    created_at: Optional[str] = None
    window_days: int = 252                      # 분석 기간 (영업일)

    def __post_init__(self):
        """데이터 검증 및 초기화"""
        # 유의성 자동 설정
        if self.significance is None:
            if self.p_value < 0.01:
                self.significance = CointegrationSignificance.HIGHLY_SIGNIFICANT
            elif self.p_value < 0.05:
                self.significance = CointegrationSignificance.SIGNIFICANT
            elif self.p_value < 0.10:
                self.significance = CointegrationSignificance.MARGINAL
            else:
                self.significance = CointegrationSignificance.NOT_SIGNIFICANT

        # result_id 자동 생성
        if not self.result_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.result_id = f"{self.pair_id}_{timestamp}"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        # List와 Dict를 JSON 문자열로 변환
        data['stock_codes'] = json.dumps(self.stock_codes)
        data['critical_values'] = json.dumps(self.critical_values)
        data['cointegration_vector'] = json.dumps(self.cointegration_vector)
        data['hedge_ratios'] = json.dumps(self.hedge_ratios)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CointegrationResult':
        """딕셔너리에서 생성"""
        # JSON 문자열을 객체로 변환
        if isinstance(data.get('stock_codes'), str):
            data['stock_codes'] = json.loads(data['stock_codes'])
        if isinstance(data.get('critical_values'), str):
            data['critical_values'] = json.loads(data['critical_values'])
        if isinstance(data.get('cointegration_vector'), str):
            data['cointegration_vector'] = json.loads(data['cointegration_vector'])
        if isinstance(data.get('hedge_ratios'), str):
            data['hedge_ratios'] = json.loads(data['hedge_ratios'])
        return cls(**data)

    def is_cointegrated(self, alpha: float = 0.05) -> bool:
        """공적분 관계 존재 여부"""
        return self.p_value < alpha


class CointegrationTable:
    """공적분 결과 테이블 관리 클래스"""

    TABLE_NAME = "cointegration_results"

    CREATE_SQL = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        result_id TEXT PRIMARY KEY,
        pair_id TEXT NOT NULL,
        stock_codes TEXT NOT NULL,
        method TEXT NOT NULL,
        test_statistic REAL NOT NULL,
        p_value REAL NOT NULL,
        critical_values TEXT,
        cointegration_vector TEXT,
        hedge_ratios TEXT,
        intercept REAL DEFAULT 0.0,
        residuals_mean REAL DEFAULT 0.0,
        residuals_std REAL DEFAULT 0.0,
        half_life REAL DEFAULT 0.0,
        adf_statistic REAL DEFAULT 0.0,
        adf_p_value REAL DEFAULT 0.0,
        sample_size INTEGER DEFAULT 0,
        start_date TEXT,
        end_date TEXT,
        significance TEXT,
        window_days INTEGER DEFAULT 252,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
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
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_pvalue ON {cls.TABLE_NAME}(p_value)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_significance ON {cls.TABLE_NAME}(significance)",
            f"CREATE INDEX IF NOT EXISTS idx_{cls.TABLE_NAME}_date ON {cls.TABLE_NAME}(created_at)",
        ]

        for index_sql in indexes:
            conn.execute(index_sql)

        conn.commit()

    @classmethod
    def insert_result(cls, conn: sqlite3.Connection, result: CointegrationResult) -> None:
        """공적분 결과 삽입"""
        if not result.created_at:
            result.created_at = datetime.now().isoformat()

        result_dict = result.to_dict()

        placeholders = ", ".join([f":{k}" for k in result_dict.keys()])
        columns = ", ".join(result_dict.keys())

        sql = f"INSERT INTO {cls.TABLE_NAME} ({columns}) VALUES ({placeholders})"
        conn.execute(sql, result_dict)

    @classmethod
    def get_latest_result(cls, conn: sqlite3.Connection, pair_id: str) -> Optional[CointegrationResult]:
        """최신 공적분 결과 조회"""
        sql = f"""
            SELECT * FROM {cls.TABLE_NAME}
            WHERE pair_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """
        cursor = conn.execute(sql, (pair_id,))
        row = cursor.fetchone()

        if row:
            columns = [desc[0] for desc in cursor.description]
            data = dict(zip(columns, row))
            return CointegrationResult.from_dict(data)

        return None

    @classmethod
    def get_results_by_pair(cls, conn: sqlite3.Connection, pair_id: str,
                           limit: int = 10) -> List[CointegrationResult]:
        """페어별 공적분 결과 이력 조회"""
        sql = f"""
            SELECT * FROM {cls.TABLE_NAME}
            WHERE pair_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        cursor = conn.execute(sql, (pair_id, limit))

        results = []
        columns = [desc[0] for desc in cursor.description]

        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            results.append(CointegrationResult.from_dict(data))

        return results

    @classmethod
    def get_significant_results(cls, conn: sqlite3.Connection,
                                max_p_value: float = 0.05) -> List[CointegrationResult]:
        """유의한 공적분 결과 조회"""
        # 각 페어별 최신 결과만 가져오기
        sql = f"""
            WITH LatestResults AS (
                SELECT *,
                       ROW_NUMBER() OVER (PARTITION BY pair_id ORDER BY created_at DESC) as rn
                FROM {cls.TABLE_NAME}
            )
            SELECT * FROM LatestResults
            WHERE rn = 1 AND p_value < ?
            ORDER BY p_value ASC
        """
        cursor = conn.execute(sql, (max_p_value,))

        results = []
        columns = [desc[0] for desc in cursor.description]

        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            # rn 컬럼 제거
            data.pop('rn', None)
            results.append(CointegrationResult.from_dict(data))

        return results

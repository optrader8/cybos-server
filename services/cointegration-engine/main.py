"""
Cointegration Engine - 공적분 분석 엔진

페어 트레이딩을 위한 공적분 분석 및 페어 검색 엔진입니다.
N-way 페어를 지원하며, 효율적인 조합 생성 알고리즘을 사용합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Optional
from itertools import combinations
from datetime import datetime, timedelta

from statsmodels.tsa.stattools import coint, adfuller
from scipy.stats import pearsonr

from src.database.connection import get_connection_context
from src.database.models.pair import PairInfo, PairStatus, PairTable
from src.database.models.cointegration import (
    CointegrationResult,
    CointegrationMethod,
    CointegrationTable
)
from src.database.models.history import HistoryTable, HistoryTimeframe


class CointegrationEngine:
    """공적분 분석 엔진"""

    def __init__(self, db_path: str = "data/cybos.db"):
        self.db_path = db_path

    def get_price_series(self, stock_codes: List[str],
                        days: int = 252) -> Dict[str, pd.Series]:
        """종목별 가격 시계열 데이터 조회"""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days * 1.5)).strftime("%Y-%m-%d")

        price_series = {}

        with get_connection_context(self.db_path) as conn:
            for code in stock_codes:
                history_list = HistoryTable.get_history(
                    conn, code, HistoryTimeframe.DAILY, start_date, end_date
                )

                if len(history_list) >= days:
                    # 가장 최근 N일 데이터만 사용
                    recent_data = history_list[-days:]
                    prices = [h.close_price for h in recent_data]
                    dates = [h.date for h in recent_data]

                    price_series[code] = pd.Series(prices, index=pd.to_datetime(dates))

        return price_series

    def test_pairwise_cointegration(self, code1: str, code2: str,
                                   window_days: int = 252) -> Optional[CointegrationResult]:
        """
        2개 종목 간 공적분 검정 (Engle-Granger)
        """
        # 가격 데이터 조회
        price_series = self.get_price_series([code1, code2], window_days)

        if code1 not in price_series or code2 not in price_series:
            return None

        y = price_series[code1].values
        x = price_series[code2].values

        # 길이 맞추기
        min_len = min(len(y), len(x))
        y = y[-min_len:]
        x = x[-min_len:]

        if len(y) < 30:  # 최소 데이터 포인트
            return None

        try:
            # Engle-Granger 공적분 검정
            score, p_value, crit_values = coint(y, x)

            # 헤지 비율 계산 (OLS)
            hedge_ratio = np.cov(y, x)[0, 1] / np.var(x)

            # 잔차 계산
            residuals = y - hedge_ratio * x
            residuals_mean = np.mean(residuals)
            residuals_std = np.std(residuals)

            # 반감기 계산 (AR(1) 모델)
            half_life = self._calculate_half_life(residuals)

            # ADF 검정 (잔차의 정상성)
            adf_result = adfuller(residuals)
            adf_statistic = adf_result[0]
            adf_p_value = adf_result[1]

            # 상관계수
            correlation, _ = pearsonr(y, x)

            # 결과 생성
            result = CointegrationResult(
                result_id="",
                pair_id=f"{code1}_{code2}",
                stock_codes=[code1, code2],
                method=CointegrationMethod.ENGLE_GRANGER,
                test_statistic=score,
                p_value=p_value,
                critical_values={
                    "1%": float(crit_values[0]),
                    "5%": float(crit_values[1]),
                    "10%": float(crit_values[2])
                },
                cointegration_vector=[1.0, -hedge_ratio],
                hedge_ratios=[1.0, hedge_ratio],
                intercept=residuals_mean,
                residuals_mean=residuals_mean,
                residuals_std=residuals_std,
                half_life=half_life,
                adf_statistic=adf_statistic,
                adf_p_value=adf_p_value,
                sample_size=len(y),
                start_date=price_series[code1].index[0].strftime("%Y-%m-%d"),
                end_date=price_series[code1].index[-1].strftime("%Y-%m-%d"),
                window_days=window_days
            )

            return result

        except Exception as e:
            print(f"공적분 검정 실패 ({code1}, {code2}): {e}")
            return None

    def _calculate_half_life(self, residuals: np.ndarray) -> float:
        """
        잔차의 반감기 계산
        AR(1) 모델: residuals[t] = lambda * residuals[t-1] + epsilon
        """
        try:
            lag_residuals = residuals[:-1]
            delta_residuals = residuals[1:] - residuals[:-1]

            # OLS: delta = (lambda - 1) * lag + error
            # lambda = cov(delta, lag) / var(lag) + 1
            if len(lag_residuals) > 0 and np.var(lag_residuals) > 0:
                lambda_param = np.cov(delta_residuals, lag_residuals)[0, 1] / np.var(lag_residuals) + 1

                if 0 < lambda_param < 1:
                    half_life = -np.log(2) / np.log(lambda_param)
                    return float(half_life)

            return 0.0
        except:
            return 0.0

    def find_cointegrated_pairs(self, stock_codes: List[str],
                               max_p_value: float = 0.05,
                               window_days: int = 252) -> List[CointegrationResult]:
        """
        종목 리스트에서 공적분 관계를 가진 페어 찾기
        """
        results = []

        # 모든 2개 조합 생성
        pair_combinations = list(combinations(stock_codes, 2))

        print(f"🔍 {len(stock_codes)}개 종목에서 {len(pair_combinations)}개 페어 조합 분석 중...")

        for i, (code1, code2) in enumerate(pair_combinations):
            if (i + 1) % 100 == 0:
                print(f"  진행률: {i + 1}/{len(pair_combinations)} ({(i + 1) / len(pair_combinations) * 100:.1f}%)")

            result = self.test_pairwise_cointegration(code1, code2, window_days)

            if result and result.p_value < max_p_value:
                results.append(result)

                # 데이터베이스에 저장
                with get_connection_context(self.db_path) as conn:
                    CointegrationTable.insert_result(conn, result)
                    conn.commit()

        print(f"✅ {len(results)}개 공적분 페어 발견 (p < {max_p_value})")

        return results

    def create_pairs_from_cointegration(self, max_p_value: float = 0.05) -> List[PairInfo]:
        """
        공적분 결과로부터 페어 생성
        """
        pairs = []

        with get_connection_context(self.db_path) as conn:
            # 유의한 공적분 결과 조회
            coint_results = CointegrationTable.get_significant_results(conn, max_p_value)

            print(f"📊 {len(coint_results)}개 공적분 결과를 페어로 변환 중...")

            for result in coint_results:
                pair = PairInfo(
                    pair_id=result.pair_id,
                    pair_type="2-WAY",  # 자동으로 설정됨
                    stock_codes=result.stock_codes,
                    status=PairStatus.ACTIVE if result.p_value < 0.01 else PairStatus.MONITORING,
                    cointegration_score=result.p_value,
                    half_life=result.half_life,
                    hedge_ratios=result.hedge_ratios,
                    spread_std=result.residuals_std,
                    last_analyzed_at=result.created_at
                )

                PairTable.upsert_pair(conn, pair)
                pairs.append(pair)

            conn.commit()

        print(f"✅ {len(pairs)}개 페어 생성 완료")

        return pairs


def main():
    """메인 함수 - 공적분 분석 실행"""
    print("🚀 공적분 분석 엔진 시작")
    print("=" * 60)

    engine = CointegrationEngine()

    # KOSPI200 종목 코드 가져오기
    from src.database.models.stock import StockTable, MarketKind

    with get_connection_context() as conn:
        kospi200_stocks = StockTable.get_kospi200_stocks(conn)
        stock_codes = [stock.code for stock in kospi200_stocks[:50]]  # 테스트용 50개

    print(f"📋 대상 종목: {len(stock_codes)}개")

    # 공적분 페어 찾기
    results = engine.find_cointegrated_pairs(stock_codes, max_p_value=0.05, window_days=252)

    # 페어 생성
    pairs = engine.create_pairs_from_cointegration(max_p_value=0.05)

    print(f"\n🎉 분석 완료!")
    print(f"  공적분 페어: {len(results)}개")
    print(f"  생성된 페어: {len(pairs)}개")


if __name__ == "__main__":
    main()

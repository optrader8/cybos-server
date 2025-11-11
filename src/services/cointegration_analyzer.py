"""
Cointegration Analyzer - 공적분 분석 엔진

통계적 공적분 테스트를 수행합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from datetime import datetime
from enum import Enum

try:
    from statsmodels.tsa.stattools import coint, adfuller
    from statsmodels.tsa.vector_ar.vecm import coint_johansen
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False


class CointegrationMethod(str, Enum):
    """공적분 테스트 방법"""
    ENGLE_GRANGER = "engle_granger"
    JOHANSEN = "johansen"


class SignificanceLevel(str, Enum):
    """통계적 유의성"""
    HIGHLY_SIG = "HIGHLY_SIG"      # p < 0.01
    SIGNIFICANT = "SIGNIFICANT"     # p < 0.05
    MARGINAL = "MARGINAL"           # p < 0.10
    NOT_SIG = "NOT_SIG"             # p >= 0.10


class CointegrationAnalyzer:
    """공적분 분석 클래스"""

    def __init__(self):
        """초기화"""
        if not STATSMODELS_AVAILABLE:
            raise ImportError("statsmodels is required for cointegration analysis")

    def analyze_pair(
        self,
        prices_a: List[float],
        prices_b: List[float],
        method: CointegrationMethod = CointegrationMethod.ENGLE_GRANGER
    ) -> Dict:
        """
        2개 종목 간 공적분 분석

        Args:
            prices_a: 종목 A 가격 시계열
            prices_b: 종목 B 가격 시계열
            method: 분석 방법

        Returns:
            분석 결과 딕셔너리
        """
        if len(prices_a) != len(prices_b):
            raise ValueError("Price series must have same length")

        if len(prices_a) < 30:
            raise ValueError("Insufficient data: need at least 30 observations")

        prices_a = np.array(prices_a)
        prices_b = np.array(prices_b)

        if method == CointegrationMethod.ENGLE_GRANGER:
            return self._engle_granger_test(prices_a, prices_b)
        elif method == CointegrationMethod.JOHANSEN:
            return self._johansen_test_2stocks(prices_a, prices_b)
        else:
            raise ValueError(f"Unknown method: {method}")

    def _engle_granger_test(
        self,
        prices_a: np.ndarray,
        prices_b: np.ndarray
    ) -> Dict:
        """
        Engle-Granger 공적분 테스트

        Args:
            prices_a: 종목 A 가격
            prices_b: 종목 B 가격

        Returns:
            테스트 결과
        """
        # 공적분 테스트 수행
        test_stat, p_value, critical_values = coint(prices_a, prices_b)

        # 헤지 비율 계산 (OLS regression)
        hedge_ratio = self._calculate_hedge_ratio(prices_a, prices_b)

        # 스프레드 계산
        spread = prices_a - hedge_ratio * prices_b

        # 잔차 통계
        residuals_mean = float(np.mean(spread))
        residuals_std = float(np.std(spread, ddof=1))

        # 반감기 계산
        half_life = self._calculate_half_life(spread)

        # ADF 테스트 (잔차의 정상성)
        adf_result = adfuller(spread, maxlag=1)
        adf_statistic = float(adf_result[0])
        adf_p_value = float(adf_result[1])

        # 유의성 판단
        significance = self._determine_significance(p_value)

        return {
            "method": CointegrationMethod.ENGLE_GRANGER.value,
            "test_statistic": float(test_stat),
            "p_value": float(p_value),
            "critical_values": {
                "1%": float(critical_values[0]),
                "5%": float(critical_values[1]),
                "10%": float(critical_values[2])
            },
            "cointegration_vector": [1.0, -hedge_ratio],
            "hedge_ratios": [hedge_ratio],
            "intercept": 0.0,
            "residuals_mean": residuals_mean,
            "residuals_std": residuals_std,
            "half_life": half_life,
            "adf_statistic": adf_statistic,
            "adf_p_value": adf_p_value,
            "significance": significance.value,
            "sample_size": len(prices_a)
        }

    def _johansen_test_2stocks(
        self,
        prices_a: np.ndarray,
        prices_b: np.ndarray
    ) -> Dict:
        """
        Johansen 공적분 테스트 (2개 종목)

        Args:
            prices_a: 종목 A 가격
            prices_b: 종목 B 가격

        Returns:
            테스트 결과
        """
        # 가격 행렬 구성
        prices_matrix = np.column_stack([prices_a, prices_b])

        # Johansen 테스트 수행
        result = coint_johansen(prices_matrix, det_order=0, k_ar_diff=1)

        # Trace 통계량 (첫 번째 공적분 벡터)
        test_stat = float(result.lr1[0])  # Trace statistic

        # Critical values (90%, 95%, 99%)
        critical_values = result.cvt[0]  # Critical values for trace statistic

        # p-value 추정 (critical value 기반)
        p_value = self._estimate_p_value_from_critical(test_stat, critical_values)

        # 공적분 벡터 (첫 번째)
        coint_vector = result.evec[:, 0]

        # 헤지 비율 계산
        hedge_ratio = -coint_vector[1] / coint_vector[0] if coint_vector[0] != 0 else 1.0

        # 스프레드 계산
        spread = prices_a - hedge_ratio * prices_b

        # 잔차 통계
        residuals_mean = float(np.mean(spread))
        residuals_std = float(np.std(spread, ddof=1))

        # 반감기
        half_life = self._calculate_half_life(spread)

        # ADF 테스트
        adf_result = adfuller(spread, maxlag=1)
        adf_statistic = float(adf_result[0])
        adf_p_value = float(adf_result[1])

        # 유의성 판단
        significance = self._determine_significance(p_value)

        return {
            "method": CointegrationMethod.JOHANSEN.value,
            "test_statistic": test_stat,
            "p_value": p_value,
            "critical_values": {
                "10%": float(critical_values[0]),
                "5%": float(critical_values[1]),
                "1%": float(critical_values[2])
            },
            "cointegration_vector": coint_vector.tolist(),
            "hedge_ratios": [hedge_ratio],
            "intercept": 0.0,
            "residuals_mean": residuals_mean,
            "residuals_std": residuals_std,
            "half_life": half_life,
            "adf_statistic": adf_statistic,
            "adf_p_value": adf_p_value,
            "significance": significance.value,
            "sample_size": len(prices_a)
        }

    def _calculate_hedge_ratio(
        self,
        prices_a: np.ndarray,
        prices_b: np.ndarray
    ) -> float:
        """OLS 회귀로 헤지 비율 계산"""
        covariance = np.cov(prices_a, prices_b)[0, 1]
        variance_b = np.var(prices_b, ddof=1)

        if variance_b == 0:
            return 1.0

        return covariance / variance_b

    def _calculate_half_life(self, spread: np.ndarray) -> float:
        """반감기 계산 (mean reversion 속도)"""
        if len(spread) < 2:
            return 0.0

        spread_lag = spread[:-1]
        spread_curr = spread[1:]

        covariance = np.cov(spread_lag, spread_curr)[0, 1]
        variance = np.var(spread_lag, ddof=1)

        if variance == 0:
            return 0.0

        beta = covariance / variance

        if beta >= 1 or beta <= 0:
            return 0.0

        half_life = -np.log(2) / np.log(beta)

        return float(half_life)

    def _estimate_p_value_from_critical(
        self,
        test_stat: float,
        critical_values: np.ndarray
    ) -> float:
        """
        Critical value로부터 p-value 추정

        Args:
            test_stat: 테스트 통계량
            critical_values: [90%, 95%, 99%] critical values

        Returns:
            추정된 p-value
        """
        cv_90, cv_95, cv_99 = critical_values

        if test_stat > cv_99:
            return 0.005  # p < 0.01
        elif test_stat > cv_95:
            return 0.03   # 0.01 < p < 0.05
        elif test_stat > cv_90:
            return 0.07   # 0.05 < p < 0.10
        else:
            return 0.15   # p > 0.10

    def _determine_significance(self, p_value: float) -> SignificanceLevel:
        """통계적 유의성 판단"""
        if p_value < 0.01:
            return SignificanceLevel.HIGHLY_SIG
        elif p_value < 0.05:
            return SignificanceLevel.SIGNIFICANT
        elif p_value < 0.10:
            return SignificanceLevel.MARGINAL
        else:
            return SignificanceLevel.NOT_SIG


# 전역 인스턴스
_analyzer: Optional[CointegrationAnalyzer] = None


def get_analyzer() -> CointegrationAnalyzer:
    """전역 분석기 인스턴스 반환"""
    global _analyzer
    if _analyzer is None:
        _analyzer = CointegrationAnalyzer()
    return _analyzer

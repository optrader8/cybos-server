"""
Spread Analyzer - 스프레드 분석기

페어의 스프레드를 분석하고 Z-score를 계산합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta


class SpreadAnalyzer:
    """스프레드 분석 클래스"""

    def __init__(
        self,
        lookback_period: int = 60,
        z_score_entry: float = 2.0,
        z_score_exit: float = 0.5
    ):
        """
        Args:
            lookback_period: 스프레드 계산 기간 (일)
            z_score_entry: 진입 Z-score 임계값
            z_score_exit: 청산 Z-score 임계값
        """
        self.lookback_period = lookback_period
        self.z_score_entry = z_score_entry
        self.z_score_exit = z_score_exit

    def calculate_spread(
        self,
        prices_a: List[float],
        prices_b: List[float],
        hedge_ratio: float = 1.0
    ) -> np.ndarray:
        """
        스프레드 계산

        Args:
            prices_a: 종목 A 가격 시계열
            prices_b: 종목 B 가격 시계열
            hedge_ratio: 헤지 비율

        Returns:
            스프레드 시계열
        """
        if len(prices_a) != len(prices_b):
            raise ValueError("Price series must have same length")

        prices_a = np.array(prices_a)
        prices_b = np.array(prices_b)

        # 스프레드 = A - hedge_ratio * B
        spread = prices_a - hedge_ratio * prices_b

        return spread

    def calculate_z_score(self, spread: np.ndarray, window: int = None) -> float:
        """
        Z-score 계산

        Args:
            spread: 스프레드 시계열
            window: 계산 윈도우 (None이면 전체 사용)

        Returns:
            현재 Z-score
        """
        if len(spread) == 0:
            return 0.0

        if window is None:
            window = len(spread)

        # 최근 window 기간 데이터 사용
        recent_spread = spread[-window:]

        mean = np.mean(recent_spread)
        std = np.std(recent_spread, ddof=1)

        if std == 0:
            return 0.0

        # 현재 스프레드의 Z-score
        current_spread = spread[-1]
        z_score = (current_spread - mean) / std

        return z_score

    def calculate_spread_stats(
        self,
        spread: np.ndarray,
        window: int = None
    ) -> Dict[str, float]:
        """
        스프레드 통계 계산

        Args:
            spread: 스프레드 시계열
            window: 계산 윈도우

        Returns:
            통계 정보 딕셔너리
        """
        if window is None:
            window = len(spread)

        recent_spread = spread[-window:]

        return {
            "mean": float(np.mean(recent_spread)),
            "std": float(np.std(recent_spread, ddof=1)),
            "min": float(np.min(recent_spread)),
            "max": float(np.max(recent_spread)),
            "current": float(spread[-1]),
            "z_score": self.calculate_z_score(spread, window)
        }

    def detect_entry_signal(
        self,
        spread: np.ndarray,
        window: int = None
    ) -> Optional[str]:
        """
        진입 신호 감지

        Args:
            spread: 스프레드 시계열
            window: 계산 윈도우

        Returns:
            신호 타입 ("LONG", "SHORT", None)
        """
        z_score = self.calculate_z_score(spread, window)

        # Z-score가 높으면 스프레드가 평균보다 높음 -> SHORT (mean reversion)
        if z_score > self.z_score_entry:
            return "SHORT"

        # Z-score가 낮으면 스프레드가 평균보다 낮음 -> LONG (mean reversion)
        if z_score < -self.z_score_entry:
            return "LONG"

        return None

    def detect_exit_signal(
        self,
        spread: np.ndarray,
        position_type: str,
        window: int = None
    ) -> bool:
        """
        청산 신호 감지

        Args:
            spread: 스프레드 시계열
            position_type: 포지션 타입 ("LONG", "SHORT")
            window: 계산 윈도우

        Returns:
            청산 여부
        """
        z_score = self.calculate_z_score(spread, window)

        # LONG 포지션: Z-score가 exit 임계값 이상으로 회귀하면 청산
        if position_type == "LONG":
            return z_score >= -self.z_score_exit

        # SHORT 포지션: Z-score가 exit 임계값 이하로 회귀하면 청산
        if position_type == "SHORT":
            return z_score <= self.z_score_exit

        return False

    def calculate_optimal_hedge_ratio(
        self,
        prices_a: List[float],
        prices_b: List[float]
    ) -> float:
        """
        최적 헤지 비율 계산 (OLS 회귀)

        Args:
            prices_a: 종목 A 가격 시계열
            prices_b: 종목 B 가격 시계열

        Returns:
            최적 헤지 비율
        """
        if len(prices_a) != len(prices_b) or len(prices_a) < 2:
            return 1.0

        prices_a = np.array(prices_a)
        prices_b = np.array(prices_b)

        # OLS: A = beta * B + alpha
        # beta = cov(A, B) / var(B)
        covariance = np.cov(prices_a, prices_b)[0, 1]
        variance_b = np.var(prices_b, ddof=1)

        if variance_b == 0:
            return 1.0

        hedge_ratio = covariance / variance_b

        return hedge_ratio

    def calculate_half_life(self, spread: np.ndarray) -> float:
        """
        반감기 계산 (mean reversion 속도)

        Args:
            spread: 스프레드 시계열

        Returns:
            반감기 (일)
        """
        if len(spread) < 2:
            return 0.0

        # AR(1) 모델: spread(t) = alpha + beta * spread(t-1) + epsilon
        # 반감기 = -log(2) / log(beta)

        spread_lag = spread[:-1]
        spread_curr = spread[1:]

        # OLS 회귀
        covariance = np.cov(spread_lag, spread_curr)[0, 1]
        variance = np.var(spread_lag, ddof=1)

        if variance == 0:
            return 0.0

        beta = covariance / variance

        if beta >= 1 or beta <= 0:
            return 0.0  # Mean reversion 없음

        half_life = -np.log(2) / np.log(beta)

        return half_life

    def is_spread_stable(
        self,
        spread: np.ndarray,
        max_half_life: float = 60.0
    ) -> bool:
        """
        스프레드 안정성 확인

        Args:
            spread: 스프레드 시계열
            max_half_life: 최대 허용 반감기

        Returns:
            안정성 여부
        """
        half_life = self.calculate_half_life(spread)

        # 반감기가 0이면 mean reversion 없음
        if half_life <= 0:
            return False

        # 반감기가 너무 길면 mean reversion이 느림
        if half_life > max_half_life:
            return False

        return True

    def calculate_confidence(
        self,
        spread: np.ndarray,
        z_score: float
    ) -> float:
        """
        신호 신뢰도 계산

        Args:
            spread: 스프레드 시계열
            z_score: 현재 Z-score

        Returns:
            신뢰도 (0.0 ~ 1.0)
        """
        # Z-score 절대값이 클수록 신뢰도 높음
        z_confidence = min(abs(z_score) / 3.0, 1.0)

        # 스프레드 안정성 확인
        is_stable = self.is_spread_stable(spread)
        stability_confidence = 1.0 if is_stable else 0.5

        # 종합 신뢰도
        confidence = z_confidence * stability_confidence

        return confidence

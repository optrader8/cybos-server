"""
Signal Generator 테스트

신호 생성기의 주요 기능을 테스트합니다.
"""

import pytest
import numpy as np
from datetime import datetime

from src.services.signal_generator import SpreadAnalyzer


class TestSpreadAnalyzer:
    """스프레드 분석기 테스트"""

    def test_analyzer_initialization(self):
        """분석기 초기화 테스트"""
        analyzer = SpreadAnalyzer(
            lookback_period=60,
            z_score_entry=2.0,
            z_score_exit=0.5
        )

        assert analyzer.lookback_period == 60
        assert analyzer.z_score_entry == 2.0
        assert analyzer.z_score_exit == 0.5

    def test_calculate_spread(self):
        """스프레드 계산 테스트"""
        analyzer = SpreadAnalyzer()

        prices_a = [100, 101, 102, 103, 104]
        prices_b = [50, 51, 52, 53, 54]
        hedge_ratio = 2.0

        spread = analyzer.calculate_spread(prices_a, prices_b, hedge_ratio)

        # spread = A - 2*B
        expected = np.array([100 - 2*50, 101 - 2*51, 102 - 2*52, 103 - 2*53, 104 - 2*54])

        assert len(spread) == 5
        assert np.allclose(spread, expected)

    def test_calculate_z_score(self):
        """Z-score 계산 테스트"""
        analyzer = SpreadAnalyzer()

        # 평균 0, 표준편차 1인 스프레드 시계열
        spread = np.array([0, 1, 0, -1, 0, 1, 2])  # 마지막 값이 높음

        z_score = analyzer.calculate_z_score(spread)

        assert isinstance(z_score, float)
        assert z_score > 0  # 마지막 값이 평균보다 높음

    def test_calculate_spread_stats(self):
        """스프레드 통계 계산 테스트"""
        analyzer = SpreadAnalyzer()

        spread = np.array([0, 1, 2, 3, 4, 5])

        stats = analyzer.calculate_spread_stats(spread)

        assert "mean" in stats
        assert "std" in stats
        assert "min" in stats
        assert "max" in stats
        assert "current" in stats
        assert "z_score" in stats

        assert stats["mean"] == 2.5
        assert stats["min"] == 0
        assert stats["max"] == 5
        assert stats["current"] == 5

    def test_detect_entry_signal_long(self):
        """진입 신호 감지 테스트 - LONG"""
        analyzer = SpreadAnalyzer(z_score_entry=2.0)

        # Z-score가 -2 이하인 스프레드 (mean reversion LONG 신호)
        spread = np.array([0, 0, 0, 0, -5])

        signal = analyzer.detect_entry_signal(spread)

        assert signal == "LONG"

    def test_detect_entry_signal_short(self):
        """진입 신호 감지 테스트 - SHORT"""
        analyzer = SpreadAnalyzer(z_score_entry=2.0)

        # Z-score가 2 이상인 스프레드 (mean reversion SHORT 신호)
        spread = np.array([0, 0, 0, 0, 5])

        signal = analyzer.detect_entry_signal(spread)

        assert signal == "SHORT"

    def test_detect_entry_signal_none(self):
        """진입 신호 없음 테스트"""
        analyzer = SpreadAnalyzer(z_score_entry=2.0)

        # Z-score가 임계값 범위 내
        spread = np.array([0, 0, 0, 0, 0.5])

        signal = analyzer.detect_entry_signal(spread)

        assert signal is None

    def test_detect_exit_signal_long(self):
        """청산 신호 감지 테스트 - LONG"""
        analyzer = SpreadAnalyzer(z_score_exit=0.5)

        # LONG 포지션: Z-score가 exit 임계값 이상으로 회귀
        spread = np.array([0, 0, 0, 0, 0.6])

        should_exit = analyzer.detect_exit_signal(spread, "LONG")

        assert should_exit is True

    def test_detect_exit_signal_short(self):
        """청산 신호 감지 테스트 - SHORT"""
        analyzer = SpreadAnalyzer(z_score_exit=0.5)

        # SHORT 포지션: Z-score가 exit 임계값 이하로 회귀
        spread = np.array([0, 0, 0, 0, 0.3])

        should_exit = analyzer.detect_exit_signal(spread, "SHORT")

        assert should_exit is True

    def test_calculate_optimal_hedge_ratio(self):
        """최적 헤지 비율 계산 테스트"""
        analyzer = SpreadAnalyzer()

        # 선형 관계: A = 2*B + noise
        np.random.seed(42)
        prices_b = np.linspace(50, 100, 100)
        prices_a = 2 * prices_b + np.random.normal(0, 1, 100)

        hedge_ratio = analyzer.calculate_optimal_hedge_ratio(
            prices_a.tolist(),
            prices_b.tolist()
        )

        assert isinstance(hedge_ratio, float)
        assert 1.8 < hedge_ratio < 2.2  # 2에 근접해야 함

    def test_calculate_half_life(self):
        """반감기 계산 테스트"""
        analyzer = SpreadAnalyzer()

        # Mean reverting 시계열
        spread = np.array([0, 1, 0.5, 0.25, 0.125, 0.06])

        half_life = analyzer.calculate_half_life(spread)

        assert isinstance(half_life, float)
        assert half_life > 0

    def test_is_spread_stable(self):
        """스프레드 안정성 확인 테스트"""
        analyzer = SpreadAnalyzer()

        # Mean reverting 스프레드 (안정적)
        spread = np.array([0, 1, 0.5, 0.25, 0, -0.25, 0])

        is_stable = analyzer.is_spread_stable(spread, max_half_life=60)

        assert isinstance(is_stable, bool)

    def test_calculate_confidence(self):
        """신호 신뢰도 계산 테스트"""
        analyzer = SpreadAnalyzer()

        # Z-score가 높은 스프레드
        spread = np.array([0, 0, 0, 0, 5])
        z_score = analyzer.calculate_z_score(spread)

        confidence = analyzer.calculate_confidence(spread, z_score)

        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_calculate_confidence_low_z_score(self):
        """낮은 Z-score의 신뢰도 테스트"""
        analyzer = SpreadAnalyzer()

        # Z-score가 낮은 스프레드
        spread = np.array([0, 0, 0, 0, 0.1])
        z_score = analyzer.calculate_z_score(spread)

        confidence = analyzer.calculate_confidence(spread, z_score)

        assert confidence < 0.5  # 낮은 신뢰도

    def test_spread_calculation_length_mismatch(self):
        """길이가 다른 가격 시계열에 대한 스프레드 계산 테스트"""
        analyzer = SpreadAnalyzer()

        prices_a = [100, 101, 102]
        prices_b = [50, 51]  # 길이가 다름

        with pytest.raises(ValueError):
            analyzer.calculate_spread(prices_a, prices_b, 1.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

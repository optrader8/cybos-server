"""
Backtest Engine 테스트

백테스트 엔진의 주요 기능을 테스트합니다.
"""

import pytest
from datetime import datetime, timedelta
import numpy as np

from src.services.backtest_engine import (
    BacktestEngine,
    BacktestConfig,
    Portfolio,
    PerformanceMetrics
)


class TestPortfolio:
    """포트폴리오 테스트"""

    def test_portfolio_initialization(self):
        """포트폴리오 초기화 테스트"""
        portfolio = Portfolio(initial_capital=10000000)

        assert portfolio.initial_capital == 10000000
        assert portfolio.cash == 10000000
        assert portfolio.total_value == 10000000
        assert len(portfolio.positions) == 0
        assert len(portfolio.pair_positions) == 0

    def test_add_position(self):
        """포지션 추가 테스트"""
        portfolio = Portfolio(initial_capital=10000000)
        date = datetime.now()

        # 포지션 추가
        success = portfolio.add_position("005930", 100, 70000, date)

        assert success is True
        assert "005930" in portfolio.positions
        assert portfolio.positions["005930"].quantity == 100
        assert portfolio.positions["005930"].entry_price == 70000
        assert portfolio.cash == 10000000 - 7000000  # 3,000,000

    def test_add_position_insufficient_funds(self):
        """자금 부족 시 포지션 추가 실패 테스트"""
        portfolio = Portfolio(initial_capital=1000000)
        date = datetime.now()

        # 자금 부족으로 실패해야 함
        success = portfolio.add_position("005930", 100, 70000, date)

        assert success is False
        assert "005930" not in portfolio.positions

    def test_close_position(self):
        """포지션 청산 테스트"""
        portfolio = Portfolio(initial_capital=10000000)
        date = datetime.now()

        # 포지션 추가
        portfolio.add_position("005930", 100, 70000, date)

        # 포지션 청산 (10% 수익)
        trade = portfolio.close_position("005930", 77000, date + timedelta(days=5))

        assert trade is not None
        assert trade["pnl"] == 700000  # 10% profit
        assert "005930" not in portfolio.positions
        assert portfolio.cash == 10000000 - 7000000 + 7700000

    def test_add_pair_position(self):
        """페어 포지션 추가 테스트"""
        portfolio = Portfolio(initial_capital=10000000)
        date = datetime.now()

        # 페어 포지션 추가
        success = portfolio.add_pair_position(
            pair_id="005930_000660",
            long_code="005930",
            short_code="000660",
            long_qty=100,
            short_qty=200,
            long_price=70000,
            short_price=100000,
            date=date,
            hedge_ratio=1.0
        )

        assert success is True
        assert "005930_000660" in portfolio.pair_positions
        assert portfolio.pair_positions["005930_000660"].long_position.quantity == 100
        assert portfolio.pair_positions["005930_000660"].short_position.quantity == -200


class TestPerformanceMetrics:
    """성과 지표 테스트"""

    def test_total_return(self):
        """총 수익률 계산 테스트"""
        initial = 10000000
        final = 12000000

        total_ret = PerformanceMetrics.total_return(initial, final)

        assert total_ret == 20.0  # 20% return

    def test_sharpe_ratio(self):
        """샤프 비율 계산 테스트"""
        # 랜덤 수익률 생성 (평균 0.1%, 표준편차 1%)
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.01, 252)

        sharpe = PerformanceMetrics.sharpe_ratio(returns, risk_free_rate=0.03)

        assert isinstance(sharpe, float)
        assert -10 < sharpe < 10  # 합리적 범위

    def test_max_drawdown(self):
        """최대 낙폭 계산 테스트"""
        equity_curve = [
            (datetime(2024, 1, 1), 10000000),
            (datetime(2024, 1, 2), 10500000),
            (datetime(2024, 1, 3), 10300000),
            (datetime(2024, 1, 4), 9800000),  # 최대 낙폭 지점
            (datetime(2024, 1, 5), 10100000),
        ]

        max_dd, dd_period = PerformanceMetrics.max_drawdown(equity_curve)

        assert max_dd < 0  # 낙폭은 음수
        assert dd_period >= 0

    def test_win_rate(self):
        """승률 계산 테스트"""
        trades = [
            {"pnl": 100000},  # 승
            {"pnl": -50000},  # 패
            {"pnl": 80000},   # 승
            {"pnl": 120000},  # 승
        ]

        win_rate = PerformanceMetrics.win_rate(trades)

        assert win_rate == 75.0  # 3/4 = 75%

    def test_profit_factor(self):
        """손익비 계산 테스트"""
        trades = [
            {"pnl": 100000},
            {"pnl": -50000},
            {"pnl": 80000},
        ]

        profit_factor = PerformanceMetrics.profit_factor(trades)

        assert profit_factor == (100000 + 80000) / 50000  # 3.6


class TestBacktestEngine:
    """백테스트 엔진 테스트"""

    def test_backtest_engine_initialization(self):
        """백테스트 엔진 초기화 테스트"""
        config = BacktestConfig(
            initial_capital=10000000,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )

        engine = BacktestEngine(config)

        assert engine.config == config
        assert engine.portfolio.initial_capital == 10000000

    def test_backtest_with_mock_data(self):
        """Mock 데이터로 백테스트 실행 테스트"""
        config = BacktestConfig(
            initial_capital=10000000,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10)
        )

        engine = BacktestEngine(config)

        # Mock 가격 데이터
        price_data = {
            "005930": {
                datetime(2024, 1, 1): 70000,
                datetime(2024, 1, 2): 71000,
                datetime(2024, 1, 3): 72000,
                datetime(2024, 1, 4): 71500,
                datetime(2024, 1, 5): 73000,
            }
        }

        # Mock 신호
        signals = [
            {
                "date": datetime(2024, 1, 2),
                "signal_type": "LONG",
                "stock_code": "005930",
                "quantity": 100
            },
            {
                "date": datetime(2024, 1, 5),
                "signal_type": "LONG",
                "stock_code": "005930",
                "quantity": 100
            }
        ]

        # 백테스트 실행
        result = engine.run(price_data, signals)

        assert result is not None
        assert isinstance(result.metrics, dict)
        assert "total_return" in result.metrics
        assert "sharpe_ratio" in result.metrics
        assert len(result.equity_curve) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

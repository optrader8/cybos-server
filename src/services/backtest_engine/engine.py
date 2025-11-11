"""
Backtest Engine - 백테스트 엔진

페어 트레이딩 전략 백테스트를 실행합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .portfolio import Portfolio
from .simulator import TradingSimulator
from .metrics import PerformanceMetrics


@dataclass
class BacktestConfig:
    """백테스트 설정"""
    initial_capital: float
    start_date: datetime
    end_date: datetime
    commission_rate: float = 0.0015
    slippage_rate: float = 0.001
    impact_cost_rate: float = 0.0005
    risk_free_rate: float = 0.03


@dataclass
class BacktestResult:
    """백테스트 결과"""
    config: BacktestConfig
    portfolio: Portfolio
    metrics: Dict[str, float]
    trades: List[dict]
    equity_curve: List[tuple]


class BacktestEngine:
    """백테스트 엔진"""

    def __init__(self, config: BacktestConfig):
        """
        Args:
            config: 백테스트 설정
        """
        self.config = config
        self.portfolio = Portfolio(initial_capital=config.initial_capital)
        self.simulator = TradingSimulator(
            commission_rate=config.commission_rate,
            slippage_rate=config.slippage_rate,
            impact_cost_rate=config.impact_cost_rate
        )

    def run(
        self,
        price_data: Dict[str, Dict[datetime, float]],
        signals: List[dict]
    ) -> BacktestResult:
        """
        백테스트 실행

        Args:
            price_data: 가격 데이터 {stock_code: {date: price}}
            signals: 트레이딩 신호 목록

        Returns:
            BacktestResult
        """
        # 신호를 날짜순으로 정렬
        sorted_signals = sorted(signals, key=lambda x: x["date"])

        # 백테스트 기간 동안 일별로 실행
        current_date = self.config.start_date
        signal_idx = 0

        while current_date <= self.config.end_date:
            # 현재 날짜의 가격 수집
            current_prices = self._get_prices_for_date(price_data, current_date)

            # 포트폴리오 가격 업데이트
            if current_prices:
                self.portfolio.update_prices(current_prices, current_date)

            # 현재 날짜의 신호 처리
            while signal_idx < len(sorted_signals):
                signal = sorted_signals[signal_idx]
                signal_date = signal["date"]

                if signal_date > current_date:
                    break

                if signal_date == current_date:
                    self._execute_signal(signal, current_prices, current_date)

                signal_idx += 1

            # 다음 날짜로 이동 (영업일 기준)
            current_date += timedelta(days=1)

        # 성과 지표 계산
        metrics = PerformanceMetrics.calculate_all_metrics(
            initial_capital=self.config.initial_capital,
            final_capital=self.portfolio.total_value,
            equity_curve=self.portfolio.equity_curve,
            trades=self.portfolio.trades,
            risk_free_rate=self.config.risk_free_rate
        )

        return BacktestResult(
            config=self.config,
            portfolio=self.portfolio,
            metrics=metrics,
            trades=self.portfolio.trades,
            equity_curve=self.portfolio.equity_curve
        )

    def _get_prices_for_date(
        self,
        price_data: Dict[str, Dict[datetime, float]],
        date: datetime
    ) -> Dict[str, float]:
        """특정 날짜의 가격 조회"""
        prices = {}
        for stock_code, date_prices in price_data.items():
            if date in date_prices:
                prices[stock_code] = date_prices[date]
        return prices

    def _execute_signal(
        self,
        signal: dict,
        current_prices: Dict[str, float],
        date: datetime
    ) -> None:
        """신호 실행"""
        signal_type = signal.get("signal_type", "")

        if signal_type == "PAIR_ENTRY_LONG":
            self._execute_pair_entry(signal, current_prices, date)
        elif signal_type == "PAIR_EXIT":
            self._execute_pair_exit(signal, current_prices, date)
        elif signal_type == "LONG":
            self._execute_long(signal, current_prices, date)
        elif signal_type == "SHORT":
            self._execute_short(signal, current_prices, date)

    def _execute_pair_entry(
        self,
        signal: dict,
        current_prices: Dict[str, float],
        date: datetime
    ) -> None:
        """페어 진입 실행"""
        pair_id = signal.get("pair_id")
        long_code = signal.get("long_code")
        short_code = signal.get("short_code")

        if not all([pair_id, long_code, short_code]):
            return

        # 현재 가격 확인
        if long_code not in current_prices or short_code not in current_prices:
            return

        long_price = current_prices[long_code]
        short_price = current_prices[short_code]

        # 수량 계산 (신호에 있으면 사용, 없으면 기본값)
        long_qty = signal.get("long_quantity", 100)
        short_qty = signal.get("short_quantity", 100)
        hedge_ratio = signal.get("hedge_ratio", 1.0)

        # 페어 트레이드 실행
        success, error = self.simulator.execute_pair_trade(
            portfolio=self.portfolio,
            pair_id=pair_id,
            long_code=long_code,
            short_code=short_code,
            long_qty=long_qty,
            short_qty=short_qty,
            long_price=long_price,
            short_price=short_price,
            date=date,
            hedge_ratio=hedge_ratio
        )

        if not success:
            print(f"Failed to execute pair entry for {pair_id}: {error}")

    def _execute_pair_exit(
        self,
        signal: dict,
        current_prices: Dict[str, float],
        date: datetime
    ) -> None:
        """페어 청산 실행"""
        pair_id = signal.get("pair_id")

        if not pair_id or pair_id not in self.portfolio.pair_positions:
            return

        pair = self.portfolio.pair_positions[pair_id]
        long_code = pair.long_position.stock_code
        short_code = pair.short_position.stock_code

        # 현재 가격 확인
        if long_code not in current_prices or short_code not in current_prices:
            return

        long_price = current_prices[long_code]
        short_price = current_prices[short_code]

        # 페어 트레이드 청산
        success, error, trade = self.simulator.close_pair_trade(
            portfolio=self.portfolio,
            pair_id=pair_id,
            long_price=long_price,
            short_price=short_price,
            date=date
        )

        if not success:
            print(f"Failed to close pair {pair_id}: {error}")

    def _execute_long(
        self,
        signal: dict,
        current_prices: Dict[str, float],
        date: datetime
    ) -> None:
        """롱 포지션 실행"""
        stock_code = signal.get("stock_code")
        quantity = signal.get("quantity", 100)

        if not stock_code or stock_code not in current_prices:
            return

        price = current_prices[stock_code]

        success, error = self.simulator.execute_long(
            portfolio=self.portfolio,
            stock_code=stock_code,
            quantity=quantity,
            price=price,
            date=date
        )

        if not success:
            print(f"Failed to execute long for {stock_code}: {error}")

    def _execute_short(
        self,
        signal: dict,
        current_prices: Dict[str, float],
        date: datetime
    ) -> None:
        """숏 포지션 실행"""
        stock_code = signal.get("stock_code")
        quantity = signal.get("quantity", 100)

        if not stock_code or stock_code not in current_prices:
            return

        price = current_prices[stock_code]

        success, error = self.simulator.execute_short(
            portfolio=self.portfolio,
            stock_code=stock_code,
            quantity=quantity,
            price=price,
            date=date
        )

        if not success:
            print(f"Failed to execute short for {stock_code}: {error}")

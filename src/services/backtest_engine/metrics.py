"""
Performance Metrics - 백테스트 성과 지표 계산

백테스트 결과에 대한 다양한 성과 지표를 계산합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime


class PerformanceMetrics:
    """성과 지표 계산 클래스"""

    @staticmethod
    def calculate_returns(equity_curve: List[Tuple[datetime, float]]) -> np.ndarray:
        """수익률 계산"""
        if len(equity_curve) < 2:
            return np.array([])

        values = np.array([value for _, value in equity_curve])
        returns = np.diff(values) / values[:-1]

        return returns

    @staticmethod
    def total_return(initial_capital: float, final_capital: float) -> float:
        """총 수익률 (%)"""
        if initial_capital == 0:
            return 0.0
        return ((final_capital - initial_capital) / initial_capital) * 100

    @staticmethod
    def annualized_return(total_return_pct: float, days: int) -> float:
        """연환산 수익률 (%)"""
        if days == 0:
            return 0.0

        years = days / 252  # 영업일 기준
        if years == 0:
            return 0.0

        compound_return = (1 + total_return_pct / 100)
        annualized = (compound_return ** (1 / years) - 1) * 100

        return annualized

    @staticmethod
    def sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.03) -> float:
        """샤프 비율"""
        if len(returns) == 0:
            return 0.0

        # 일간 무위험 수익률
        daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1

        excess_returns = returns - daily_rf
        mean_excess = np.mean(excess_returns)
        std_excess = np.std(excess_returns, ddof=1)

        if std_excess == 0:
            return 0.0

        # 연환산
        sharpe = (mean_excess / std_excess) * np.sqrt(252)

        return sharpe

    @staticmethod
    def sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.03) -> float:
        """소르티노 비율 (하방 위험만 고려)"""
        if len(returns) == 0:
            return 0.0

        # 일간 무위험 수익률
        daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1

        excess_returns = returns - daily_rf
        mean_excess = np.mean(excess_returns)

        # 하방 편차 (음수 수익률만)
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0:
            return 0.0

        downside_std = np.std(downside_returns, ddof=1)
        if downside_std == 0:
            return 0.0

        # 연환산
        sortino = (mean_excess / downside_std) * np.sqrt(252)

        return sortino

    @staticmethod
    def max_drawdown(equity_curve: List[Tuple[datetime, float]]) -> Tuple[float, int]:
        """최대 낙폭 (MDD) 및 기간"""
        if len(equity_curve) < 2:
            return 0.0, 0

        values = np.array([value for _, value in equity_curve])
        cummax = np.maximum.accumulate(values)
        drawdowns = (values - cummax) / cummax * 100

        max_dd = np.min(drawdowns)
        max_dd_idx = np.argmin(drawdowns)

        # MDD 기간 계산 (피크부터 바닥까지)
        peak_idx = np.argmax(values[:max_dd_idx + 1])
        dd_period = max_dd_idx - peak_idx

        return max_dd, dd_period

    @staticmethod
    def calmar_ratio(annualized_return: float, max_drawdown: float) -> float:
        """칼마 비율 (연환산 수익률 / MDD)"""
        if max_drawdown >= 0:  # MDD는 음수여야 함
            return 0.0

        return annualized_return / abs(max_drawdown)

    @staticmethod
    def win_rate(trades: List[dict]) -> float:
        """승률 (%)"""
        if len(trades) == 0:
            return 0.0

        winning_trades = sum(1 for trade in trades if trade.get("pnl", 0) > 0)
        return (winning_trades / len(trades)) * 100

    @staticmethod
    def profit_factor(trades: List[dict]) -> float:
        """손익비 (총 이익 / 총 손실)"""
        if len(trades) == 0:
            return 0.0

        total_profit = sum(trade.get("pnl", 0) for trade in trades if trade.get("pnl", 0) > 0)
        total_loss = abs(sum(trade.get("pnl", 0) for trade in trades if trade.get("pnl", 0) < 0))

        if total_loss == 0:
            return float('inf') if total_profit > 0 else 0.0

        return total_profit / total_loss

    @staticmethod
    def average_win(trades: List[dict]) -> float:
        """평균 수익"""
        winning_trades = [trade.get("pnl", 0) for trade in trades if trade.get("pnl", 0) > 0]
        if len(winning_trades) == 0:
            return 0.0
        return np.mean(winning_trades)

    @staticmethod
    def average_loss(trades: List[dict]) -> float:
        """평균 손실"""
        losing_trades = [trade.get("pnl", 0) for trade in trades if trade.get("pnl", 0) < 0]
        if len(losing_trades) == 0:
            return 0.0
        return np.mean(losing_trades)

    @staticmethod
    def average_holding_period(trades: List[dict]) -> float:
        """평균 보유 기간 (일)"""
        if len(trades) == 0:
            return 0.0

        holding_periods = [trade.get("holding_days", 0) for trade in trades]
        return np.mean(holding_periods)

    @classmethod
    def calculate_all_metrics(
        cls,
        initial_capital: float,
        final_capital: float,
        equity_curve: List[Tuple[datetime, float]],
        trades: List[dict],
        risk_free_rate: float = 0.03
    ) -> Dict[str, float]:
        """모든 성과 지표 계산"""

        # 수익률 계산
        returns = cls.calculate_returns(equity_curve)

        # 기간 계산
        if len(equity_curve) >= 2:
            start_date = equity_curve[0][0]
            end_date = equity_curve[-1][0]
            days = (end_date - start_date).days
        else:
            days = 0

        # 총 수익률
        total_ret = cls.total_return(initial_capital, final_capital)

        # 연환산 수익률
        ann_ret = cls.annualized_return(total_ret, days)

        # 샤프/소르티노 비율
        sharpe = cls.sharpe_ratio(returns, risk_free_rate)
        sortino = cls.sortino_ratio(returns, risk_free_rate)

        # 최대 낙폭
        max_dd, dd_period = cls.max_drawdown(equity_curve)

        # 칼마 비율
        calmar = cls.calmar_ratio(ann_ret, max_dd)

        # 거래 통계
        win_rate = cls.win_rate(trades)
        profit_factor = cls.profit_factor(trades)
        avg_win = cls.average_win(trades)
        avg_loss = cls.average_loss(trades)
        avg_holding = cls.average_holding_period(trades)

        # 변동성
        volatility = np.std(returns, ddof=1) * np.sqrt(252) * 100 if len(returns) > 0 else 0.0

        return {
            "total_return": total_ret,
            "annualized_return": ann_ret,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown": max_dd,
            "max_drawdown_period": dd_period,
            "calmar_ratio": calmar,
            "volatility": volatility,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "average_win": avg_win,
            "average_loss": avg_loss,
            "average_holding_period": avg_holding,
            "total_trades": len(trades),
            "trading_days": days
        }

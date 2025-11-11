"""
Portfolio Manager - 백테스트 포트폴리오 관리

백테스트 중 포트폴리오 상태를 관리합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class Position:
    """포지션 정보"""
    stock_code: str
    quantity: int
    entry_price: float
    entry_date: datetime
    current_price: float = 0.0

    @property
    def value(self) -> float:
        """현재 포지션 가치"""
        return self.quantity * self.current_price

    @property
    def cost(self) -> float:
        """포지션 비용"""
        return self.quantity * self.entry_price

    @property
    def pnl(self) -> float:
        """손익"""
        return self.value - self.cost

    @property
    def pnl_pct(self) -> float:
        """손익률 (%)"""
        if self.cost == 0:
            return 0.0
        return (self.pnl / self.cost) * 100


@dataclass
class PairPosition:
    """페어 포지션 (롱/숏 동시 보유)"""
    pair_id: str
    long_position: Position
    short_position: Position
    entry_date: datetime
    hedge_ratio: float = 1.0

    @property
    def total_value(self) -> float:
        """총 포지션 가치"""
        return abs(self.long_position.value) + abs(self.short_position.value)

    @property
    def total_cost(self) -> float:
        """총 포지션 비용"""
        return abs(self.long_position.cost) + abs(self.short_position.cost)

    @property
    def net_pnl(self) -> float:
        """순 손익"""
        return self.long_position.pnl + self.short_position.pnl

    @property
    def net_pnl_pct(self) -> float:
        """순 손익률 (%)"""
        if self.total_cost == 0:
            return 0.0
        return (self.net_pnl / self.total_cost) * 100


@dataclass
class Portfolio:
    """백테스트 포트폴리오"""

    initial_capital: float
    cash: float = 0.0
    positions: Dict[str, Position] = field(default_factory=dict)
    pair_positions: Dict[str, PairPosition] = field(default_factory=dict)
    equity_curve: List[tuple] = field(default_factory=list)
    trades: List[dict] = field(default_factory=list)

    def __post_init__(self):
        """초기화"""
        if self.cash == 0.0:
            self.cash = self.initial_capital

    @property
    def total_position_value(self) -> float:
        """총 포지션 가치"""
        return sum(pos.value for pos in self.positions.values())

    @property
    def total_pair_value(self) -> float:
        """총 페어 포지션 가치"""
        return sum(pair.total_value for pair in self.pair_positions.values())

    @property
    def total_value(self) -> float:
        """총 포트폴리오 가치"""
        return self.cash + self.total_position_value + self.total_pair_value

    @property
    def invested_value(self) -> float:
        """투자 금액"""
        return self.total_position_value + self.total_pair_value

    @property
    def total_pnl(self) -> float:
        """총 손익"""
        return self.total_value - self.initial_capital

    @property
    def total_pnl_pct(self) -> float:
        """총 손익률 (%)"""
        if self.initial_capital == 0:
            return 0.0
        return (self.total_pnl / self.initial_capital) * 100

    def add_position(self, stock_code: str, quantity: int, price: float, date: datetime) -> bool:
        """포지션 추가"""
        cost = abs(quantity * price)

        if cost > self.cash:
            return False  # 자금 부족

        self.cash -= cost
        self.positions[stock_code] = Position(
            stock_code=stock_code,
            quantity=quantity,
            entry_price=price,
            entry_date=date,
            current_price=price
        )

        return True

    def close_position(self, stock_code: str, price: float, date: datetime) -> Optional[dict]:
        """포지션 청산"""
        if stock_code not in self.positions:
            return None

        position = self.positions[stock_code]
        proceeds = position.quantity * price
        pnl = proceeds - position.cost

        self.cash += proceeds

        # 거래 기록
        trade = {
            "stock_code": stock_code,
            "quantity": position.quantity,
            "entry_price": position.entry_price,
            "exit_price": price,
            "entry_date": position.entry_date,
            "exit_date": date,
            "pnl": pnl,
            "pnl_pct": position.pnl_pct,
            "holding_days": (date - position.entry_date).days
        }

        self.trades.append(trade)
        del self.positions[stock_code]

        return trade

    def add_pair_position(
        self,
        pair_id: str,
        long_code: str,
        short_code: str,
        long_qty: int,
        short_qty: int,
        long_price: float,
        short_price: float,
        date: datetime,
        hedge_ratio: float = 1.0
    ) -> bool:
        """페어 포지션 추가"""
        long_cost = long_qty * long_price
        short_cost = abs(short_qty * short_price)
        total_cost = long_cost + short_cost

        if total_cost > self.cash:
            return False  # 자금 부족

        self.cash -= total_cost

        long_position = Position(
            stock_code=long_code,
            quantity=long_qty,
            entry_price=long_price,
            entry_date=date,
            current_price=long_price
        )

        short_position = Position(
            stock_code=short_code,
            quantity=-abs(short_qty),  # 숏은 음수
            entry_price=short_price,
            entry_date=date,
            current_price=short_price
        )

        self.pair_positions[pair_id] = PairPosition(
            pair_id=pair_id,
            long_position=long_position,
            short_position=short_position,
            entry_date=date,
            hedge_ratio=hedge_ratio
        )

        return True

    def close_pair_position(
        self,
        pair_id: str,
        long_price: float,
        short_price: float,
        date: datetime
    ) -> Optional[dict]:
        """페어 포지션 청산"""
        if pair_id not in self.pair_positions:
            return None

        pair = self.pair_positions[pair_id]

        # 롱 포지션 청산
        long_proceeds = pair.long_position.quantity * long_price
        # 숏 포지션 청산 (숏은 이익이 반대)
        short_proceeds = abs(pair.short_position.quantity) * (pair.short_position.entry_price - short_price)

        total_proceeds = long_proceeds + short_proceeds
        total_cost = pair.total_cost
        pnl = pair.net_pnl

        self.cash += total_proceeds

        # 거래 기록
        trade = {
            "pair_id": pair_id,
            "long_code": pair.long_position.stock_code,
            "short_code": pair.short_position.stock_code,
            "entry_date": pair.entry_date,
            "exit_date": date,
            "total_cost": total_cost,
            "total_proceeds": total_proceeds,
            "pnl": pnl,
            "pnl_pct": pair.net_pnl_pct,
            "holding_days": (date - pair.entry_date).days
        }

        self.trades.append(trade)
        del self.pair_positions[pair_id]

        return trade

    def update_prices(self, prices: Dict[str, float], date: datetime) -> None:
        """가격 업데이트"""
        # 개별 포지션 가격 업데이트
        for stock_code, position in self.positions.items():
            if stock_code in prices:
                position.current_price = prices[stock_code]

        # 페어 포지션 가격 업데이트
        for pair in self.pair_positions.values():
            if pair.long_position.stock_code in prices:
                pair.long_position.current_price = prices[pair.long_position.stock_code]
            if pair.short_position.stock_code in prices:
                pair.short_position.current_price = prices[pair.short_position.stock_code]

        # 자산 곡선 기록
        self.equity_curve.append((date, self.total_value))

    def get_summary(self) -> dict:
        """포트폴리오 요약"""
        return {
            "initial_capital": self.initial_capital,
            "total_value": self.total_value,
            "cash": self.cash,
            "invested": self.invested_value,
            "total_pnl": self.total_pnl,
            "total_pnl_pct": self.total_pnl_pct,
            "num_positions": len(self.positions),
            "num_pair_positions": len(self.pair_positions),
            "num_trades": len(self.trades)
        }

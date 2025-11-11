"""
Trading Simulator - 백테스트 거래 시뮬레이터

거래 실행 및 거래 비용 계산을 시뮬레이션합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from typing import Dict, Tuple, Optional
from datetime import datetime
from .portfolio import Portfolio


class TradingSimulator:
    """거래 시뮬레이터"""

    def __init__(
        self,
        commission_rate: float = 0.0015,
        slippage_rate: float = 0.001,
        impact_cost_rate: float = 0.0005
    ):
        """
        Args:
            commission_rate: 수수료율 (0.15% 기본)
            slippage_rate: 슬리피지율 (0.1% 기본)
            impact_cost_rate: 시장 충격 비용율 (0.05% 기본)
        """
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.impact_cost_rate = impact_cost_rate

    def calculate_execution_price(
        self,
        base_price: float,
        quantity: int,
        is_buy: bool
    ) -> float:
        """
        실행 가격 계산 (슬리피지 및 시장 충격 포함)

        Args:
            base_price: 기준 가격
            quantity: 수량
            is_buy: 매수 여부

        Returns:
            실행 가격
        """
        # 슬리피지 (매수는 불리하게, 매도는 유리하게)
        slippage = base_price * self.slippage_rate * (1 if is_buy else -1)

        # 시장 충격 비용 (거래량에 비례)
        impact = base_price * self.impact_cost_rate * (1 if is_buy else -1)

        execution_price = base_price + slippage + impact

        return max(0, execution_price)  # 음수 방지

    def calculate_commission(self, trade_value: float) -> float:
        """
        수수료 계산

        Args:
            trade_value: 거래 금액

        Returns:
            수수료
        """
        return trade_value * self.commission_rate

    def execute_long(
        self,
        portfolio: Portfolio,
        stock_code: str,
        quantity: int,
        price: float,
        date: datetime
    ) -> Tuple[bool, Optional[str]]:
        """
        롱 포지션 실행

        Args:
            portfolio: 포트폴리오
            stock_code: 종목 코드
            quantity: 수량
            price: 기준 가격
            date: 거래 일시

        Returns:
            (성공 여부, 에러 메시지)
        """
        if quantity <= 0:
            return False, "Invalid quantity"

        # 실행 가격 계산
        execution_price = self.calculate_execution_price(price, quantity, is_buy=True)

        # 거래 금액
        trade_value = quantity * execution_price

        # 수수료 계산
        commission = self.calculate_commission(trade_value)

        # 총 필요 금액
        total_cost = trade_value + commission

        # 자금 확인
        if total_cost > portfolio.cash:
            return False, f"Insufficient funds: need {total_cost:,.0f}, have {portfolio.cash:,.0f}"

        # 포지션 추가
        success = portfolio.add_position(stock_code, quantity, execution_price, date)
        if not success:
            return False, "Failed to add position"

        # 수수료 차감
        portfolio.cash -= commission

        return True, None

    def execute_short(
        self,
        portfolio: Portfolio,
        stock_code: str,
        quantity: int,
        price: float,
        date: datetime
    ) -> Tuple[bool, Optional[str]]:
        """
        숏 포지션 실행 (실제로는 마진 필요)

        Args:
            portfolio: 포트폴리오
            stock_code: 종목 코드
            quantity: 수량
            price: 기준 가격
            date: 거래 일시

        Returns:
            (성공 여부, 에러 메시지)
        """
        if quantity <= 0:
            return False, "Invalid quantity"

        # 실행 가격 계산 (숏은 매도)
        execution_price = self.calculate_execution_price(price, quantity, is_buy=False)

        # 거래 금액
        trade_value = quantity * execution_price

        # 수수료 계산
        commission = self.calculate_commission(trade_value)

        # 마진 요구 (거래금액의 100% 담보)
        margin_required = trade_value + commission

        # 자금 확인
        if margin_required > portfolio.cash:
            return False, f"Insufficient margin: need {margin_required:,.0f}, have {portfolio.cash:,.0f}"

        # 포지션 추가 (수량은 음수)
        success = portfolio.add_position(stock_code, -quantity, execution_price, date)
        if not success:
            return False, "Failed to add position"

        # 수수료 및 마진 차감
        portfolio.cash -= margin_required

        return True, None

    def execute_pair_trade(
        self,
        portfolio: Portfolio,
        pair_id: str,
        long_code: str,
        short_code: str,
        long_qty: int,
        short_qty: int,
        long_price: float,
        short_price: float,
        date: datetime,
        hedge_ratio: float = 1.0
    ) -> Tuple[bool, Optional[str]]:
        """
        페어 트레이드 실행

        Args:
            portfolio: 포트폴리오
            pair_id: 페어 ID
            long_code: 롱 종목 코드
            short_code: 숏 종목 코드
            long_qty: 롱 수량
            short_qty: 숏 수량
            long_price: 롱 가격
            short_price: 숏 가격
            date: 거래 일시
            hedge_ratio: 헤지 비율

        Returns:
            (성공 여부, 에러 메시지)
        """
        if long_qty <= 0 or short_qty <= 0:
            return False, "Invalid quantities"

        # 실행 가격 계산
        long_exec_price = self.calculate_execution_price(long_price, long_qty, is_buy=True)
        short_exec_price = self.calculate_execution_price(short_price, short_qty, is_buy=False)

        # 거래 금액
        long_trade_value = long_qty * long_exec_price
        short_trade_value = short_qty * short_exec_price

        # 수수료 계산
        long_commission = self.calculate_commission(long_trade_value)
        short_commission = self.calculate_commission(short_trade_value)

        # 총 필요 금액 (롱 비용 + 숏 마진 + 수수료)
        total_cost = long_trade_value + short_trade_value + long_commission + short_commission

        # 자금 확인
        if total_cost > portfolio.cash:
            return False, f"Insufficient funds: need {total_cost:,.0f}, have {portfolio.cash:,.0f}"

        # 페어 포지션 추가
        success = portfolio.add_pair_position(
            pair_id=pair_id,
            long_code=long_code,
            short_code=short_code,
            long_qty=long_qty,
            short_qty=short_qty,
            long_price=long_exec_price,
            short_price=short_exec_price,
            date=date,
            hedge_ratio=hedge_ratio
        )

        if not success:
            return False, "Failed to add pair position"

        # 수수료 차감
        portfolio.cash -= (long_commission + short_commission)

        return True, None

    def close_pair_trade(
        self,
        portfolio: Portfolio,
        pair_id: str,
        long_price: float,
        short_price: float,
        date: datetime
    ) -> Tuple[bool, Optional[str], Optional[dict]]:
        """
        페어 트레이드 청산

        Args:
            portfolio: 포트폴리오
            pair_id: 페어 ID
            long_price: 롱 청산 가격
            short_price: 숏 청산 가격
            date: 거래 일시

        Returns:
            (성공 여부, 에러 메시지, 거래 정보)
        """
        if pair_id not in portfolio.pair_positions:
            return False, f"Pair position not found: {pair_id}", None

        pair = portfolio.pair_positions[pair_id]

        # 실행 가격 계산 (청산은 매수/매도가 반대)
        long_exec_price = self.calculate_execution_price(
            long_price, pair.long_position.quantity, is_buy=False
        )
        short_exec_price = self.calculate_execution_price(
            short_price, abs(pair.short_position.quantity), is_buy=True
        )

        # 수수료 계산
        long_commission = self.calculate_commission(pair.long_position.quantity * long_exec_price)
        short_commission = self.calculate_commission(abs(pair.short_position.quantity) * short_exec_price)

        # 포지션 청산
        trade = portfolio.close_pair_position(pair_id, long_exec_price, short_exec_price, date)

        if trade is None:
            return False, "Failed to close pair position", None

        # 수수료 차감
        portfolio.cash -= (long_commission + short_commission)

        # 거래 정보에 수수료 추가
        trade["commission"] = long_commission + short_commission

        return True, None, trade

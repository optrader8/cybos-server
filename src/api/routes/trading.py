"""
Trading Router - 알고리즘 트레이딩 API

백테스트, 포트폴리오 관리, 성과 분석 API 엔드포인트를 제공합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
import os

from ..schemas.trading import (
    BacktestRequest,
    BacktestResponse,
    BacktestResult,
    PortfolioResponse,
    PortfolioPair,
    PortfolioPosition,
    TradeExecutionRequest,
    TradeExecutionResponse,
    PerformanceResponse,
    PerformanceMetrics
)
from ...database.connection import get_connection_context
from ...database.models.pair import PairTable
from ...database.models.signal import SignalTable

router = APIRouter(prefix="/api/trading", tags=["trading"])


@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    백테스트 실행

    페어 트레이딩 전략을 과거 데이터로 백테스트합니다.
    """
    from ...services.backtest_engine import BacktestEngine, BacktestConfig
    from ...database.models.price import PriceTable
    from ...database.models.signal import SignalTable
    from datetime import datetime

    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            # 백테스트 설정
            config = BacktestConfig(
                initial_capital=request.initial_capital,
                start_date=datetime.strptime(request.start_date, "%Y-%m-%d"),
                end_date=datetime.strptime(request.end_date, "%Y-%m-%d"),
                commission_rate=float(os.getenv("BACKTEST_COMMISSION_RATE", "0.0015")),
                slippage_rate=float(os.getenv("BACKTEST_SLIPPAGE_RATE", "0.001")),
                risk_free_rate=float(os.getenv("BACKTEST_RISK_FREE_RATE", "0.03"))
            )

            # 백테스트 엔진 생성
            engine = BacktestEngine(config)

            # 가격 데이터 수집
            price_data = {}
            all_stock_codes = set()

            for pair_id in request.pair_ids:
                pair = PairTable.get_pair(conn, pair_id)
                if pair:
                    all_stock_codes.update(pair.stock_codes)

            # 각 종목의 가격 데이터 조회
            for stock_code in all_stock_codes:
                prices = PriceTable.get_price_history(
                    conn,
                    stock_code,
                    config.start_date.strftime("%Y%m%d"),
                    config.end_date.strftime("%Y%m%d")
                )

                if prices:
                    price_data[stock_code] = {
                        datetime.strptime(p.date, "%Y%m%d"): p.close for p in prices
                    }

            if not price_data:
                raise HTTPException(
                    status_code=404,
                    detail="No price data found for the specified period"
                )

            # 신호 데이터 수집 (해당 기간의 신호)
            signals = []
            for pair_id in request.pair_ids:
                pair_signals = SignalTable.get_signals_by_pair(conn, pair_id)
                for signal in pair_signals:
                    signal_date = datetime.fromisoformat(signal.created_at)
                    if config.start_date <= signal_date <= config.end_date:
                        signals.append({
                            "date": signal_date,
                            "signal_type": signal.signal_type.value,
                            "pair_id": signal.pair_id,
                            "long_code": signal.stock_codes[0] if len(signal.stock_codes) > 0 else None,
                            "short_code": signal.stock_codes[1] if len(signal.stock_codes) > 1 else None,
                            "long_quantity": 100,  # 기본값
                            "short_quantity": 100,
                            "hedge_ratio": signal.hedge_ratios[0] if signal.hedge_ratios else 1.0
                        })

            # 백테스트 실행
            result = engine.run(price_data, signals)

            # 결과 변환
            backtest_results = [
                BacktestResult(
                    pair_id=pair_id,
                    total_return=result.metrics["total_return"],
                    annualized_return=result.metrics["annualized_return"],
                    sharpe_ratio=result.metrics["sharpe_ratio"],
                    sortino_ratio=result.metrics["sortino_ratio"],
                    max_drawdown=result.metrics["max_drawdown"],
                    volatility=result.metrics["volatility"],
                    win_rate=result.metrics["win_rate"],
                    profit_factor=result.metrics["profit_factor"],
                    total_trades=result.metrics["total_trades"]
                )
                for pair_id in request.pair_ids
            ]

            return BacktestResponse(
                success=True,
                message="Backtest completed successfully.",
                results=backtest_results,
                portfolio_return=result.metrics["total_return"],
                portfolio_sharpe=result.metrics["sharpe_ratio"],
                portfolio_max_dd=result.metrics["max_drawdown"]
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio():
    """
    포트폴리오 조회

    현재 포트폴리오 상태를 조회합니다.
    (실제 포트폴리오 관리 시스템이 필요)
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            # 활성 페어 조회
            active_pairs = PairTable.get_active_pairs(conn)

            # 포트폴리오 구성 (Mock 데이터)
            pairs = []
            positions = []
            total_value = 10000000  # Mock 데이터
            cash = 2000000
            invested = 8000000

            return PortfolioResponse(
                total_value=total_value,
                cash=cash,
                invested=invested,
                total_pnl=0.0,
                total_pnl_pct=0.0,
                pairs=pairs,
                positions=positions
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve portfolio: {str(e)}")


@router.post("/execute", response_model=TradeExecutionResponse)
async def execute_trade(request: TradeExecutionRequest):
    """
    거래 실행

    트레이딩 신호를 실제 거래로 실행합니다.
    (Paper Trading 모드 - 실제 주문은 발생하지 않습니다)
    """
    from ...database.models.price import PriceTable
    from ...database.models.signal import SignalStatus

    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            # 신호 조회
            signal = SignalTable.get_signal(conn, request.signal_id)
            if signal is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Signal not found: {request.signal_id}"
                )

            # 신호 상태 확인
            if signal.status != SignalStatus.ACTIVE:
                raise HTTPException(
                    status_code=400,
                    detail=f"Signal is not active: {signal.status.value}"
                )

            # 현재 가격 조회
            executed_prices = {}
            for stock_code in signal.stock_codes:
                price = PriceTable.get_latest_price(conn, stock_code)
                if price:
                    executed_prices[stock_code] = float(price.close)
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No price data for stock: {stock_code}"
                    )

            # 거래 수량 (신호에서 제안된 수량 또는 기본값)
            executed_quantities = {
                stock_code: request.quantity or 100
                for stock_code in signal.stock_codes
            }

            # 총 비용 계산
            total_cost = sum(
                executed_prices[code] * executed_quantities[code]
                for code in signal.stock_codes
            )

            # 신호 상태 업데이트
            SignalTable.update_signal_status(
                conn,
                request.signal_id,
                SignalStatus.EXECUTED
            )

            # 실행 가격 업데이트
            SignalTable.update_signal(
                conn,
                request.signal_id,
                {"exit_prices": executed_prices}
            )

            conn.commit()

            # Trading 모드 확인
            trading_mode = os.getenv("TRADING_MODE", "paper")

            return TradeExecutionResponse(
                success=True,
                message=f"Trade executed successfully in {trading_mode} mode.",
                signal_id=request.signal_id,
                executed_prices=executed_prices,
                executed_quantities=executed_quantities,
                total_cost=total_cost
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trade execution failed: {str(e)}")


@router.get("/performance", response_model=PerformanceResponse)
async def get_performance():
    """
    성과 분석 조회

    포트폴리오의 성과를 기간별로 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            # 기간별 성과 지표 (Mock 데이터)
            metrics_by_period = [
                PerformanceMetrics(
                    period="1D",
                    total_return=0.5,
                    sharpe_ratio=1.5,
                    max_drawdown=-1.0,
                    win_rate=0.65,
                    profit_factor=2.0,
                    total_trades=3
                ),
                PerformanceMetrics(
                    period="1W",
                    total_return=2.3,
                    sharpe_ratio=1.6,
                    max_drawdown=-2.5,
                    win_rate=0.68,
                    profit_factor=2.1,
                    total_trades=15
                ),
                PerformanceMetrics(
                    period="1M",
                    total_return=8.5,
                    sharpe_ratio=1.7,
                    max_drawdown=-4.2,
                    win_rate=0.70,
                    profit_factor=2.3,
                    total_trades=60
                )
            ]

            # 자본 곡선 (Mock 데이터)
            equity_curve = []

            return PerformanceResponse(
                metrics_by_period=metrics_by_period,
                equity_curve=equity_curve
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve performance: {str(e)}")


@router.get("/signals/active", response_model=dict)
async def get_active_trading_signals():
    """
    활성 트레이딩 신호 조회

    현재 실행 대기 중인 트레이딩 신호를 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            signals = SignalTable.get_active_signals(conn)

            return {
                "total": len(signals),
                "entry_signals": sum(1 for s in signals if s.is_entry_signal()),
                "exit_signals": sum(1 for s in signals if s.is_exit_signal())
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active signals: {str(e)}")


@router.get("/pairs/tradeable", response_model=dict)
async def get_tradeable_pairs():
    """
    거래 가능 페어 조회

    현재 거래 가능한 페어 목록을 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            active_pairs = PairTable.get_active_pairs(conn)

            # 거래 가능한 페어 필터링
            tradeable_pairs = [p for p in active_pairs if p.is_valid_for_trading()]

            return {
                "total_active": len(active_pairs),
                "tradeable": len(tradeable_pairs),
                "pair_ids": [p.pair_id for p in tradeable_pairs[:20]]  # 상위 20개
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tradeable pairs: {str(e)}")


@router.get("/risk/exposure", response_model=dict)
async def get_risk_exposure():
    """
    리스크 노출도 조회

    포트폴리오의 현재 리스크 노출도를 조회합니다.
    """
    from ...database.models.price import PriceTable
    import numpy as np

    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            # 활성 신호 조회
            active_signals = SignalTable.get_active_signals(conn)

            # 총 노출도 계산
            total_exposure = 0.0
            pair_exposures = {}

            for signal in active_signals:
                if signal.current_prices:
                    # 각 페어의 노출도 계산
                    pair_exposure = sum(
                        signal.current_prices.get(code, 0) * 100  # 기본 수량 100
                        for code in signal.stock_codes
                    )
                    total_exposure += pair_exposure
                    pair_exposures[signal.pair_id] = pair_exposure

            # 최대 페어 노출도
            max_pair_exposure = max(pair_exposures.values()) if pair_exposures else 0.0

            # 마진 사용률 (총 자본 대비)
            initial_capital = float(os.getenv("BACKTEST_INITIAL_CAPITAL", "100000000"))
            margin_usage = total_exposure / initial_capital if initial_capital > 0 else 0.0

            # VaR 계산 (간단한 Historical VaR)
            var_confidence = float(os.getenv("RISK_VAR_CONFIDENCE", "0.95"))

            # 최근 수익률 수집 (간단히 시뮬레이션)
            returns = []
            for signal in active_signals:
                if signal.current_prices and signal.entry_prices:
                    for code in signal.stock_codes:
                        entry = signal.entry_prices.get(code, 0)
                        current = signal.current_prices.get(code, 0)
                        if entry > 0:
                            ret = (current - entry) / entry
                            returns.append(ret)

            # VaR 계산
            if returns:
                returns_array = np.array(returns)
                var_percentile = (1 - var_confidence) * 100
                var_return = np.percentile(returns_array, var_percentile)
                var_95 = abs(var_return * total_exposure)
            else:
                var_95 = 0.0

            # 리스크 레벨 판단
            max_exposure_pct = float(os.getenv("RISK_MAX_PORTFOLIO_EXPOSURE", "0.8"))

            if margin_usage < 0.3:
                risk_level = "LOW"
            elif margin_usage < 0.6:
                risk_level = "MEDIUM"
            elif margin_usage < max_exposure_pct:
                risk_level = "HIGH"
            else:
                risk_level = "CRITICAL"

            return {
                "total_exposure": total_exposure,
                "max_pair_exposure": max_pair_exposure,
                "margin_usage": margin_usage,
                "var_95": var_95,
                "risk_level": risk_level,
                "active_signals": len(active_signals),
                "max_allowed_exposure_pct": max_exposure_pct
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate risk exposure: {str(e)}")

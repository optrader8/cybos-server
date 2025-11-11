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
    (실제 백테스트 엔진은 백그라운드 서비스에서 구현 필요)
    """
    # TODO: 실제 백테스트 로직 구현
    # 현재는 Mock 응답 반환

    # 실제 백테스트 로직이 구현되면 아래 코드로 대체
    # from services.backtest_engine import run_backtest
    # results = run_backtest(request)

    return BacktestResponse(
        success=True,
        message="Backtest request received. Analysis will be performed in background.",
        results=[],
        portfolio_return=0.0,
        portfolio_sharpe=0.0,
        portfolio_max_dd=0.0
    )


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
    (실제 거래 실행 시스템이 필요)
    """
    # TODO: 실제 거래 실행 로직 구현
    # 현재는 Mock 응답 반환

    return TradeExecutionResponse(
        success=True,
        message="Trade execution request received. Will be processed in background.",
        signal_id=request.signal_id,
        executed_prices={},
        executed_quantities={},
        total_cost=0.0
    )


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
    # TODO: 실제 리스크 관리 시스템 구현
    # 현재는 Mock 응답 반환

    return {
        "total_exposure": 8000000,
        "max_pair_exposure": 2000000,
        "margin_usage": 0.4,
        "var_95": 350000,  # Value at Risk (95%)
        "risk_level": "MEDIUM"
    }

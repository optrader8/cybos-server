"""
Trading Schema - 알고리즘 트레이딩 스키마

백테스트, 포트폴리오 관리 등 알고리즘 트레이딩 관련 스키마를 정의합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    """백테스트 요청"""
    pair_ids: List[str] = Field(..., description="백테스트할 페어 ID 리스트")
    start_date: str = Field(..., description="시작일 (YYYYMMDD)")
    end_date: str = Field(..., description="종료일 (YYYYMMDD)")
    initial_capital: float = Field(10000000, description="초기 자본금")

    # 신호 생성 파라미터
    entry_z_score: float = Field(2.0, description="진입 Z-score 임계값")
    exit_z_score: float = Field(0.5, description="청산 Z-score 임계값")
    stop_loss_pct: float = Field(0.05, description="손절 비율")
    take_profit_pct: float = Field(0.10, description="익절 비율")

    # 포지션 관리
    max_position_size: float = Field(0.2, description="최대 포지션 크기 (자본 대비)")
    rebalance_interval: int = Field(5, description="리밸런싱 간격 (일)")

    class Config:
        json_schema_extra = {
            "example": {
                "pair_ids": ["005930_000660", "005380_051910"],
                "start_date": "20230101",
                "end_date": "20231231",
                "initial_capital": 10000000,
                "entry_z_score": 2.0,
                "exit_z_score": 0.5,
                "stop_loss_pct": 0.05
            }
        }


class BacktestResult(BaseModel):
    """백테스트 결과"""
    pair_id: str = Field(..., description="페어 ID")

    # 수익 지표
    total_return: float = Field(..., description="총 수익률 (%)")
    annual_return: float = Field(..., description="연간 수익률 (%)")
    sharpe_ratio: float = Field(..., description="샤프 비율")
    sortino_ratio: float = Field(..., description="소르티노 비율")

    # 위험 지표
    max_drawdown: float = Field(..., description="최대 낙폭 (%)")
    volatility: float = Field(..., description="변동성 (%)")

    # 거래 통계
    total_trades: int = Field(..., description="총 거래 횟수")
    win_rate: float = Field(..., description="승률")
    profit_factor: float = Field(..., description="수익 팩터")
    avg_win: float = Field(..., description="평균 수익")
    avg_loss: float = Field(..., description="평균 손실")

    # 자본
    final_capital: float = Field(..., description="최종 자본금")

    class Config:
        json_schema_extra = {
            "example": {
                "pair_id": "005930_000660",
                "total_return": 25.5,
                "annual_return": 12.3,
                "sharpe_ratio": 1.8,
                "max_drawdown": -8.5,
                "total_trades": 45,
                "win_rate": 0.65,
                "profit_factor": 2.1,
                "final_capital": 12550000
            }
        }


class BacktestResponse(BaseModel):
    """백테스트 응답"""
    success: bool = Field(..., description="백테스트 성공 여부")
    message: str = Field(..., description="결과 메시지")
    results: List[BacktestResult] = Field(default_factory=list, description="페어별 백테스트 결과")

    # 전체 포트폴리오 통계
    portfolio_return: float = Field(0.0, description="포트폴리오 총 수익률 (%)")
    portfolio_sharpe: float = Field(0.0, description="포트폴리오 샤프 비율")
    portfolio_max_dd: float = Field(0.0, description="포트폴리오 최대 낙폭 (%)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Backtest completed successfully",
                "results": [],
                "portfolio_return": 22.3,
                "portfolio_sharpe": 1.6,
                "portfolio_max_dd": -10.2
            }
        }


class PortfolioPosition(BaseModel):
    """포트폴리오 포지션"""
    stock_code: str = Field(..., description="종목 코드")
    stock_name: Optional[str] = Field(None, description="종목명")
    quantity: int = Field(..., description="수량 (주)")
    entry_price: float = Field(..., description="진입가")
    current_price: float = Field(..., description="현재가")
    market_value: float = Field(..., description="평가금액")
    unrealized_pnl: float = Field(..., description="미실현 손익")
    unrealized_pnl_pct: float = Field(..., description="미실현 손익률 (%)")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "005930",
                "stock_name": "삼성전자",
                "quantity": 100,
                "entry_price": 74000,
                "current_price": 75000,
                "market_value": 7500000,
                "unrealized_pnl": 100000,
                "unrealized_pnl_pct": 1.35
            }
        }


class PortfolioPair(BaseModel):
    """포트폴리오 페어"""
    pair_id: str = Field(..., description="페어 ID")
    stock_codes: List[str] = Field(..., description="종목 코드 리스트")
    positions: List[PortfolioPosition] = Field(..., description="포지션 목록")
    pair_value: float = Field(..., description="페어 평가금액")
    pair_pnl: float = Field(..., description="페어 손익")
    pair_pnl_pct: float = Field(..., description="페어 손익률 (%)")
    status: str = Field(..., description="상태 (OPEN, CLOSED)")

    class Config:
        json_schema_extra = {
            "example": {
                "pair_id": "005930_000660",
                "stock_codes": ["005930", "000660"],
                "positions": [],
                "pair_value": 10000000,
                "pair_pnl": 250000,
                "pair_pnl_pct": 2.5,
                "status": "OPEN"
            }
        }


class PortfolioResponse(BaseModel):
    """포트폴리오 응답"""
    total_value: float = Field(..., description="총 평가금액")
    cash: float = Field(..., description="현금")
    invested: float = Field(..., description="투자금액")
    total_pnl: float = Field(..., description="총 손익")
    total_pnl_pct: float = Field(..., description="총 수익률 (%)")

    pairs: List[PortfolioPair] = Field(default_factory=list, description="페어 목록")
    positions: List[PortfolioPosition] = Field(default_factory=list, description="전체 포지션")

    class Config:
        json_schema_extra = {
            "example": {
                "total_value": 10250000,
                "cash": 250000,
                "invested": 10000000,
                "total_pnl": 250000,
                "total_pnl_pct": 2.5,
                "pairs": [],
                "positions": []
            }
        }


class TradeExecutionRequest(BaseModel):
    """거래 실행 요청"""
    signal_id: str = Field(..., description="신호 ID")
    execution_type: str = Field(..., description="실행 타입 (MARKET, LIMIT)")
    prices: Optional[Dict[str, float]] = Field(None, description="지정가 (LIMIT인 경우)")

    class Config:
        json_schema_extra = {
            "example": {
                "signal_id": "005930_000660_20240101_120000",
                "execution_type": "MARKET"
            }
        }


class TradeExecutionResponse(BaseModel):
    """거래 실행 응답"""
    success: bool = Field(..., description="실행 성공 여부")
    message: str = Field(..., description="결과 메시지")
    signal_id: str = Field(..., description="신호 ID")
    executed_prices: Dict[str, float] = Field(default_factory=dict, description="실행 가격")
    executed_quantities: Dict[str, int] = Field(default_factory=dict, description="실행 수량")
    total_cost: float = Field(0.0, description="총 비용")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Trade executed successfully",
                "signal_id": "005930_000660_20240101_120000",
                "executed_prices": {"005930": 75100, "000660": 125200},
                "executed_quantities": {"005930": 100, "000660": -50},
                "total_cost": 1255000
            }
        }


class PerformanceMetrics(BaseModel):
    """성과 지표"""
    period: str = Field(..., description="기간 (1D, 1W, 1M, 3M, 6M, 1Y, ALL)")
    total_return: float = Field(..., description="총 수익률 (%)")
    sharpe_ratio: float = Field(..., description="샤프 비율")
    max_drawdown: float = Field(..., description="최대 낙폭 (%)")
    win_rate: float = Field(..., description="승률")
    profit_factor: float = Field(..., description="수익 팩터")
    total_trades: int = Field(..., description="총 거래 횟수")

    class Config:
        json_schema_extra = {
            "example": {
                "period": "1M",
                "total_return": 5.2,
                "sharpe_ratio": 1.8,
                "max_drawdown": -3.5,
                "win_rate": 0.68,
                "profit_factor": 2.3,
                "total_trades": 15
            }
        }


class PerformanceResponse(BaseModel):
    """성과 응답"""
    metrics_by_period: List[PerformanceMetrics] = Field(..., description="기간별 성과 지표")
    equity_curve: List[Dict[str, float]] = Field(default_factory=list, description="자본 곡선")

    class Config:
        json_schema_extra = {
            "example": {
                "metrics_by_period": [],
                "equity_curve": [
                    {"date": "2024-01-01", "value": 10000000},
                    {"date": "2024-01-02", "value": 10050000}
                ]
            }
        }

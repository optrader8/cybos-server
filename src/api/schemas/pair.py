"""
Pair Schema - 페어 트레이딩 페어 스키마

페어 트레이딩 관련 API 요청/응답 스키마를 정의합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class PairBase(BaseModel):
    """페어 기본 정보"""
    pair_id: str = Field(..., description="페어 고유 ID")
    pair_type: str = Field(..., description="페어 타입 (2-WAY, 3-WAY, N-WAY)")
    stock_codes: List[str] = Field(..., description="종목 코드 리스트")


class PairResponse(PairBase):
    """페어 정보 응답"""
    status: str = Field(..., description="페어 상태 (ACTIVE, INACTIVE, MONITORING, SUSPENDED)")
    name: Optional[str] = Field(None, description="페어 이름")
    description: Optional[str] = Field(None, description="설명")

    # 공적분 정보
    cointegration_score: float = Field(0.0, description="공적분 점수 (p-value)")
    half_life: float = Field(0.0, description="반감기 (일)")
    hedge_ratios: List[float] = Field(default_factory=list, description="헤지 비율")

    # 통계 정보
    correlation: float = Field(0.0, description="상관계수")
    spread_mean: float = Field(0.0, description="스프레드 평균")
    spread_std: float = Field(0.0, description="스프레드 표준편차")

    # 성과 정보
    sharpe_ratio: float = Field(0.0, description="샤프 비율")
    max_drawdown: float = Field(0.0, description="최대 낙폭")
    win_rate: float = Field(0.0, description="승률")
    total_trades: int = Field(0, description="총 거래 횟수")

    # 시간 정보
    created_at: Optional[str] = Field(None, description="생성일시")
    updated_at: Optional[str] = Field(None, description="수정일시")
    last_analyzed_at: Optional[str] = Field(None, description="마지막 분석일시")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "pair_id": "005930_000660",
                "pair_type": "2-WAY",
                "stock_codes": ["005930", "000660"],
                "status": "ACTIVE",
                "name": "삼성전자-SK하이닉스 페어",
                "cointegration_score": 0.01,
                "half_life": 15.5,
                "hedge_ratios": [1.0, 0.85],
                "sharpe_ratio": 1.8,
                "win_rate": 0.65,
                "total_trades": 120
            }
        }


class PairListResponse(BaseModel):
    """페어 목록 응답"""
    total: int = Field(..., description="전체 페어 수")
    items: List[PairResponse] = Field(..., description="페어 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "items": [
                    {
                        "pair_id": "005930_000660",
                        "pair_type": "2-WAY",
                        "stock_codes": ["005930", "000660"],
                        "status": "ACTIVE",
                        "sharpe_ratio": 1.8
                    }
                ]
            }
        }


class PairCreateRequest(BaseModel):
    """페어 생성 요청"""
    stock_codes: List[str] = Field(..., min_length=2, description="종목 코드 리스트 (최소 2개)")
    name: Optional[str] = Field(None, description="페어 이름")
    description: Optional[str] = Field(None, description="설명")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_codes": ["005930", "000660"],
                "name": "삼성전자-SK하이닉스 페어",
                "description": "반도체 섹터 페어 트레이딩"
            }
        }


class PairUpdateRequest(BaseModel):
    """페어 업데이트 요청"""
    status: Optional[str] = Field(None, description="상태 변경")
    name: Optional[str] = Field(None, description="이름 변경")
    description: Optional[str] = Field(None, description="설명 변경")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ACTIVE",
                "name": "새 페어 이름"
            }
        }


class PairAnalysisRequest(BaseModel):
    """페어 분석 요청"""
    stock_codes: List[str] = Field(..., min_length=2, description="종목 코드 리스트")
    window_days: int = Field(252, ge=30, le=1000, description="분석 기간 (영업일)")
    method: str = Field("ENGLE_GRANGER", description="공적분 검정 방법")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_codes": ["005930", "000660"],
                "window_days": 252,
                "method": "ENGLE_GRANGER"
            }
        }


class PairAnalysisResponse(BaseModel):
    """페어 분석 응답"""
    success: bool = Field(..., description="분석 성공 여부")
    message: str = Field(..., description="결과 메시지")
    pair_id: str = Field(..., description="페어 ID")
    is_cointegrated: bool = Field(..., description="공적분 관계 존재 여부")
    p_value: float = Field(..., description="p-value")
    hedge_ratios: List[float] = Field(default_factory=list, description="헤지 비율")
    half_life: float = Field(0.0, description="반감기 (일)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Cointegration analysis completed",
                "pair_id": "005930_000660",
                "is_cointegrated": True,
                "p_value": 0.01,
                "hedge_ratios": [1.0, 0.85],
                "half_life": 15.5
            }
        }


class PairStatsResponse(BaseModel):
    """페어 통계 응답"""
    total_pairs: int = Field(..., description="전체 페어 수")
    active_pairs: int = Field(..., description="활성 페어 수")
    pairs_by_type: Dict[str, int] = Field(..., description="타입별 페어 수")
    avg_sharpe_ratio: float = Field(0.0, description="평균 샤프 비율")
    avg_win_rate: float = Field(0.0, description="평균 승률")

    class Config:
        json_schema_extra = {
            "example": {
                "total_pairs": 150,
                "active_pairs": 45,
                "pairs_by_type": {
                    "2-WAY": 120,
                    "3-WAY": 25,
                    "4-WAY": 5
                },
                "avg_sharpe_ratio": 1.2,
                "avg_win_rate": 0.58
            }
        }


class PairPerformanceResponse(BaseModel):
    """페어 성과 응답"""
    pair_id: str = Field(..., description="페어 ID")
    total_trades: int = Field(..., description="총 거래 횟수")
    win_rate: float = Field(..., description="승률")
    profit_factor: float = Field(..., description="수익 팩터")
    sharpe_ratio: float = Field(..., description="샤프 비율")
    max_drawdown: float = Field(..., description="최대 낙폭 (%)")
    avg_return: float = Field(..., description="평균 수익률 (%)")
    total_return: float = Field(..., description="총 수익률 (%)")

    class Config:
        json_schema_extra = {
            "example": {
                "pair_id": "005930_000660",
                "total_trades": 120,
                "win_rate": 0.65,
                "profit_factor": 2.1,
                "sharpe_ratio": 1.8,
                "max_drawdown": -8.5,
                "avg_return": 1.2,
                "total_return": 145.5
            }
        }

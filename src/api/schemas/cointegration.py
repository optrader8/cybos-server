"""
Cointegration Schema - 공적분 분석 스키마

공적분 분석 관련 API 요청/응답 스키마를 정의합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class CointegrationBase(BaseModel):
    """공적분 결과 기본 정보"""
    result_id: str = Field(..., description="결과 ID")
    pair_id: str = Field(..., description="페어 ID")
    stock_codes: List[str] = Field(..., description="종목 코드 리스트")


class CointegrationResponse(CointegrationBase):
    """공적분 결과 응답"""
    # 분석 정보
    method: str = Field(..., description="검정 방법 (ENGLE_GRANGER, JOHANSEN, ADF)")
    test_statistic: float = Field(..., description="검정 통계량")
    p_value: float = Field(..., description="p-value")
    critical_values: Dict[str, float] = Field(default_factory=dict, description="임계값")

    # 공적분 벡터 및 계수
    cointegration_vector: List[float] = Field(default_factory=list, description="공적분 벡터")
    hedge_ratios: List[float] = Field(default_factory=list, description="헤지 비율")
    intercept: float = Field(0.0, description="절편")

    # 잔차 정보
    residuals_mean: float = Field(0.0, description="잔차 평균")
    residuals_std: float = Field(0.0, description="잔차 표준편차")
    half_life: float = Field(0.0, description="반감기 (일)")

    # 추가 통계
    adf_statistic: float = Field(0.0, description="ADF 통계량")
    adf_p_value: float = Field(0.0, description="ADF p-value")

    # 데이터 정보
    sample_size: int = Field(0, description="샘플 크기")
    start_date: Optional[str] = Field(None, description="분석 시작일")
    end_date: Optional[str] = Field(None, description="분석 종료일")

    # 메타데이터
    significance: str = Field(..., description="통계적 유의성 (HIGHLY_SIG, SIGNIFICANT, MARGINAL, NOT_SIG)")
    window_days: int = Field(252, description="분석 기간 (영업일)")
    created_at: Optional[str] = Field(None, description="생성일시")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "result_id": "005930_000660_20240101",
                "pair_id": "005930_000660",
                "stock_codes": ["005930", "000660"],
                "method": "ENGLE_GRANGER",
                "test_statistic": -4.5,
                "p_value": 0.01,
                "critical_values": {"1%": -3.9, "5%": -3.3, "10%": -3.0},
                "hedge_ratios": [1.0, 0.85],
                "half_life": 15.5,
                "significance": "HIGHLY_SIG",
                "sample_size": 252
            }
        }


class CointegrationListResponse(BaseModel):
    """공적분 결과 목록 응답"""
    total: int = Field(..., description="전체 결과 수")
    items: List[CointegrationResponse] = Field(..., description="결과 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 10,
                "items": [
                    {
                        "result_id": "005930_000660_20240101",
                        "pair_id": "005930_000660",
                        "stock_codes": ["005930", "000660"],
                        "p_value": 0.01,
                        "significance": "HIGHLY_SIG"
                    }
                ]
            }
        }


class CointegrationAnalyzeRequest(BaseModel):
    """공적분 분석 요청"""
    stock_codes: List[str] = Field(..., min_length=2, description="종목 코드 리스트 (최소 2개)")
    method: str = Field("ENGLE_GRANGER", description="검정 방법")
    window_days: int = Field(252, ge=30, le=1000, description="분석 기간 (영업일)")
    period_type: str = Field("D", description="기간 타입 (D:일, W:주, M:월)")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_codes": ["005930", "000660"],
                "method": "ENGLE_GRANGER",
                "window_days": 252,
                "period_type": "D"
            }
        }


class CointegrationAnalyzeResponse(BaseModel):
    """공적분 분석 응답"""
    success: bool = Field(..., description="분석 성공 여부")
    message: str = Field(..., description="결과 메시지")
    result: Optional[CointegrationResponse] = Field(None, description="분석 결과")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Cointegration analysis completed successfully",
                "result": {
                    "result_id": "005930_000660_20240101",
                    "pair_id": "005930_000660",
                    "stock_codes": ["005930", "000660"],
                    "p_value": 0.01,
                    "significance": "HIGHLY_SIG"
                }
            }
        }


class CointegrationBatchRequest(BaseModel):
    """공적분 배치 분석 요청"""
    stock_codes_list: List[List[str]] = Field(..., description="종목 코드 리스트의 리스트")
    method: str = Field("ENGLE_GRANGER", description="검정 방법")
    window_days: int = Field(252, ge=30, le=1000, description="분석 기간 (영업일)")
    max_p_value: float = Field(0.05, ge=0.0, le=1.0, description="최대 p-value (유의한 결과만)")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_codes_list": [
                    ["005930", "000660"],
                    ["005380", "051910"],
                    ["035420", "035720"]
                ],
                "method": "ENGLE_GRANGER",
                "window_days": 252,
                "max_p_value": 0.05
            }
        }


class CointegrationBatchResponse(BaseModel):
    """공적분 배치 분석 응답"""
    success: bool = Field(..., description="분석 성공 여부")
    message: str = Field(..., description="결과 메시지")
    total_analyzed: int = Field(..., description="분석한 페어 수")
    significant_pairs: int = Field(..., description="유의한 페어 수")
    results: List[CointegrationResponse] = Field(default_factory=list, description="분석 결과 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Batch cointegration analysis completed",
                "total_analyzed": 100,
                "significant_pairs": 25,
                "results": []
            }
        }


class CointegrationSummaryResponse(BaseModel):
    """공적분 요약 응답"""
    total_results: int = Field(..., description="전체 분석 결과 수")
    highly_significant: int = Field(..., description="매우 유의한 결과 수 (p < 0.01)")
    significant: int = Field(..., description="유의한 결과 수 (p < 0.05)")
    marginal: int = Field(..., description="한계적 유의 결과 수 (p < 0.10)")
    not_significant: int = Field(..., description="유의하지 않은 결과 수")
    avg_p_value: float = Field(0.0, description="평균 p-value")
    avg_half_life: float = Field(0.0, description="평균 반감기 (일)")

    class Config:
        json_schema_extra = {
            "example": {
                "total_results": 150,
                "highly_significant": 30,
                "significant": 45,
                "marginal": 25,
                "not_significant": 50,
                "avg_p_value": 0.08,
                "avg_half_life": 18.5
            }
        }


class CointegrationMonitorRequest(BaseModel):
    """공적분 모니터링 요청"""
    pair_ids: Optional[List[str]] = Field(None, description="모니터링할 페어 ID 리스트")
    recalculate: bool = Field(False, description="재계산 여부")
    window_days: int = Field(252, ge=30, le=1000, description="분석 기간 (영업일)")

    class Config:
        json_schema_extra = {
            "example": {
                "pair_ids": ["005930_000660", "005380_051910"],
                "recalculate": True,
                "window_days": 252
            }
        }


class CointegrationMonitorResponse(BaseModel):
    """공적분 모니터링 응답"""
    success: bool = Field(..., description="모니터링 성공 여부")
    message: str = Field(..., description="결과 메시지")
    monitored_pairs: int = Field(..., description="모니터링한 페어 수")
    deteriorated_pairs: List[str] = Field(default_factory=list, description="공적분 관계가 약화된 페어 ID")
    improved_pairs: List[str] = Field(default_factory=list, description="공적분 관계가 강화된 페어 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Cointegration monitoring completed",
                "monitored_pairs": 50,
                "deteriorated_pairs": ["005930_000660"],
                "improved_pairs": ["005380_051910"]
            }
        }

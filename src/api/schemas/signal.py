"""
Signal Schema - 트레이딩 신호 스키마

트레이딩 신호 관련 API 요청/응답 스키마를 정의합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class SignalBase(BaseModel):
    """신호 기본 정보"""
    signal_id: str = Field(..., description="신호 ID")
    pair_id: str = Field(..., description="페어 ID")
    stock_codes: List[str] = Field(..., description="종목 코드 리스트")
    signal_type: str = Field(..., description="신호 타입 (ENTRY_LONG, ENTRY_SHORT, EXIT_LONG, EXIT_SHORT, STOP_LOSS, TAKE_PROFIT)")


class SignalResponse(SignalBase):
    """신호 정보 응답"""
    status: str = Field(..., description="신호 상태 (ACTIVE, EXECUTED, CANCELLED, EXPIRED)")

    # 가격 정보
    current_prices: Dict[str, float] = Field(default_factory=dict, description="현재가")
    entry_prices: Dict[str, float] = Field(default_factory=dict, description="진입가")
    target_prices: Dict[str, float] = Field(default_factory=dict, description="목표가")
    stop_prices: Dict[str, float] = Field(default_factory=dict, description="손절가")

    # 스프레드 정보
    spread: float = Field(0.0, description="현재 스프레드")
    spread_mean: float = Field(0.0, description="스프레드 평균")
    spread_std: float = Field(0.0, description="스프레드 표준편차")
    z_score: float = Field(0.0, description="Z-score")

    # 포지션 정보
    position_sizes: Dict[str, int] = Field(default_factory=dict, description="포지션 크기 (주)")
    hedge_ratios: List[float] = Field(default_factory=list, description="헤지 비율")

    # 메타데이터
    confidence: float = Field(0.0, description="신호 신뢰도 (0-1)")
    expected_return: float = Field(0.0, description="기대 수익률 (%)")
    risk_level: int = Field(1, ge=1, le=5, description="위험도 (1-5)")
    notes: str = Field("", description="메모")

    # 시간 정보
    created_at: Optional[str] = Field(None, description="생성일시")
    executed_at: Optional[str] = Field(None, description="실행일시")
    expired_at: Optional[str] = Field(None, description="만료일시")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "signal_id": "005930_000660_20240101_120000",
                "pair_id": "005930_000660",
                "stock_codes": ["005930", "000660"],
                "signal_type": "ENTRY_LONG",
                "status": "ACTIVE",
                "current_prices": {"005930": 75000, "000660": 125000},
                "z_score": -2.5,
                "confidence": 0.85,
                "expected_return": 3.5,
                "risk_level": 2
            }
        }


class SignalListResponse(BaseModel):
    """신호 목록 응답"""
    total: int = Field(..., description="전체 신호 수")
    items: List[SignalResponse] = Field(..., description="신호 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 5,
                "items": [
                    {
                        "signal_id": "005930_000660_20240101_120000",
                        "pair_id": "005930_000660",
                        "stock_codes": ["005930", "000660"],
                        "signal_type": "ENTRY_LONG",
                        "status": "ACTIVE",
                        "z_score": -2.5
                    }
                ]
            }
        }


class SignalCreateRequest(BaseModel):
    """신호 생성 요청"""
    pair_id: str = Field(..., description="페어 ID")
    signal_type: str = Field(..., description="신호 타입")
    current_prices: Dict[str, float] = Field(..., description="현재가")
    z_score: Optional[float] = Field(None, description="Z-score")
    confidence: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="신호 신뢰도")
    notes: Optional[str] = Field("", description="메모")

    class Config:
        json_schema_extra = {
            "example": {
                "pair_id": "005930_000660",
                "signal_type": "ENTRY_LONG",
                "current_prices": {"005930": 75000, "000660": 125000},
                "z_score": -2.5,
                "confidence": 0.85,
                "notes": "강한 진입 신호"
            }
        }


class SignalUpdateRequest(BaseModel):
    """신호 업데이트 요청"""
    status: str = Field(..., description="신호 상태 (EXECUTED, CANCELLED, EXPIRED)")
    notes: Optional[str] = Field(None, description="메모")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "EXECUTED",
                "notes": "신호 실행 완료"
            }
        }


class SignalExecuteRequest(BaseModel):
    """신호 실행 요청"""
    signal_id: str = Field(..., description="신호 ID")
    execution_prices: Dict[str, float] = Field(..., description="실행 가격")
    position_sizes: Dict[str, int] = Field(..., description="포지션 크기 (주)")

    class Config:
        json_schema_extra = {
            "example": {
                "signal_id": "005930_000660_20240101_120000",
                "execution_prices": {"005930": 75100, "000660": 125200},
                "position_sizes": {"005930": 100, "000660": -50}
            }
        }


class SignalExecuteResponse(BaseModel):
    """신호 실행 응답"""
    success: bool = Field(..., description="실행 성공 여부")
    message: str = Field(..., description="결과 메시지")
    signal_id: str = Field(..., description="신호 ID")
    executed_at: str = Field(..., description="실행 시각")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Signal executed successfully",
                "signal_id": "005930_000660_20240101_120000",
                "executed_at": "2024-01-01T12:00:00"
            }
        }


class SignalStatsResponse(BaseModel):
    """신호 통계 응답"""
    total_signals: int = Field(..., description="전체 신호 수")
    active_signals: int = Field(..., description="활성 신호 수")
    executed_signals: int = Field(..., description="실행된 신호 수")
    signals_by_type: Dict[str, int] = Field(..., description="타입별 신호 수")
    avg_confidence: float = Field(0.0, description="평균 신뢰도")
    avg_expected_return: float = Field(0.0, description="평균 기대 수익률")

    class Config:
        json_schema_extra = {
            "example": {
                "total_signals": 250,
                "active_signals": 15,
                "executed_signals": 200,
                "signals_by_type": {
                    "ENTRY_LONG": 80,
                    "ENTRY_SHORT": 75,
                    "EXIT_LONG": 70,
                    "EXIT_SHORT": 25
                },
                "avg_confidence": 0.72,
                "avg_expected_return": 2.8
            }
        }


class SignalScanRequest(BaseModel):
    """신호 스캔 요청"""
    pair_ids: Optional[List[str]] = Field(None, description="스캔할 페어 ID 리스트 (None이면 전체)")
    min_z_score: float = Field(2.0, description="최소 Z-score 절대값")
    min_confidence: float = Field(0.7, ge=0.0, le=1.0, description="최소 신뢰도")
    signal_types: Optional[List[str]] = Field(None, description="신호 타입 필터")

    class Config:
        json_schema_extra = {
            "example": {
                "pair_ids": ["005930_000660", "005380_051910"],
                "min_z_score": 2.0,
                "min_confidence": 0.7,
                "signal_types": ["ENTRY_LONG", "ENTRY_SHORT"]
            }
        }


class SignalScanResponse(BaseModel):
    """신호 스캔 응답"""
    success: bool = Field(..., description="스캔 성공 여부")
    message: str = Field(..., description="결과 메시지")
    total_scanned: int = Field(..., description="스캔한 페어 수")
    signals_found: int = Field(..., description="발견된 신호 수")
    signals: List[SignalResponse] = Field(default_factory=list, description="신호 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Signal scan completed",
                "total_scanned": 50,
                "signals_found": 5,
                "signals": []
            }
        }

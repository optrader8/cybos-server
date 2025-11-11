"""
Price Schema - 시세 정보 스키마

시세 정보 관련 API 요청/응답 스키마를 정의합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class PriceBase(BaseModel):
    """시세 기본 정보"""
    code: str = Field(..., description="종목 코드")
    current_price: int = Field(..., description="현재가")
    change: int = Field(..., description="전일 대비")
    status: int = Field(..., description="상태 구분 (2:상승, 3:보합, 5:하락)")


class PriceResponse(PriceBase):
    """시세 정보 응답"""
    name: str = Field(..., description="종목명")
    time: str = Field(..., description="시각 (HHMM)")
    open_price: int = Field(..., description="시가")
    high_price: int = Field(..., description="고가")
    low_price: int = Field(..., description="저가")
    prev_close: int = Field(..., description="전일 종가")
    ask_price: int = Field(..., description="매도 호가")
    bid_price: int = Field(..., description="매수 호가")
    volume: int = Field(..., description="거래량")
    amount: Optional[int] = Field(None, description="거래대금")
    change_rate: Optional[float] = Field(None, description="등락률 (%)")
    created_at: Optional[str] = Field(None, description="생성 시각")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "code": "005930",
                "name": "삼성전자",
                "time": "1430",
                "current_price": 75000,
                "change": 1000,
                "status": 2,
                "open_price": 74500,
                "high_price": 75500,
                "low_price": 74000,
                "prev_close": 74000,
                "ask_price": 75100,
                "bid_price": 74900,
                "volume": 12345678,
                "amount": 920000000000,
                "change_rate": 1.35,
                "created_at": "2024-01-01T14:30:00"
            }
        }


class PriceListResponse(BaseModel):
    """시세 목록 응답"""
    total: int = Field(..., description="전체 시세 수")
    items: List[PriceResponse] = Field(..., description="시세 목록")
    timestamp: str = Field(..., description="조회 시각")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "items": [
                    {
                        "code": "005930",
                        "name": "삼성전자",
                        "current_price": 75000,
                        "change": 1000,
                        "status": 2
                    }
                ],
                "timestamp": "2024-01-01T14:30:00"
            }
        }


class HistoricalPriceBase(BaseModel):
    """과거 시세 기본 정보"""
    code: str = Field(..., description="종목 코드")
    date: str = Field(..., description="날짜 (YYYYMMDD)")
    open_price: int = Field(..., description="시가")
    high_price: int = Field(..., description="고가")
    low_price: int = Field(..., description="저가")
    close_price: int = Field(..., description="종가")
    volume: int = Field(..., description="거래량")


class HistoricalPriceResponse(HistoricalPriceBase):
    """과거 시세 응답"""
    change: Optional[int] = Field(None, description="전일 대비")
    amount: Optional[int] = Field(None, description="거래대금")
    change_rate: Optional[float] = Field(None, description="등락률 (%)")
    period_type: Optional[str] = Field(None, description="기간 타입 (D/W/M)")
    created_at: Optional[str] = Field(None, description="생성 시각")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "code": "005930",
                "date": "20240101",
                "open_price": 74000,
                "high_price": 75500,
                "low_price": 73500,
                "close_price": 75000,
                "volume": 20000000,
                "change": 1000,
                "amount": 1500000000000,
                "change_rate": 1.35,
                "period_type": "D",
                "created_at": "2024-01-01T15:30:00"
            }
        }


class HistoricalPriceListResponse(BaseModel):
    """과거 시세 목록 응답"""
    code: str = Field(..., description="종목 코드")
    name: Optional[str] = Field(None, description="종목명")
    period_type: str = Field(..., description="기간 타입 (D:일, W:주, M:월)")
    total: int = Field(..., description="전체 데이터 수")
    items: List[HistoricalPriceResponse] = Field(..., description="과거 시세 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "005930",
                "name": "삼성전자",
                "period_type": "D",
                "total": 100,
                "items": [
                    {
                        "code": "005930",
                        "date": "20240101",
                        "open_price": 74000,
                        "high_price": 75500,
                        "low_price": 73500,
                        "close_price": 75000,
                        "volume": 20000000
                    }
                ]
            }
        }


class PriceUpdateRequest(BaseModel):
    """시세 업데이트 요청"""
    codes: Optional[List[str]] = Field(
        None,
        description="업데이트할 종목 코드 목록 (None이면 전체)"
    )
    market_kinds: Optional[List[int]] = Field(
        default=[1, 2],
        description="시장 구분 (1:KOSPI, 2:KOSDAQ)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "codes": ["005930", "000660"],
                "market_kinds": [1]
            }
        }


class PriceUpdateResponse(BaseModel):
    """시세 업데이트 응답"""
    success: bool = Field(..., description="업데이트 성공 여부")
    message: str = Field(..., description="결과 메시지")
    total_updated: int = Field(..., description="업데이트된 종목 수")
    failed_count: int = Field(..., description="실패한 종목 수")
    elapsed_time: float = Field(..., description="소요 시간 (초)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Price update completed",
                "total_updated": 2800,
                "failed_count": 0,
                "elapsed_time": 120.5
            }
        }

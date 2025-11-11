"""
Stock Schema - 주식 정보 스키마

주식 정보 관련 API 요청/응답 스키마를 정의합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class StockBase(BaseModel):
    """주식 기본 정보"""
    code: str = Field(..., description="종목 코드 (6자리)")
    name: str = Field(..., description="종목명")
    market_kind: int = Field(..., description="시장 구분 (1:KOSPI, 2:KOSDAQ)")


class StockResponse(StockBase):
    """주식 정보 응답"""
    control_kind: Optional[int] = Field(None, description="관리 구분")
    supervise_kind: Optional[int] = Field(None, description="감리 구분")
    stock_kind: Optional[int] = Field(None, description="주식 종류")
    listing_date: Optional[str] = Field(None, description="상장일")
    capital: Optional[int] = Field(None, description="자본금")
    credit_able: Optional[int] = Field(None, description="신용 거래 가능 여부")
    created_at: Optional[str] = Field(None, description="생성 시각")
    updated_at: Optional[str] = Field(None, description="수정 시각")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "code": "005930",
                "name": "삼성전자",
                "market_kind": 1,
                "control_kind": 0,
                "supervise_kind": 0,
                "stock_kind": 1,
                "listing_date": "19750613",
                "capital": 8970000000000,
                "credit_able": 1,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }


class StockListResponse(BaseModel):
    """주식 목록 응답"""
    total: int = Field(..., description="전체 종목 수")
    items: List[StockResponse] = Field(..., description="종목 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "items": [
                    {
                        "code": "005930",
                        "name": "삼성전자",
                        "market_kind": 1
                    },
                    {
                        "code": "000660",
                        "name": "SK하이닉스",
                        "market_kind": 1
                    }
                ]
            }
        }


class StockSyncRequest(BaseModel):
    """주식 정보 동기화 요청"""
    market_kinds: Optional[List[int]] = Field(
        default=[1, 2],
        description="동기화할 시장 구분 목록 (1:KOSPI, 2:KOSDAQ)"
    )
    force: bool = Field(
        default=False,
        description="강제 동기화 여부"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "market_kinds": [1, 2],
                "force": False
            }
        }


class StockSyncResponse(BaseModel):
    """주식 정보 동기화 응답"""
    success: bool = Field(..., description="동기화 성공 여부")
    message: str = Field(..., description="결과 메시지")
    total_synced: int = Field(..., description="동기화된 종목 수")
    elapsed_time: float = Field(..., description="소요 시간 (초)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Stock sync completed successfully",
                "total_synced": 3000,
                "elapsed_time": 45.2
            }
        }


class MarketStatusResponse(BaseModel):
    """시장 상태 응답"""
    is_connected: bool = Field(..., description="Cybos Plus 연결 상태")
    server_time: Optional[str] = Field(None, description="서버 시각")
    market_open: bool = Field(..., description="시장 개장 여부")
    total_stocks: int = Field(..., description="전체 종목 수")
    kospi_count: int = Field(..., description="KOSPI 종목 수")
    kosdaq_count: int = Field(..., description="KOSDAQ 종목 수")

    class Config:
        json_schema_extra = {
            "example": {
                "is_connected": True,
                "server_time": "2024-01-01T14:30:00",
                "market_open": True,
                "total_stocks": 3000,
                "kospi_count": 800,
                "kosdaq_count": 1500
            }
        }

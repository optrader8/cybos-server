"""
Stocks Router - 주식 정보 API

주식 종목 정보를 조회하고 관리하는 API 엔드포인트를 제공합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import os
import time
from datetime import datetime

from ..schemas.stock import (
    StockResponse,
    StockListResponse,
    StockSyncRequest,
    StockSyncResponse,
    MarketStatusResponse
)
from ...database.connection import get_connection_context
from ...database.models.stock import StockTable, MarketKind, StockInfo
from ...cybos.codes.fetcher import get_stock_code_fetcher
from ...cybos.connection.validator import validate_connection

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


def _stock_info_to_response(stock: StockInfo) -> StockResponse:
    """StockInfo를 StockResponse로 변환"""
    return StockResponse(
        code=stock.code,
        name=stock.name,
        market_kind=stock.market_kind,
        control_kind=stock.control_kind,
        supervise_kind=stock.supervise_kind,
        stock_kind=stock.stock_kind,
        listing_date=stock.listing_date,
        capital=stock.capital,
        credit_able=stock.credit_able,
        created_at=stock.created_at,
        updated_at=stock.updated_at
    )


@router.get("/", response_model=StockListResponse)
async def get_stocks(
    market_kind: Optional[int] = Query(None, description="시장 구분 (1:KOSPI, 2:KOSDAQ)"),
    limit: int = Query(100, ge=1, le=5000, description="조회할 종목 수"),
    offset: int = Query(0, ge=0, description="조회 시작 위치")
):
    """
    주식 목록 조회

    전체 주식 종목 목록을 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            if market_kind is not None:
                # 특정 시장의 종목만 조회
                stocks = StockTable.get_stocks_by_market(conn, market_kind)
            else:
                # 전체 종목 조회
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT code, name, market_kind, control_kind, supervise_kind,
                           stock_kind, listing_date, capital, credit_able,
                           created_at, updated_at
                    FROM stocks
                    ORDER BY code
                    LIMIT ? OFFSET ?
                """, (limit, offset))

                rows = cursor.fetchall()
                stocks = [
                    StockInfo(
                        code=row[0], name=row[1], market_kind=row[2],
                        control_kind=row[3], supervise_kind=row[4],
                        stock_kind=row[5], listing_date=row[6],
                        capital=row[7], credit_able=row[8],
                        created_at=row[9], updated_at=row[10]
                    )
                    for row in rows
                ]

            # 전체 개수 조회
            cursor = conn.cursor()
            if market_kind is not None:
                cursor.execute("SELECT COUNT(*) FROM stocks WHERE market_kind = ?", (market_kind,))
            else:
                cursor.execute("SELECT COUNT(*) FROM stocks")

            total = cursor.fetchone()[0]

            # 응답 생성
            items = [_stock_info_to_response(stock) for stock in stocks[offset:offset + limit]]

            return StockListResponse(total=total, items=items)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stocks: {str(e)}")


@router.get("/{code}", response_model=StockResponse)
async def get_stock(code: str):
    """
    특정 주식 정보 조회

    종목 코드로 주식 정보를 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            stock = StockTable.get_stock(conn, code)

            if stock is None:
                raise HTTPException(status_code=404, detail=f"Stock not found: {code}")

            return _stock_info_to_response(stock)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stock: {str(e)}")


@router.post("/sync", response_model=StockSyncResponse)
async def sync_stocks(request: StockSyncRequest = StockSyncRequest()):
    """
    주식 정보 동기화

    Cybos Plus에서 최신 종목 정보를 가져와 데이터베이스에 저장합니다.
    """
    # Cybos Plus 연결 확인
    validation_result = validate_connection()
    if not validation_result["is_connected"]:
        raise HTTPException(status_code=503, detail="Cybos Plus not connected")

    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")
    start_time = time.time()

    try:
        fetcher = get_stock_code_fetcher()
        total_synced = 0

        with get_connection_context(db_path) as conn:
            for market_kind in request.market_kinds:
                # Cybos Plus에서 종목 정보 조회
                stocks = fetcher.fetch_all_stocks(market_kind)

                # 데이터베이스에 저장
                for stock in stocks:
                    if request.force:
                        # 기존 데이터 삭제 후 삽입
                        StockTable.delete_stock(conn, stock.code)

                    StockTable.insert_or_update_stock(conn, stock)
                    total_synced += 1

            conn.commit()

        elapsed_time = time.time() - start_time

        return StockSyncResponse(
            success=True,
            message=f"Successfully synced {total_synced} stocks",
            total_synced=total_synced,
            elapsed_time=elapsed_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stock sync failed: {str(e)}")


@router.get("/status/market", response_model=MarketStatusResponse)
async def get_market_status():
    """
    시장 상태 조회

    Cybos Plus 연결 상태와 시장 정보를 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        # Cybos Plus 연결 상태
        validation_result = validate_connection()

        # 데이터베이스 통계
        with get_connection_context(db_path) as conn:
            kospi_stocks = StockTable.get_stocks_by_market(conn, MarketKind.KOSPI)
            kosdaq_stocks = StockTable.get_stocks_by_market(conn, MarketKind.KOSDAQ)

        # 시장 개장 여부 확인 (09:00 ~ 15:30)
        now = datetime.now()
        market_open_time = now.replace(hour=9, minute=0, second=0)
        market_close_time = now.replace(hour=15, minute=30, second=0)
        market_open = market_open_time <= now <= market_close_time

        return MarketStatusResponse(
            is_connected=validation_result["is_connected"],
            server_time=now.isoformat(),
            market_open=market_open,
            total_stocks=len(kospi_stocks) + len(kosdaq_stocks),
            kospi_count=len(kospi_stocks),
            kosdaq_count=len(kosdaq_stocks)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market status: {str(e)}")

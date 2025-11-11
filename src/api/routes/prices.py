"""
Prices Router - 시세 정보 API

시세 데이터를 조회하고 업데이트하는 API 엔드포인트를 제공합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from typing import List, Optional
import os
import time
from datetime import datetime
import asyncio

from ..schemas.price import (
    PriceResponse,
    PriceListResponse,
    HistoricalPriceResponse,
    HistoricalPriceListResponse,
    PriceUpdateRequest,
    PriceUpdateResponse
)
from ...database.connection import get_connection_context
from ...database.models.price import PriceTable, PriceInfo
from ...database.models.history import HistoricalPriceTable
from ...database.models.stock import StockTable
from ...cybos.price.fetcher import get_price_fetcher
from ...cybos.connection.validator import validate_connection

router = APIRouter(prefix="/api/prices", tags=["prices"])


def _price_info_to_response(price: PriceInfo, stock_name: str = None) -> PriceResponse:
    """PriceInfo를 PriceResponse로 변환"""
    change_rate = None
    if price.prev_close and price.prev_close > 0:
        change_rate = (price.change / price.prev_close) * 100

    return PriceResponse(
        code=price.code,
        name=stock_name or price.name or "",
        time=price.time,
        current_price=price.current_price,
        change=price.change,
        status=price.status,
        open_price=price.open_price,
        high_price=price.high_price,
        low_price=price.low_price,
        prev_close=price.prev_close,
        ask_price=price.ask_price,
        bid_price=price.bid_price,
        volume=price.volume,
        amount=price.amount,
        change_rate=change_rate,
        created_at=price.created_at
    )


@router.get("/{code}", response_model=PriceResponse)
async def get_price(code: str, fetch_new: bool = Query(False, description="실시간 조회 여부")):
    """
    특정 종목 시세 조회

    종목 코드로 시세 정보를 조회합니다.
    fetch_new=true이면 Cybos Plus에서 실시간 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        if fetch_new:
            # Cybos Plus 연결 확인
            validation_result = validate_connection()
            if not validation_result["is_connected"]:
                raise HTTPException(status_code=503, detail="Cybos Plus not connected")

            # 실시간 시세 조회
            fetcher = get_price_fetcher()
            price = fetcher.fetch_single_price(code)

            if price is None:
                raise HTTPException(status_code=404, detail=f"Failed to fetch price for {code}")

            # 데이터베이스에 저장
            with get_connection_context(db_path) as conn:
                PriceTable.insert_price(conn, price)
                conn.commit()

            return _price_info_to_response(price)
        else:
            # 데이터베이스에서 조회
            with get_connection_context(db_path) as conn:
                price = PriceTable.get_latest_price(conn, code)

                if price is None:
                    raise HTTPException(status_code=404, detail=f"Price not found for {code}")

                # 종목명 조회
                stock = StockTable.get_stock(conn, code)
                stock_name = stock.name if stock else None

                return _price_info_to_response(price, stock_name)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve price: {str(e)}")


@router.get("/", response_model=PriceListResponse)
async def get_prices(
    codes: Optional[str] = Query(None, description="종목 코드 (쉼표로 구분)"),
    limit: int = Query(100, ge=1, le=500, description="조회할 시세 수")
):
    """
    시세 목록 조회

    여러 종목의 시세를 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            if codes:
                # 특정 종목들의 시세 조회
                code_list = [c.strip() for c in codes.split(",")]
                prices = []

                for code in code_list[:limit]:
                    price = PriceTable.get_latest_price(conn, code)
                    if price:
                        stock = StockTable.get_stock(conn, code)
                        stock_name = stock.name if stock else None
                        prices.append(_price_info_to_response(price, stock_name))
            else:
                # 최근 시세 조회
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT code
                    FROM prices
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))

                unique_codes = [row[0] for row in cursor.fetchall()]
                prices = []

                for code in unique_codes:
                    price = PriceTable.get_latest_price(conn, code)
                    if price:
                        stock = StockTable.get_stock(conn, code)
                        stock_name = stock.name if stock else None
                        prices.append(_price_info_to_response(price, stock_name))

            return PriceListResponse(
                total=len(prices),
                items=prices,
                timestamp=datetime.now().isoformat()
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve prices: {str(e)}")


@router.get("/{code}/history", response_model=HistoricalPriceListResponse)
async def get_historical_prices(
    code: str,
    period_type: str = Query("D", description="기간 타입 (D:일, W:주, M:월)"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 데이터 수")
):
    """
    과거 시세 조회

    종목의 과거 시세 데이터를 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            # 과거 시세 조회
            historical_prices = HistoricalPriceTable.get_history_by_code(
                conn, code, period_type, limit
            )

            if not historical_prices:
                raise HTTPException(
                    status_code=404,
                    detail=f"No historical data found for {code}"
                )

            # 종목명 조회
            stock = StockTable.get_stock(conn, code)
            stock_name = stock.name if stock else None

            # 응답 생성
            items = [
                HistoricalPriceResponse(
                    code=h.code,
                    date=h.date,
                    open_price=h.open_price,
                    high_price=h.high_price,
                    low_price=h.low_price,
                    close_price=h.close_price,
                    volume=h.volume,
                    change=h.change,
                    amount=h.amount,
                    period_type=h.period_type,
                    created_at=h.created_at
                )
                for h in historical_prices
            ]

            return HistoricalPriceListResponse(
                code=code,
                name=stock_name,
                period_type=period_type,
                total=len(items),
                items=items
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve historical prices: {str(e)}")


@router.post("/update", response_model=PriceUpdateResponse)
async def update_prices(request: PriceUpdateRequest = PriceUpdateRequest()):
    """
    시세 업데이트

    Cybos Plus에서 최신 시세를 가져와 데이터베이스에 저장합니다.
    """
    # Cybos Plus 연결 확인
    validation_result = validate_connection()
    if not validation_result["is_connected"]:
        raise HTTPException(status_code=503, detail="Cybos Plus not connected")

    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")
    start_time = time.time()

    try:
        fetcher = get_price_fetcher()

        if request.codes:
            # 특정 종목만 업데이트
            target_codes = request.codes
        else:
            # 전체 종목 업데이트
            with get_connection_context(db_path) as conn:
                from ...database.models.stock import MarketKind
                target_codes = []
                for market_kind in request.market_kinds:
                    stocks = StockTable.get_stocks_by_market(conn, market_kind)
                    target_codes.extend([s.code for s in stocks])

        # 시세 조회 및 저장
        total_updated = 0
        failed_count = 0

        with get_connection_context(db_path) as conn:
            for code in target_codes:
                try:
                    price = fetcher.fetch_single_price(code)
                    if price:
                        PriceTable.insert_price(conn, price)
                        total_updated += 1
                    else:
                        failed_count += 1
                except Exception:
                    failed_count += 1

            conn.commit()

        elapsed_time = time.time() - start_time

        return PriceUpdateResponse(
            success=True,
            message=f"Successfully updated {total_updated} prices",
            total_updated=total_updated,
            failed_count=failed_count,
            elapsed_time=elapsed_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price update failed: {str(e)}")

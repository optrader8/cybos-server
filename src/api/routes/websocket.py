"""
WebSocket Router - 실시간 시세 스트리밍

WebSocket을 통해 실시간 시세 데이터를 스트리밍합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set, Dict
import asyncio
import json
import logging
import os

from ...cybos.price.fetcher import get_price_fetcher
from ...cybos.connection.validator import validate_connection
from ...database.connection import get_connection_context
from ...database.models.price import PriceTable

router = APIRouter(tags=["websocket"])
logger = logging.getLogger("cybos-server")


class ConnectionManager:
    """WebSocket 연결 관리자"""

    def __init__(self):
        # 활성 연결: {websocket: set(codes)}
        self.active_connections: Dict[WebSocket, Set[str]] = {}
        # 종목별 구독자: {code: set(websockets)}
        self.subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        """클라이언트 연결"""
        await websocket.accept()
        self.active_connections[websocket] = set()
        logger.info(f"WebSocket client connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        """클라이언트 연결 해제"""
        if websocket in self.active_connections:
            # 구독 정보 제거
            subscribed_codes = self.active_connections[websocket]
            for code in subscribed_codes:
                if code in self.subscriptions:
                    self.subscriptions[code].discard(websocket)
                    if not self.subscriptions[code]:
                        del self.subscriptions[code]

            del self.active_connections[websocket]
            logger.info(f"WebSocket client disconnected: {websocket.client}")

    def subscribe(self, websocket: WebSocket, code: str):
        """종목 구독"""
        if websocket in self.active_connections:
            self.active_connections[websocket].add(code)

            if code not in self.subscriptions:
                self.subscriptions[code] = set()

            self.subscriptions[code].add(websocket)
            logger.info(f"Client {websocket.client} subscribed to {code}")

    def unsubscribe(self, websocket: WebSocket, code: str):
        """종목 구독 해제"""
        if websocket in self.active_connections:
            self.active_connections[websocket].discard(code)

            if code in self.subscriptions:
                self.subscriptions[code].discard(websocket)
                if not self.subscriptions[code]:
                    del self.subscriptions[code]

            logger.info(f"Client {websocket.client} unsubscribed from {code}")

    async def broadcast_to_subscribers(self, code: str, data: dict):
        """특정 종목 구독자에게 브로드캐스트"""
        if code in self.subscriptions:
            disconnected = []

            for websocket in self.subscriptions[code]:
                try:
                    await websocket.send_json(data)
                except Exception as e:
                    logger.error(f"Failed to send to {websocket.client}: {e}")
                    disconnected.append(websocket)

            # 연결 끊긴 클라이언트 정리
            for websocket in disconnected:
                self.disconnect(websocket)


# 전역 연결 관리자
manager = ConnectionManager()


@router.websocket("/ws/prices")
async def websocket_endpoint(websocket: WebSocket):
    """
    실시간 시세 WebSocket 엔드포인트

    클라이언트가 연결하고 종목을 구독하면 실시간 시세를 전송합니다.

    메시지 형식:
    - 구독: {"action": "subscribe", "codes": ["005930", "000660"]}
    - 구독 해제: {"action": "unsubscribe", "codes": ["005930"]}
    - 전체 해제: {"action": "unsubscribe_all"}
    """
    await manager.connect(websocket)

    try:
        while True:
            # 클라이언트 메시지 수신
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                codes = data.get("codes", [])
                for code in codes:
                    manager.subscribe(websocket, code)

                await websocket.send_json({
                    "type": "subscription",
                    "status": "success",
                    "codes": codes
                })

            elif action == "unsubscribe":
                codes = data.get("codes", [])
                for code in codes:
                    manager.unsubscribe(websocket, code)

                await websocket.send_json({
                    "type": "unsubscription",
                    "status": "success",
                    "codes": codes
                })

            elif action == "unsubscribe_all":
                if websocket in manager.active_connections:
                    subscribed_codes = list(manager.active_connections[websocket])
                    for code in subscribed_codes:
                        manager.unsubscribe(websocket, code)

                await websocket.send_json({
                    "type": "unsubscription",
                    "status": "success",
                    "message": "All subscriptions removed"
                })

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown action: {action}"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def price_streaming_task():
    """
    실시간 시세 스트리밍 백그라운드 태스크

    구독된 종목의 시세를 주기적으로 조회하여 브로드캐스트합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")
    fetcher = get_price_fetcher()

    while True:
        try:
            # Cybos Plus 연결 확인
            validation_result = validate_connection()
            if not validation_result["is_connected"]:
                await asyncio.sleep(5)
                continue

            # 구독된 종목 목록
            subscribed_codes = list(manager.subscriptions.keys())

            if not subscribed_codes:
                await asyncio.sleep(1)
                continue

            # 시세 조회 및 브로드캐스트
            for code in subscribed_codes:
                try:
                    # 시세 조회
                    price = fetcher.fetch_single_price(code)

                    if price:
                        # 데이터베이스 저장
                        with get_connection_context(db_path) as conn:
                            PriceTable.insert_price(conn, price)
                            conn.commit()

                        # 브로드캐스트
                        await manager.broadcast_to_subscribers(code, {
                            "type": "price_update",
                            "code": price.code,
                            "name": price.name,
                            "time": price.time,
                            "current_price": price.current_price,
                            "change": price.change,
                            "status": price.status,
                            "open_price": price.open_price,
                            "high_price": price.high_price,
                            "low_price": price.low_price,
                            "prev_close": price.prev_close,
                            "volume": price.volume
                        })

                except Exception as e:
                    logger.error(f"Failed to fetch price for {code}: {e}")

                # Rate limiting
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Price streaming error: {e}")
            await asyncio.sleep(5)


# 백그라운드 태스크 시작 함수
async def start_price_streaming():
    """실시간 시세 스트리밍 시작"""
    asyncio.create_task(price_streaming_task())
    logger.info("✅ Price streaming task started")


# 신호 WebSocket 엔드포인트
@router.websocket("/ws/signals")
async def signals_websocket_endpoint(websocket: WebSocket):
    """
    실시간 트레이딩 신호 WebSocket 엔드포인트

    클라이언트가 연결하고 페어를 구독하면 실시간 신호를 전송합니다.

    메시지 형식:
    - 구독: {"action": "subscribe", "pair_ids": ["005930_000660"]}
    - 구독 해제: {"action": "unsubscribe", "pair_ids": ["005930_000660"]}
    """
    await websocket.accept()
    logger.info(f"Signals WebSocket client connected: {websocket.client}")

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                pair_ids = data.get("pair_ids", [])
                await websocket.send_json({
                    "type": "subscription",
                    "status": "success",
                    "pair_ids": pair_ids,
                    "message": f"Subscribed to {len(pair_ids)} pairs"
                })

            elif action == "unsubscribe":
                pair_ids = data.get("pair_ids", [])
                await websocket.send_json({
                    "type": "unsubscription",
                    "status": "success",
                    "pair_ids": pair_ids
                })

            elif action == "get_active":
                # 활성 신호 조회
                from ...database.models.signal import SignalTable
                db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

                with get_connection_context(db_path) as conn:
                    signals = SignalTable.get_active_signals(conn)
                    await websocket.send_json({
                        "type": "active_signals",
                        "count": len(signals),
                        "signals": [
                            {
                                "signal_id": s.signal_id,
                                "pair_id": s.pair_id,
                                "signal_type": s.signal_type.value,
                                "z_score": s.z_score,
                                "confidence": s.confidence
                            }
                            for s in signals[:10]  # 최대 10개
                        ]
                    })

    except WebSocketDisconnect:
        logger.info(f"Signals WebSocket client disconnected: {websocket.client}")
    except Exception as e:
        logger.error(f"Signals WebSocket error: {e}")

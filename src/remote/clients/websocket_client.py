"""
WebSocket Client - WebSocket 클라이언트

원격 서버에 WebSocket을 통해 실시간 데이터를 전송합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import asyncio
import json
import logging
from typing import Optional, Callable, Any
import websockets
from websockets.exceptions import WebSocketException

logger = logging.getLogger("cybos-server")


class WebSocketClient:
    """WebSocket 클라이언트"""

    def __init__(
        self,
        server_url: str,
        reconnect_interval: float = 5.0,
        ping_interval: float = 30.0,
        ping_timeout: float = 10.0
    ):
        """
        WebSocket 클라이언트 초기화

        Args:
            server_url: 서버 WebSocket URL
            reconnect_interval: 재연결 간격 (초)
            ping_interval: Ping 간격 (초)
            ping_timeout: Ping 타임아웃 (초)
        """
        self.server_url = server_url
        self.reconnect_interval = reconnect_interval
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout

        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.running = False
        self.on_message_callback: Optional[Callable] = None

    async def connect(self) -> bool:
        """
        서버에 연결

        Returns:
            연결 성공 여부
        """
        try:
            self.websocket = await websockets.connect(
                self.server_url,
                ping_interval=self.ping_interval,
                ping_timeout=self.ping_timeout
            )
            self.connected = True
            logger.info(f"WebSocket connected to {self.server_url}")
            return True

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """연결 종료"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("WebSocket disconnected")

    async def send(self, data: Any) -> bool:
        """
        데이터 전송

        Args:
            data: 전송할 데이터 (딕셔너리 또는 JSON 문자열)

        Returns:
            전송 성공 여부
        """
        if not self.connected or not self.websocket:
            logger.warning("WebSocket not connected")
            return False

        try:
            if isinstance(data, dict):
                message = json.dumps(data, ensure_ascii=False)
            else:
                message = str(data)

            await self.websocket.send(message)
            return True

        except WebSocketException as e:
            logger.error(f"Failed to send data: {e}")
            self.connected = False
            return False

    async def receive(self) -> Optional[Any]:
        """
        데이터 수신

        Returns:
            수신한 데이터 또는 None
        """
        if not self.connected or not self.websocket:
            return None

        try:
            message = await self.websocket.recv()

            # JSON 파싱 시도
            try:
                return json.loads(message)
            except json.JSONDecodeError:
                return message

        except WebSocketException as e:
            logger.error(f"Failed to receive data: {e}")
            self.connected = False
            return None

    async def send_price_update(self, price_data: dict) -> bool:
        """
        시세 업데이트 전송

        Args:
            price_data: 시세 데이터

        Returns:
            전송 성공 여부
        """
        message = {
            "type": "price_update",
            "data": price_data
        }
        return await self.send(message)

    async def send_stock_update(self, stock_data: dict) -> bool:
        """
        주식 정보 업데이트 전송

        Args:
            stock_data: 주식 데이터

        Returns:
            전송 성공 여부
        """
        message = {
            "type": "stock_update",
            "data": stock_data
        }
        return await self.send(message)

    def set_on_message_callback(self, callback: Callable):
        """
        메시지 수신 콜백 설정

        Args:
            callback: 메시지 수신 시 호출될 함수
        """
        self.on_message_callback = callback

    async def run(self):
        """
        WebSocket 클라이언트 실행 (자동 재연결 포함)
        """
        self.running = True

        while self.running:
            if not self.connected:
                logger.info("Attempting to connect...")
                await self.connect()

            if self.connected:
                try:
                    message = await self.receive()

                    if message and self.on_message_callback:
                        await self.on_message_callback(message)

                except Exception as e:
                    logger.error(f"Error in WebSocket loop: {e}")
                    self.connected = False

            if not self.connected:
                logger.info(f"Reconnecting in {self.reconnect_interval} seconds...")
                await asyncio.sleep(self.reconnect_interval)

    async def stop(self):
        """WebSocket 클라이언트 중지"""
        self.running = False
        await self.disconnect()
        logger.info("WebSocket client stopped")

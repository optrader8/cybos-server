"""
Data Sender - 데이터 전송 관리자

원격 서버로 데이터를 전송하는 통합 인터페이스를 제공합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import os
import logging
from typing import List, Optional
from .clients.rest_client import RESTClient
from .clients.websocket_client import WebSocketClient
from .formatters.json_formatter import JSONFormatter
from ..database.models.price import PriceInfo
from ..database.models.stock import StockInfo

logger = logging.getLogger("cybos-server")


class DataSender:
    """데이터 전송 관리자"""

    def __init__(
        self,
        rest_url: Optional[str] = None,
        websocket_url: Optional[str] = None,
        api_key: Optional[str] = None,
        use_rest: bool = True,
        use_websocket: bool = False
    ):
        """
        데이터 전송 관리자 초기화

        Args:
            rest_url: REST API 서버 URL
            websocket_url: WebSocket 서버 URL
            api_key: API 인증 키
            use_rest: REST API 사용 여부
            use_websocket: WebSocket 사용 여부
        """
        self.use_rest = use_rest
        self.use_websocket = use_websocket
        self.formatter = JSONFormatter()

        # REST 클라이언트 초기화
        self.rest_client: Optional[RESTClient] = None
        if use_rest and rest_url:
            self.rest_client = RESTClient(
                base_url=rest_url,
                api_key=api_key,
                timeout=int(os.getenv("REMOTE_TIMEOUT", "30")),
                retry_attempts=int(os.getenv("REMOTE_RETRY_ATTEMPTS", "3")),
                retry_delay=float(os.getenv("REMOTE_RETRY_DELAY", "2.0"))
            )
            logger.info(f"REST client initialized: {rest_url}")

        # WebSocket 클라이언트 초기화
        self.websocket_client: Optional[WebSocketClient] = None
        if use_websocket and websocket_url:
            self.websocket_client = WebSocketClient(
                server_url=websocket_url,
                reconnect_interval=5.0
            )
            logger.info(f"WebSocket client initialized: {websocket_url}")

    def send_price(self, price: PriceInfo) -> bool:
        """
        시세 데이터 전송

        Args:
            price: 시세 정보

        Returns:
            전송 성공 여부
        """
        try:
            price_data = self.formatter.format_price(price)
            success = True

            # REST로 전송
            if self.use_rest and self.rest_client:
                if not self.rest_client.send_price(price_data):
                    logger.warning("REST price send failed")
                    success = False

            # WebSocket으로 전송
            if self.use_websocket and self.websocket_client:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if not loop.run_until_complete(self.websocket_client.send_price_update(price_data)):
                        logger.warning("WebSocket price send failed")
                        success = False
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")
                    success = False

            return success

        except Exception as e:
            logger.error(f"Failed to send price data: {e}")
            return False

    def send_prices(self, prices: List[PriceInfo]) -> bool:
        """
        여러 시세 데이터 전송

        Args:
            prices: 시세 정보 리스트

        Returns:
            전송 성공 여부
        """
        try:
            prices_data = self.formatter.format_prices(prices)
            success = True

            # REST로 전송
            if self.use_rest and self.rest_client:
                if not self.rest_client.send_prices(prices_data):
                    logger.warning("REST prices batch send failed")
                    success = False

            return success

        except Exception as e:
            logger.error(f"Failed to send prices data: {e}")
            return False

    def send_stock(self, stock: StockInfo) -> bool:
        """
        주식 정보 전송

        Args:
            stock: 주식 정보

        Returns:
            전송 성공 여부
        """
        try:
            stock_data = self.formatter.format_stock(stock)
            success = True

            # REST로 전송
            if self.use_rest and self.rest_client:
                if not self.rest_client.send_stock(stock_data):
                    logger.warning("REST stock send failed")
                    success = False

            # WebSocket으로 전송
            if self.use_websocket and self.websocket_client:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if not loop.run_until_complete(self.websocket_client.send_stock_update(stock_data)):
                        logger.warning("WebSocket stock send failed")
                        success = False
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")
                    success = False

            return success

        except Exception as e:
            logger.error(f"Failed to send stock data: {e}")
            return False

    def send_stocks(self, stocks: List[StockInfo]) -> bool:
        """
        여러 주식 정보 전송

        Args:
            stocks: 주식 정보 리스트

        Returns:
            전송 성공 여부
        """
        try:
            stocks_data = self.formatter.format_stocks(stocks)
            success = True

            # REST로 전송
            if self.use_rest and self.rest_client:
                if not self.rest_client.send_stocks(stocks_data):
                    logger.warning("REST stocks batch send failed")
                    success = False

            return success

        except Exception as e:
            logger.error(f"Failed to send stocks data: {e}")
            return False

    def health_check(self) -> bool:
        """
        원격 서버 헬스체크

        Returns:
            서버 정상 여부
        """
        if self.rest_client:
            return self.rest_client.health_check()
        return False

    def close(self):
        """연결 종료"""
        if self.rest_client:
            self.rest_client.close()

        if self.websocket_client:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.websocket_client.stop())
            except Exception as e:
                logger.error(f"Error closing WebSocket client: {e}")

        logger.info("Data sender closed")

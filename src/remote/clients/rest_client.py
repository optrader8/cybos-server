"""
REST Client - REST API 클라이언트

원격 서버에 REST API를 통해 데이터를 전송합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import requests
import time
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger("cybos-server")


class RESTClient:
    """REST API 클라이언트"""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        retry_attempts: int = 3,
        retry_delay: float = 2.0
    ):
        """
        REST 클라이언트 초기화

        Args:
            base_url: 서버 기본 URL
            api_key: API 인증 키
            timeout: 요청 타임아웃 (초)
            retry_attempts: 재시도 횟수
            retry_delay: 재시도 간격 (초)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        # 세션 생성
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"X-API-Key": api_key})

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        HTTP 요청 실행

        Args:
            method: HTTP 메서드
            endpoint: 엔드포인트 경로
            data: 요청 본문
            params: 쿼리 파라미터

        Returns:
            응답 데이터 또는 None
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.retry_attempts):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    timeout=self.timeout
                )

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{self.retry_attempts}): {e}")

                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"All retry attempts failed for {url}")
                    return None

        return None

    def send_price(self, price_data: Dict[str, Any]) -> bool:
        """
        시세 데이터 전송

        Args:
            price_data: 시세 데이터

        Returns:
            성공 여부
        """
        result = self._make_request("POST", "/api/prices", data=price_data)
        return result is not None

    def send_prices(self, prices_data: List[Dict[str, Any]]) -> bool:
        """
        여러 시세 데이터 전송

        Args:
            prices_data: 시세 데이터 리스트

        Returns:
            성공 여부
        """
        result = self._make_request("POST", "/api/prices/batch", data={"prices": prices_data})
        return result is not None

    def send_stock(self, stock_data: Dict[str, Any]) -> bool:
        """
        주식 정보 전송

        Args:
            stock_data: 주식 데이터

        Returns:
            성공 여부
        """
        result = self._make_request("POST", "/api/stocks", data=stock_data)
        return result is not None

    def send_stocks(self, stocks_data: List[Dict[str, Any]]) -> bool:
        """
        여러 주식 정보 전송

        Args:
            stocks_data: 주식 데이터 리스트

        Returns:
            성공 여부
        """
        result = self._make_request("POST", "/api/stocks/batch", data={"stocks": stocks_data})
        return result is not None

    def health_check(self) -> bool:
        """
        서버 헬스체크

        Returns:
            서버 정상 여부
        """
        result = self._make_request("GET", "/api/health")
        return result is not None and result.get("status") == "healthy"

    def close(self):
        """연결 종료"""
        self.session.close()
        logger.info("REST client closed")

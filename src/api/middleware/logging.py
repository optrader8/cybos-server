"""
Logging Middleware - 로깅 미들웨어

HTTP 요청/응답을 로깅합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
from typing import Callable

# 로거 설정
logger = logging.getLogger("cybos-server")


class LoggingMiddleware(BaseHTTPMiddleware):
    """HTTP 요청/응답 로깅 미들웨어"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        요청 처리 및 로깅

        Args:
            request: HTTP 요청
            call_next: 다음 미들웨어 호출 함수

        Returns:
            HTTP 응답
        """
        # 요청 시작 시각
        start_time = time.time()

        # 요청 정보
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"

        # 요청 로깅
        logger.info(f"→ {method} {url} from {client_host}")

        try:
            # 다음 미들웨어/라우터 호출
            response = await call_next(request)

            # 처리 시간 계산
            process_time = time.time() - start_time

            # 응답 로깅
            logger.info(
                f"← {method} {url} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )

            # 응답 헤더에 처리 시간 추가
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            # 에러 로깅
            process_time = time.time() - start_time
            logger.error(
                f"✗ {method} {url} - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.3f}s"
            )
            raise


def setup_logging(log_level: str = "INFO") -> None:
    """
    로깅 설정

    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # 로그 레벨 설정
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # 로거 설정
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    logger.setLevel(numeric_level)
    print(f"✅ Logging configured with level: {log_level}")

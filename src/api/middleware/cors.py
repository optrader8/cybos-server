"""
CORS Middleware - CORS 설정

Cross-Origin Resource Sharing 설정을 관리합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import json


def setup_cors(app: FastAPI) -> None:
    """
    CORS 미들웨어 설정

    환경 변수에서 CORS 설정을 읽어와 적용합니다.
    """
    # 환경 변수에서 CORS 설정 읽기
    cors_origins_str = os.getenv(
        "CORS_ORIGINS",
        '["http://localhost:3000", "http://localhost:8080"]'
    )

    cors_methods_str = os.getenv(
        "CORS_METHODS",
        '["GET", "POST", "PUT", "DELETE", "OPTIONS"]'
    )

    cors_headers_str = os.getenv(
        "CORS_HEADERS",
        '["*"]'
    )

    # JSON 파싱
    try:
        cors_origins = json.loads(cors_origins_str)
    except json.JSONDecodeError:
        cors_origins = ["*"]

    try:
        cors_methods = json.loads(cors_methods_str)
    except json.JSONDecodeError:
        cors_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

    try:
        cors_headers = json.loads(cors_headers_str)
    except json.JSONDecodeError:
        cors_headers = ["*"]

    # CORS 미들웨어 추가
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=cors_methods,
        allow_headers=cors_headers,
    )

    print(f"✅ CORS configured with origins: {cors_origins}")

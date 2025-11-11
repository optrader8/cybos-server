"""
API Layer - REST API 인터페이스

FastAPI 기반 REST API 서비스를 제공합니다.
극단적 모듈화 원칙에 따라 각 파일은 300라인 이하로 제한됩니다.
"""

from .app import create_app

__all__ = ["create_app"]

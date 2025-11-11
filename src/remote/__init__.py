"""
Remote Layer - 원격 전송 레이어

원격 서버로 데이터를 전송하는 기능을 제공합니다.
극단적 모듈화 원칙에 따라 각 파일은 300라인 이하로 제한됩니다.
"""

from .sender import DataSender

__all__ = ["DataSender"]

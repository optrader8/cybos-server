"""
Signal Monitor - 신호 모니터

주기적으로 신호를 생성하고 관리합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import asyncio
import sqlite3
from typing import Optional
from datetime import datetime
import os

from .generator import SignalGenerator
from ...database.connection import get_connection_context


class SignalMonitor:
    """신호 모니터"""

    def __init__(
        self,
        db_path: str,
        interval: int = 300,
        lookback_period: int = 60,
        z_score_entry: float = 2.0,
        z_score_exit: float = 0.5,
        min_confidence: float = 0.6,
        max_signals: int = 100
    ):
        """
        Args:
            db_path: 데이터베이스 경로
            interval: 실행 간격 (초)
            lookback_period: 분석 기간 (일)
            z_score_entry: 진입 Z-score 임계값
            z_score_exit: 청산 Z-score 임계값
            min_confidence: 최소 신뢰도
            max_signals: 최대 활성 신호 수
        """
        self.db_path = db_path
        self.interval = interval
        self.max_signals = max_signals

        self.generator = SignalGenerator(
            db_path=db_path,
            lookback_period=lookback_period,
            z_score_entry=z_score_entry,
            z_score_exit=z_score_exit,
            min_confidence=min_confidence
        )

        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """모니터 시작"""
        if self.is_running:
            print("Signal monitor is already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())

        print(f"✅ Signal monitor started (interval: {self.interval}s)")

    async def stop(self) -> None:
        """모니터 중지"""
        if not self.is_running:
            return

        self.is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        print("🛑 Signal monitor stopped")

    async def _run_loop(self) -> None:
        """실행 루프"""
        while self.is_running:
            try:
                # 신호 생성 실행
                await self._run_generation()

                # 대기
                await asyncio.sleep(self.interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in signal monitor loop: {e}")
                await asyncio.sleep(60)  # 에러 시 1분 대기

    async def _run_generation(self) -> None:
        """신호 생성 실행"""
        start_time = datetime.now()
        print(f"\n📊 신호 생성 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            with get_connection_context(self.db_path) as conn:
                # 활성 신호 수 확인
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'ACTIVE'")
                active_count = cursor.fetchone()[0]

                if active_count >= self.max_signals:
                    print(f"   ⚠️  최대 신호 수 도달: {active_count}/{self.max_signals}")
                    return

                # 신호 생성
                signals = self.generator.generate_signals_for_all_pairs(conn)

                if signals:
                    # 신호 저장
                    saved_count = self.generator.save_signals(conn, signals)

                    print(f"   ✅ {saved_count}개 신호 생성 완료")

                    # 신호 요약 출력
                    entry_signals = sum(1 for s in signals if s.is_entry_signal())
                    exit_signals = sum(1 for s in signals if s.is_exit_signal())

                    print(f"      - 진입 신호: {entry_signals}")
                    print(f"      - 청산 신호: {exit_signals}")
                else:
                    print("   ℹ️  생성된 신호 없음")

        except Exception as e:
            print(f"   ❌ 신호 생성 실패: {e}")

        # 실행 시간
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"   ⏱️  실행 시간: {elapsed:.2f}초\n")

    def run_once(self) -> int:
        """
        신호 생성을 1회 실행 (동기)

        Returns:
            생성된 신호 수
        """
        try:
            with get_connection_context(self.db_path) as conn:
                signals = self.generator.generate_signals_for_all_pairs(conn)
                saved_count = self.generator.save_signals(conn, signals)

                print(f"✅ {saved_count}개 신호 생성 완료")

                return saved_count

        except Exception as e:
            print(f"❌ 신호 생성 실패: {e}")
            return 0


# 전역 인스턴스
_monitor: Optional[SignalMonitor] = None


def get_monitor() -> Optional[SignalMonitor]:
    """전역 모니터 인스턴스 반환"""
    return _monitor


def create_monitor(
    db_path: str = None,
    interval: int = None,
    **kwargs
) -> SignalMonitor:
    """
    모니터 생성

    Args:
        db_path: 데이터베이스 경로
        interval: 실행 간격 (초)
        **kwargs: 추가 설정

    Returns:
        SignalMonitor 인스턴스
    """
    global _monitor

    # 환경변수에서 설정 로드
    if db_path is None:
        db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    if interval is None:
        interval = int(os.getenv("SIGNAL_GENERATOR_INTERVAL", "300"))

    # 모니터 생성
    _monitor = SignalMonitor(
        db_path=db_path,
        interval=interval,
        lookback_period=kwargs.get("lookback_period", int(os.getenv("SIGNAL_LOOKBACK_PERIOD", "60"))),
        z_score_entry=kwargs.get("z_score_entry", float(os.getenv("SIGNAL_ENTRY_Z_SCORE", "2.0"))),
        z_score_exit=kwargs.get("z_score_exit", float(os.getenv("SIGNAL_EXIT_Z_SCORE", "0.5"))),
        min_confidence=kwargs.get("min_confidence", float(os.getenv("SIGNAL_MIN_CONFIDENCE", "0.6"))),
        max_signals=kwargs.get("max_signals", int(os.getenv("SIGNAL_GENERATOR_MAX_SIGNALS", "100")))
    )

    return _monitor


async def start_monitor(**kwargs) -> SignalMonitor:
    """
    모니터 시작

    Returns:
        SignalMonitor 인스턴스
    """
    monitor = create_monitor(**kwargs)
    await monitor.start()
    return monitor

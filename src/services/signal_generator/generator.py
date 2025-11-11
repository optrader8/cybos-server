"""
Signal Generator - 트레이딩 신호 생성기

실시간 시장 데이터를 분석하여 트레이딩 신호를 생성합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np

from .analyzer import SpreadAnalyzer
from ...database.models.pair import PairTable, PairInfo
from ...database.models.price import PriceTable
from ...database.models.signal import SignalTable, PairSignal, SignalType, SignalStatus
from ...database.models.cointegration import CointegrationTable


class SignalGenerator:
    """신호 생성기"""

    def __init__(
        self,
        db_path: str,
        lookback_period: int = 60,
        z_score_entry: float = 2.0,
        z_score_exit: float = 0.5,
        min_confidence: float = 0.6
    ):
        """
        Args:
            db_path: 데이터베이스 경로
            lookback_period: 분석 기간 (일)
            z_score_entry: 진입 Z-score 임계값
            z_score_exit: 청산 Z-score 임계값
            min_confidence: 최소 신뢰도
        """
        self.db_path = db_path
        self.lookback_period = lookback_period
        self.min_confidence = min_confidence
        self.analyzer = SpreadAnalyzer(lookback_period, z_score_entry, z_score_exit)

    def generate_signals_for_all_pairs(self, conn: sqlite3.Connection) -> List[PairSignal]:
        """
        모든 활성 페어에 대해 신호 생성

        Args:
            conn: 데이터베이스 연결

        Returns:
            생성된 신호 목록
        """
        signals = []

        # 활성 페어 조회
        active_pairs = PairTable.get_active_pairs(conn)

        for pair in active_pairs:
            # 페어별 신호 생성
            pair_signals = self.generate_signals_for_pair(conn, pair)
            signals.extend(pair_signals)

        return signals

    def generate_signals_for_pair(
        self,
        conn: sqlite3.Connection,
        pair: PairInfo
    ) -> List[PairSignal]:
        """
        특정 페어에 대해 신호 생성

        Args:
            conn: 데이터베이스 연결
            pair: 페어 정보

        Returns:
            생성된 신호 목록
        """
        signals = []

        try:
            # 최신 공적분 결과 조회
            cointegration = CointegrationTable.get_latest_result(conn, pair.pair_id)
            if cointegration is None:
                return signals

            # 가격 데이터 조회
            price_data = self._fetch_price_data(conn, pair.stock_codes)
            if not price_data:
                return signals

            # 스프레드 계산
            spread = self._calculate_spread(price_data, cointegration.hedge_ratios)
            if len(spread) < self.lookback_period:
                return signals  # 데이터 부족

            # Z-score 계산
            z_score = self.analyzer.calculate_z_score(spread)

            # 스프레드 통계
            spread_stats = self.analyzer.calculate_spread_stats(spread)

            # 진입 신호 감지
            entry_signal_type = self.analyzer.detect_entry_signal(spread)

            if entry_signal_type:
                # 신호 생성
                signal = self._create_entry_signal(
                    pair=pair,
                    signal_type=entry_signal_type,
                    z_score=z_score,
                    spread_stats=spread_stats,
                    hedge_ratios=cointegration.hedge_ratios,
                    price_data=price_data
                )

                # 신뢰도 계산
                confidence = self.analyzer.calculate_confidence(spread, z_score)
                signal.confidence = confidence

                # 최소 신뢰도 확인
                if confidence >= self.min_confidence:
                    signals.append(signal)

            # 청산 신호 감지 (기존 활성 신호 확인)
            active_signals = SignalTable.get_active_signals(conn, pair.pair_id)
            for active_signal in active_signals:
                if self.analyzer.detect_exit_signal(
                    spread,
                    active_signal.signal_type.value,
                    self.lookback_period
                ):
                    # 청산 신호 생성
                    exit_signal = self._create_exit_signal(
                        pair=pair,
                        entry_signal=active_signal,
                        z_score=z_score,
                        price_data=price_data
                    )
                    signals.append(exit_signal)

        except Exception as e:
            print(f"Error generating signals for pair {pair.pair_id}: {e}")

        return signals

    def _fetch_price_data(
        self,
        conn: sqlite3.Connection,
        stock_codes: List[str]
    ) -> Dict[str, List[float]]:
        """가격 데이터 조회"""
        price_data = {}

        for stock_code in stock_codes:
            # 최근 lookback_period 기간 가격 조회
            prices = PriceTable.get_recent_prices(conn, stock_code, self.lookback_period)

            if prices:
                price_data[stock_code] = [price.close for price in prices]

        return price_data

    def _calculate_spread(
        self,
        price_data: Dict[str, List[float]],
        hedge_ratios: List[float]
    ) -> np.ndarray:
        """스프레드 계산 (N-way pair)"""
        if len(price_data) < 2:
            return np.array([])

        # 첫 번째 종목을 기준으로
        stock_codes = list(price_data.keys())
        base_prices = np.array(price_data[stock_codes[0]])

        # 나머지 종목들을 헤지 비율로 가중 합산
        spread = base_prices.copy()

        for i, stock_code in enumerate(stock_codes[1:], 1):
            hedge_ratio = hedge_ratios[i] if i < len(hedge_ratios) else 1.0
            spread -= hedge_ratio * np.array(price_data[stock_code])

        return spread

    def _create_entry_signal(
        self,
        pair: PairInfo,
        signal_type: str,
        z_score: float,
        spread_stats: Dict[str, float],
        hedge_ratios: List[float],
        price_data: Dict[str, List[float]]
    ) -> PairSignal:
        """진입 신호 생성"""
        # 현재 가격 (최신)
        current_prices = {code: prices[-1] for code, prices in price_data.items()}

        # 신호 타입 결정
        if signal_type == "LONG":
            signal_type_enum = SignalType.PAIR_ENTRY_LONG
        else:
            signal_type_enum = SignalType.PAIR_ENTRY_SHORT

        # 신호 생성
        signal = PairSignal(
            signal_id="",  # __post_init__에서 자동 생성
            pair_id=pair.pair_id,
            stock_codes=pair.stock_codes,
            signal_type=signal_type_enum,
            status=SignalStatus.ACTIVE,
            current_prices=current_prices,
            spread=spread_stats["current"],
            spread_mean=spread_stats["mean"],
            spread_std=spread_stats["std"],
            z_score=z_score,
            hedge_ratios=hedge_ratios,
            notes=f"Entry signal: {signal_type}, Z-score: {z_score:.2f}"
        )

        return signal

    def _create_exit_signal(
        self,
        pair: PairInfo,
        entry_signal: PairSignal,
        z_score: float,
        price_data: Dict[str, List[float]]
    ) -> PairSignal:
        """청산 신호 생성"""
        # 현재 가격
        current_prices = {code: prices[-1] for code, prices in price_data.items()}

        # 청산 신호 생성
        signal = PairSignal(
            signal_id="",
            pair_id=pair.pair_id,
            stock_codes=pair.stock_codes,
            signal_type=SignalType.PAIR_EXIT,
            status=SignalStatus.ACTIVE,
            current_prices=current_prices,
            entry_prices=entry_signal.entry_prices,
            z_score=z_score,
            hedge_ratios=entry_signal.hedge_ratios,
            notes=f"Exit signal: Z-score returned to {z_score:.2f}"
        )

        return signal

    def save_signals(self, conn: sqlite3.Connection, signals: List[PairSignal]) -> int:
        """
        신호를 데이터베이스에 저장

        Args:
            conn: 데이터베이스 연결
            signals: 저장할 신호 목록

        Returns:
            저장된 신호 수
        """
        saved_count = 0

        for signal in signals:
            try:
                SignalTable.insert_signal(conn, signal)
                saved_count += 1
            except Exception as e:
                print(f"Failed to save signal {signal.signal_id}: {e}")

        conn.commit()

        return saved_count

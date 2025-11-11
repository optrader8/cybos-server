"""
Signals Router - 트레이딩 신호 API

트레이딩 신호를 조회하고 관리하는 API 엔드포인트를 제공합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import os
from datetime import datetime

from ..schemas.signal import (
    SignalResponse,
    SignalListResponse,
    SignalCreateRequest,
    SignalUpdateRequest,
    SignalExecuteRequest,
    SignalExecuteResponse,
    SignalStatsResponse
)
from ...database.connection import get_connection_context
from ...database.models.signal import SignalTable, PairSignal, SignalStatus, SignalType
from ...database.models.pair import PairTable

router = APIRouter(prefix="/api/signals", tags=["signals"])


def _signal_to_response(signal: PairSignal) -> SignalResponse:
    """PairSignal을 SignalResponse로 변환"""
    return SignalResponse(
        signal_id=signal.signal_id,
        pair_id=signal.pair_id,
        stock_codes=signal.stock_codes,
        signal_type=signal.signal_type.value,
        status=signal.status.value,
        current_prices=signal.current_prices,
        entry_prices=signal.entry_prices,
        target_prices=signal.target_prices,
        stop_prices=signal.stop_prices,
        spread=signal.spread,
        spread_mean=signal.spread_mean,
        spread_std=signal.spread_std,
        z_score=signal.z_score,
        position_sizes=signal.position_sizes,
        hedge_ratios=signal.hedge_ratios,
        confidence=signal.confidence,
        expected_return=signal.expected_return,
        risk_level=signal.risk_level,
        notes=signal.notes,
        created_at=signal.created_at,
        executed_at=signal.executed_at,
        expired_at=signal.expired_at
    )


@router.get("/", response_model=SignalListResponse)
async def get_signals(
    status: Optional[str] = Query(None, description="상태 필터 (ACTIVE, EXECUTED, CANCELLED, EXPIRED)"),
    signal_type: Optional[str] = Query(None, description="신호 타입 필터"),
    pair_id: Optional[str] = Query(None, description="페어 ID 필터"),
    limit: int = Query(100, ge=1, le=500, description="조회할 신호 수")
):
    """
    신호 목록 조회

    필터 조건에 맞는 신호 목록을 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            # SQL 쿼리 구성
            conditions = []
            params = []

            if status:
                conditions.append("status = ?")
                params.append(status)

            if signal_type:
                conditions.append("signal_type = ?")
                params.append(signal_type)

            if pair_id:
                conditions.append("pair_id = ?")
                params.append(pair_id)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            # 신호 조회
            cursor = conn.cursor()
            sql = f"""
                SELECT * FROM {SignalTable.TABLE_NAME}
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """
            params.append(limit)
            cursor.execute(sql, tuple(params))

            signals = []
            columns = [desc[0] for desc in cursor.description]

            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                signal = PairSignal.from_dict(data)
                signals.append(_signal_to_response(signal))

            # 총 개수 조회
            count_sql = f"SELECT COUNT(*) FROM {SignalTable.TABLE_NAME} {where_clause}"
            cursor.execute(count_sql, tuple(params[:-1]))
            total = cursor.fetchone()[0]

            return SignalListResponse(total=total, items=signals)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve signals: {str(e)}")


@router.get("/active/list", response_model=SignalListResponse)
async def get_active_signals(pair_id: Optional[str] = Query(None, description="페어 ID 필터")):
    """
    활성 신호 목록 조회

    실행 대기 중인 활성 신호 목록을 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            signals = SignalTable.get_active_signals(conn, pair_id)

            items = [_signal_to_response(signal) for signal in signals]

            return SignalListResponse(total=len(items), items=items)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active signals: {str(e)}")


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(signal_id: str):
    """
    특정 신호 정보 조회

    신호 ID로 신호 정보를 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {SignalTable.TABLE_NAME} WHERE signal_id = ?", (signal_id,))
            row = cursor.fetchone()

            if row is None:
                raise HTTPException(status_code=404, detail=f"Signal not found: {signal_id}")

            columns = [desc[0] for desc in cursor.description]
            data = dict(zip(columns, row))
            signal = PairSignal.from_dict(data)

            return _signal_to_response(signal)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve signal: {str(e)}")


@router.get("/pair/{pair_id}/history", response_model=SignalListResponse)
async def get_pair_signal_history(
    pair_id: str,
    limit: int = Query(50, ge=1, le=200, description="조회할 신호 수")
):
    """
    페어별 신호 이력 조회

    특정 페어의 신호 이력을 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            signals = SignalTable.get_signals_by_pair(conn, pair_id, limit)

            items = [_signal_to_response(signal) for signal in signals]

            return SignalListResponse(total=len(items), items=items)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pair signal history: {str(e)}")


@router.post("/", response_model=SignalResponse)
async def create_signal(request: SignalCreateRequest):
    """
    신호 생성

    새로운 트레이딩 신호를 생성합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            # 페어 확인
            pair = PairTable.get_pair(conn, request.pair_id)
            if pair is None:
                raise HTTPException(status_code=404, detail=f"Pair not found: {request.pair_id}")

            # 신호 객체 생성
            signal = PairSignal(
                signal_id="",  # __post_init__에서 자동 생성
                pair_id=request.pair_id,
                stock_codes=pair.stock_codes,
                signal_type=SignalType(request.signal_type),
                status=SignalStatus.ACTIVE,
                current_prices=request.current_prices,
                z_score=request.z_score or 0.0,
                confidence=request.confidence,
                notes=request.notes
            )

            # 데이터베이스에 저장
            SignalTable.insert_signal(conn, signal)
            conn.commit()

            return _signal_to_response(signal)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create signal: {str(e)}")


@router.put("/{signal_id}", response_model=SignalResponse)
async def update_signal(signal_id: str, request: SignalUpdateRequest):
    """
    신호 업데이트

    신호 상태를 업데이트합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            # 신호 존재 확인
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {SignalTable.TABLE_NAME} WHERE signal_id = ?", (signal_id,))
            row = cursor.fetchone()

            if row is None:
                raise HTTPException(status_code=404, detail=f"Signal not found: {signal_id}")

            # 상태 업데이트
            SignalTable.update_signal_status(conn, signal_id, SignalStatus(request.status))

            # 메모 업데이트
            if request.notes:
                cursor.execute(
                    f"UPDATE {SignalTable.TABLE_NAME} SET notes = ? WHERE signal_id = ?",
                    (request.notes, signal_id)
                )

            conn.commit()

            # 업데이트된 신호 조회
            cursor.execute(f"SELECT * FROM {SignalTable.TABLE_NAME} WHERE signal_id = ?", (signal_id,))
            row = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            data = dict(zip(columns, row))
            signal = PairSignal.from_dict(data)

            return _signal_to_response(signal)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update signal: {str(e)}")


@router.post("/execute", response_model=SignalExecuteResponse)
async def execute_signal(request: SignalExecuteRequest):
    """
    신호 실행

    트레이딩 신호를 실행합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            # 신호 존재 확인
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {SignalTable.TABLE_NAME} WHERE signal_id = ?", (request.signal_id,))
            row = cursor.fetchone()

            if row is None:
                raise HTTPException(status_code=404, detail=f"Signal not found: {request.signal_id}")

            # 신호 상태 업데이트
            SignalTable.update_signal_status(conn, request.signal_id, SignalStatus.EXECUTED)

            # 실행 정보 업데이트
            cursor.execute(
                f"UPDATE {SignalTable.TABLE_NAME} SET entry_prices = ?, position_sizes = ? WHERE signal_id = ?",
                (str(request.execution_prices), str(request.position_sizes), request.signal_id)
            )

            conn.commit()

            return SignalExecuteResponse(
                success=True,
                message="Signal executed successfully",
                signal_id=request.signal_id,
                executed_at=datetime.now().isoformat()
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute signal: {str(e)}")


@router.get("/stats/summary", response_model=SignalStatsResponse)
async def get_signal_stats():
    """
    신호 통계 조회

    전체 신호에 대한 통계 정보를 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            cursor = conn.cursor()

            # 전체 신호 수
            cursor.execute(f"SELECT COUNT(*) FROM {SignalTable.TABLE_NAME}")
            total_signals = cursor.fetchone()[0]

            # 활성 신호 수
            cursor.execute(f"SELECT COUNT(*) FROM {SignalTable.TABLE_NAME} WHERE status = 'ACTIVE'")
            active_signals = cursor.fetchone()[0]

            # 실행된 신호 수
            cursor.execute(f"SELECT COUNT(*) FROM {SignalTable.TABLE_NAME} WHERE status = 'EXECUTED'")
            executed_signals = cursor.fetchone()[0]

            # 타입별 신호 수
            cursor.execute(f"""
                SELECT signal_type, COUNT(*) as count
                FROM {SignalTable.TABLE_NAME}
                GROUP BY signal_type
            """)
            signals_by_type = {row[0]: row[1] for row in cursor.fetchall()}

            # 평균 신뢰도
            cursor.execute(f"SELECT AVG(confidence) FROM {SignalTable.TABLE_NAME} WHERE confidence > 0")
            avg_confidence = cursor.fetchone()[0] or 0.0

            # 평균 기대 수익률
            cursor.execute(f"SELECT AVG(expected_return) FROM {SignalTable.TABLE_NAME} WHERE expected_return > 0")
            avg_expected_return = cursor.fetchone()[0] or 0.0

            return SignalStatsResponse(
                total_signals=total_signals,
                active_signals=active_signals,
                executed_signals=executed_signals,
                signals_by_type=signals_by_type,
                avg_confidence=avg_confidence,
                avg_expected_return=avg_expected_return
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve signal stats: {str(e)}")

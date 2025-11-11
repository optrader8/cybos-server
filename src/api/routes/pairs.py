"""
Pairs Router - 페어 관리 API

페어 트레이딩 페어를 조회하고 관리하는 API 엔드포인트를 제공합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import os

from ..schemas.pair import (
    PairResponse,
    PairListResponse,
    PairCreateRequest,
    PairUpdateRequest,
    PairStatsResponse,
    PairPerformanceResponse
)
from ...database.connection import get_connection_context
from ...database.models.pair import PairTable, PairInfo, PairStatus, PairType

router = APIRouter(prefix="/api/pairs", tags=["pairs"])


def _pair_info_to_response(pair: PairInfo) -> PairResponse:
    """PairInfo를 PairResponse로 변환"""
    return PairResponse(
        pair_id=pair.pair_id,
        pair_type=pair.pair_type.value,
        stock_codes=pair.stock_codes,
        status=pair.status.value,
        name=pair.name,
        description=pair.description,
        cointegration_score=pair.cointegration_score,
        half_life=pair.half_life,
        hedge_ratios=pair.hedge_ratios,
        correlation=pair.correlation,
        spread_mean=pair.spread_mean,
        spread_std=pair.spread_std,
        sharpe_ratio=pair.sharpe_ratio,
        max_drawdown=pair.max_drawdown,
        win_rate=pair.win_rate,
        total_trades=pair.total_trades,
        created_at=pair.created_at,
        updated_at=pair.updated_at,
        last_analyzed_at=pair.last_analyzed_at
    )


@router.get("/", response_model=PairListResponse)
async def get_pairs(
    status: Optional[str] = Query(None, description="상태 필터 (ACTIVE, INACTIVE, MONITORING, SUSPENDED)"),
    pair_type: Optional[str] = Query(None, description="타입 필터 (2-WAY, 3-WAY, 4-WAY, N-WAY)"),
    min_sharpe: Optional[float] = Query(None, description="최소 샤프 비율"),
    limit: int = Query(100, ge=1, le=500, description="조회할 페어 수")
):
    """
    페어 목록 조회

    필터 조건에 맞는 페어 목록을 조회합니다.
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

            if pair_type:
                conditions.append("pair_type = ?")
                params.append(pair_type)

            if min_sharpe is not None:
                conditions.append("sharpe_ratio >= ?")
                params.append(min_sharpe)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            # 페어 조회
            cursor = conn.cursor()
            sql = f"""
                SELECT * FROM {PairTable.TABLE_NAME}
                {where_clause}
                ORDER BY sharpe_ratio DESC
                LIMIT ?
            """
            params.append(limit)
            cursor.execute(sql, tuple(params))

            pairs = []
            columns = [desc[0] for desc in cursor.description]

            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                pair = PairInfo.from_dict(data)
                pairs.append(_pair_info_to_response(pair))

            # 총 개수 조회
            count_sql = f"SELECT COUNT(*) FROM {PairTable.TABLE_NAME} {where_clause}"
            cursor.execute(count_sql, tuple(params[:-1]))
            total = cursor.fetchone()[0]

            return PairListResponse(total=total, items=pairs)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pairs: {str(e)}")


@router.get("/{pair_id}", response_model=PairResponse)
async def get_pair(pair_id: str):
    """
    특정 페어 정보 조회

    페어 ID로 페어 정보를 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            pair = PairTable.get_pair(conn, pair_id)

            if pair is None:
                raise HTTPException(status_code=404, detail=f"Pair not found: {pair_id}")

            return _pair_info_to_response(pair)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pair: {str(e)}")


@router.get("/active/list", response_model=PairListResponse)
async def get_active_pairs(
    pair_type: Optional[str] = Query(None, description="타입 필터"),
    limit: int = Query(100, ge=1, le=500, description="조회할 페어 수")
):
    """
    활성 페어 목록 조회

    거래 가능한 활성 페어 목록을 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            pt = PairType(pair_type) if pair_type else None
            pairs = PairTable.get_active_pairs(conn, pt)[:limit]

            items = [_pair_info_to_response(pair) for pair in pairs]

            return PairListResponse(total=len(items), items=items)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active pairs: {str(e)}")


@router.get("/top/performers", response_model=PairListResponse)
async def get_top_pairs(
    limit: int = Query(20, ge=1, le=100, description="조회할 페어 수"),
    min_sharpe: float = Query(0.5, description="최소 샤프 비율")
):
    """
    상위 성과 페어 조회

    샤프 비율 기준 상위 페어를 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            pairs = PairTable.get_top_pairs(conn, limit, min_sharpe)

            items = [_pair_info_to_response(pair) for pair in pairs]

            return PairListResponse(total=len(items), items=items)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve top pairs: {str(e)}")


@router.get("/by-stock/{stock_code}", response_model=PairListResponse)
async def get_pairs_by_stock(stock_code: str):
    """
    특정 종목 포함 페어 조회

    특정 종목이 포함된 페어 목록을 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            pairs = PairTable.get_pairs_by_stock(conn, stock_code)

            items = [_pair_info_to_response(pair) for pair in pairs]

            return PairListResponse(total=len(items), items=items)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pairs by stock: {str(e)}")


@router.post("/", response_model=PairResponse)
async def create_pair(request: PairCreateRequest):
    """
    페어 생성

    새로운 페어를 생성합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        # 페어 ID 생성
        sorted_codes = sorted(request.stock_codes)
        pair_id = "_".join(sorted_codes)

        # PairInfo 객체 생성
        pair = PairInfo(
            pair_id=pair_id,
            pair_type=PairType.TWO_WAY,  # __post_init__에서 자동 설정됨
            stock_codes=request.stock_codes,
            status=PairStatus.MONITORING,
            name=request.name,
            description=request.description
        )

        # 데이터베이스에 저장
        with get_connection_context(db_path) as conn:
            # 기존 페어 확인
            existing = PairTable.get_pair(conn, pair_id)
            if existing:
                raise HTTPException(status_code=400, detail=f"Pair already exists: {pair_id}")

            PairTable.upsert_pair(conn, pair)
            conn.commit()

        return _pair_info_to_response(pair)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create pair: {str(e)}")


@router.put("/{pair_id}", response_model=PairResponse)
async def update_pair(pair_id: str, request: PairUpdateRequest):
    """
    페어 업데이트

    페어 정보를 업데이트합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            # 기존 페어 조회
            pair = PairTable.get_pair(conn, pair_id)
            if pair is None:
                raise HTTPException(status_code=404, detail=f"Pair not found: {pair_id}")

            # 업데이트
            if request.status:
                pair.status = PairStatus(request.status)
            if request.name:
                pair.name = request.name
            if request.description:
                pair.description = request.description

            # 저장
            PairTable.upsert_pair(conn, pair)
            conn.commit()

        return _pair_info_to_response(pair)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update pair: {str(e)}")


@router.get("/stats/summary", response_model=PairStatsResponse)
async def get_pair_stats():
    """
    페어 통계 조회

    전체 페어에 대한 통계 정보를 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            cursor = conn.cursor()

            # 전체 페어 수
            cursor.execute(f"SELECT COUNT(*) FROM {PairTable.TABLE_NAME}")
            total_pairs = cursor.fetchone()[0]

            # 활성 페어 수
            cursor.execute(f"SELECT COUNT(*) FROM {PairTable.TABLE_NAME} WHERE status = 'ACTIVE'")
            active_pairs = cursor.fetchone()[0]

            # 타입별 페어 수
            pairs_by_type = PairTable.count_pairs_by_type(conn)

            # 평균 샤프 비율
            cursor.execute(f"SELECT AVG(sharpe_ratio) FROM {PairTable.TABLE_NAME} WHERE sharpe_ratio > 0")
            avg_sharpe = cursor.fetchone()[0] or 0.0

            # 평균 승률
            cursor.execute(f"SELECT AVG(win_rate) FROM {PairTable.TABLE_NAME} WHERE win_rate > 0")
            avg_win_rate = cursor.fetchone()[0] or 0.0

            return PairStatsResponse(
                total_pairs=total_pairs,
                active_pairs=active_pairs,
                pairs_by_type=pairs_by_type,
                avg_sharpe_ratio=avg_sharpe,
                avg_win_rate=avg_win_rate
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pair stats: {str(e)}")

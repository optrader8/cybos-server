"""
Cointegration Router - 공적분 분석 API

공적분 분석 결과를 조회하고 분석을 실행하는 API 엔드포인트를 제공합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import os

from ..schemas.cointegration import (
    CointegrationResponse,
    CointegrationListResponse,
    CointegrationAnalyzeRequest,
    CointegrationAnalyzeResponse,
    CointegrationSummaryResponse
)
from ...database.connection import get_connection_context
from ...database.models.cointegration import CointegrationTable, CointegrationResult

router = APIRouter(prefix="/api/cointegration", tags=["cointegration"])


def _result_to_response(result: CointegrationResult) -> CointegrationResponse:
    """CointegrationResult를 CointegrationResponse로 변환"""
    return CointegrationResponse(
        result_id=result.result_id,
        pair_id=result.pair_id,
        stock_codes=result.stock_codes,
        method=result.method.value,
        test_statistic=result.test_statistic,
        p_value=result.p_value,
        critical_values=result.critical_values,
        cointegration_vector=result.cointegration_vector,
        hedge_ratios=result.hedge_ratios,
        intercept=result.intercept,
        residuals_mean=result.residuals_mean,
        residuals_std=result.residuals_std,
        half_life=result.half_life,
        adf_statistic=result.adf_statistic,
        adf_p_value=result.adf_p_value,
        sample_size=result.sample_size,
        start_date=result.start_date,
        end_date=result.end_date,
        significance=result.significance.value,
        window_days=result.window_days,
        created_at=result.created_at
    )


@router.get("/{pair_id}", response_model=CointegrationResponse)
async def get_latest_cointegration(pair_id: str):
    """
    최신 공적분 결과 조회

    특정 페어의 최신 공적분 분석 결과를 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            result = CointegrationTable.get_latest_result(conn, pair_id)

            if result is None:
                raise HTTPException(status_code=404, detail=f"No cointegration result found for pair: {pair_id}")

            return _result_to_response(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cointegration result: {str(e)}")


@router.get("/{pair_id}/history", response_model=CointegrationListResponse)
async def get_cointegration_history(
    pair_id: str,
    limit: int = Query(10, ge=1, le=50, description="조회할 결과 수")
):
    """
    공적분 분석 이력 조회

    특정 페어의 공적분 분석 이력을 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            results = CointegrationTable.get_results_by_pair(conn, pair_id, limit)

            items = [_result_to_response(result) for result in results]

            return CointegrationListResponse(total=len(items), items=items)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cointegration history: {str(e)}")


@router.get("/significant/pairs", response_model=CointegrationListResponse)
async def get_significant_cointegration(
    max_p_value: float = Query(0.05, ge=0.0, le=1.0, description="최대 p-value")
):
    """
    유의한 공적분 페어 조회

    통계적으로 유의한 공적분 관계가 있는 페어를 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            results = CointegrationTable.get_significant_results(conn, max_p_value)

            items = [_result_to_response(result) for result in results]

            return CointegrationListResponse(total=len(items), items=items)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve significant cointegration: {str(e)}")


@router.post("/analyze", response_model=CointegrationAnalyzeResponse)
async def analyze_cointegration(request: CointegrationAnalyzeRequest):
    """
    공적분 분석 실행

    종목 간 공적분 관계를 분석합니다.
    """
    if len(request.stock_codes) != 2:
        raise HTTPException(status_code=400, detail="Currently only 2-stock pairs are supported")

    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")
    pair_id = "_".join(sorted(request.stock_codes))

    try:
        from ...services.cointegration_analyzer import get_analyzer, CointegrationMethod
        from ...database.models.price import PriceTable
        from datetime import datetime, timedelta

        with get_connection_context(db_path) as conn:
            # 가격 데이터 조회
            end_date = datetime.now()
            start_date = end_date - timedelta(days=request.window_days)

            prices_data = {}
            for stock_code in request.stock_codes:
                prices = PriceTable.get_recent_prices(conn, stock_code, request.window_days)
                if not prices:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No price data found for stock: {stock_code}"
                    )
                prices_data[stock_code] = [p.close for p in prices]

            # 가격 데이터 길이 확인
            if len(prices_data[request.stock_codes[0]]) < 30:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient data: need at least 30 observations"
                )

            # 공적분 분석 실행
            analyzer = get_analyzer()
            method = CointegrationMethod(request.method)

            analysis_result = analyzer.analyze_pair(
                prices_data[request.stock_codes[0]],
                prices_data[request.stock_codes[1]],
                method
            )

            # 결과를 데이터베이스에 저장
            result_obj = CointegrationResult(
                result_id="",  # auto-generated
                pair_id=pair_id,
                stock_codes=request.stock_codes,
                method=request.method,
                test_statistic=analysis_result["test_statistic"],
                p_value=analysis_result["p_value"],
                critical_values=analysis_result["critical_values"],
                cointegration_vector=analysis_result["cointegration_vector"],
                hedge_ratios=analysis_result["hedge_ratios"],
                intercept=analysis_result["intercept"],
                residuals_mean=analysis_result["residuals_mean"],
                residuals_std=analysis_result["residuals_std"],
                half_life=analysis_result["half_life"],
                adf_statistic=analysis_result["adf_statistic"],
                adf_p_value=analysis_result["adf_p_value"],
                sample_size=analysis_result["sample_size"],
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                significance=analysis_result["significance"],
                window_days=request.window_days
            )

            CointegrationTable.insert_result(conn, result_obj)
            conn.commit()

            return CointegrationAnalyzeResponse(
                success=True,
                message="Cointegration analysis completed successfully.",
                result=_result_to_response(result_obj)
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cointegration analysis failed: {str(e)}")


@router.get("/summary/stats", response_model=CointegrationSummaryResponse)
async def get_cointegration_summary():
    """
    공적분 요약 통계 조회

    전체 공적분 분석 결과에 대한 요약 통계를 조회합니다.
    """
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")

    try:
        with get_connection_context(db_path) as conn:
            cursor = conn.cursor()

            # 전체 결과 수 (최신 결과만)
            cursor.execute(f"""
                WITH LatestResults AS (
                    SELECT *,
                           ROW_NUMBER() OVER (PARTITION BY pair_id ORDER BY created_at DESC) as rn
                    FROM {CointegrationTable.TABLE_NAME}
                )
                SELECT COUNT(*) FROM LatestResults WHERE rn = 1
            """)
            total_results = cursor.fetchone()[0]

            # 유의성별 결과 수
            cursor.execute(f"""
                WITH LatestResults AS (
                    SELECT *,
                           ROW_NUMBER() OVER (PARTITION BY pair_id ORDER BY created_at DESC) as rn
                    FROM {CointegrationTable.TABLE_NAME}
                )
                SELECT significance, COUNT(*) as count
                FROM LatestResults
                WHERE rn = 1
                GROUP BY significance
            """)
            significance_counts = {row[0]: row[1] for row in cursor.fetchall()}

            highly_significant = significance_counts.get("HIGHLY_SIG", 0)
            significant = significance_counts.get("SIGNIFICANT", 0)
            marginal = significance_counts.get("MARGINAL", 0)
            not_significant = significance_counts.get("NOT_SIG", 0)

            # 평균 p-value
            cursor.execute(f"""
                WITH LatestResults AS (
                    SELECT *,
                           ROW_NUMBER() OVER (PARTITION BY pair_id ORDER BY created_at DESC) as rn
                    FROM {CointegrationTable.TABLE_NAME}
                )
                SELECT AVG(p_value) FROM LatestResults WHERE rn = 1
            """)
            avg_p_value = cursor.fetchone()[0] or 0.0

            # 평균 반감기
            cursor.execute(f"""
                WITH LatestResults AS (
                    SELECT *,
                           ROW_NUMBER() OVER (PARTITION BY pair_id ORDER BY created_at DESC) as rn
                    FROM {CointegrationTable.TABLE_NAME}
                )
                SELECT AVG(half_life) FROM LatestResults WHERE rn = 1 AND half_life > 0
            """)
            avg_half_life = cursor.fetchone()[0] or 0.0

            return CointegrationSummaryResponse(
                total_results=total_results,
                highly_significant=highly_significant,
                significant=significant,
                marginal=marginal,
                not_significant=not_significant,
                avg_p_value=avg_p_value,
                avg_half_life=avg_half_life
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cointegration summary: {str(e)}")

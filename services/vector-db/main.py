"""
Vector DB Service - 시계열 임베딩 및 유사도 검색 서비스

시계열 데이터를 벡터로 임베딩하고 Qdrant에 저장하여
유사한 주식 패턴을 빠르게 검색할 수 있는 서비스입니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)

from sklearn.preprocessing import StandardScaler
from scipy.stats import skew, kurtosis

from src.database.connection import get_connection_context
from src.database.models.history import HistoryTable, HistoryTimeframe


class TimeSeriesEmbedding:
    """시계열 데이터 임베딩"""

    @staticmethod
    def extract_statistical_features(prices: np.ndarray) -> np.ndarray:
        """
        통계적 특징 추출
        - 수익률 평균, 표준편차
        - 왜도(Skewness), 첨도(Kurtosis)
        - 최대 낙폭(Max Drawdown)
        - 샤프 비율 추정
        """
        if len(prices) < 2:
            return np.zeros(10)

        # 수익률 계산
        returns = np.diff(np.log(prices))

        features = []

        # 기본 통계
        features.append(np.mean(returns))           # 평균 수익률
        features.append(np.std(returns))            # 변동성
        features.append(skew(returns))              # 왜도
        features.append(kurtosis(returns))          # 첨도

        # 리스크 메트릭
        sharpe = np.mean(returns) / (np.std(returns) + 1e-10)
        features.append(sharpe)                     # 샤프 비율

        # 최대 낙폭
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_dd = np.min(drawdown)
        features.append(max_dd)                     # 최대 낙폭

        # 모멘텀 지표
        features.append(returns[-5:].mean())        # 최근 5일 평균
        features.append(returns[-20:].mean())       # 최근 20일 평균
        features.append(returns[-60:].mean())       # 최근 60일 평균

        # 변동성 비율
        vol_ratio = np.std(returns[-20:]) / (np.std(returns) + 1e-10)
        features.append(vol_ratio)                  # 최근 변동성 비율

        return np.array(features)

    @staticmethod
    def extract_shape_features(prices: np.ndarray, n_segments: int = 10) -> np.ndarray:
        """
        시계열 형태 특징 추출 (Piecewise Aggregate Approximation)
        """
        if len(prices) < n_segments:
            return np.zeros(n_segments)

        # 정규화
        normalized = (prices - np.mean(prices)) / (np.std(prices) + 1e-10)

        # 구간별 평균
        segment_size = len(normalized) // n_segments
        segments = []

        for i in range(n_segments):
            start = i * segment_size
            end = start + segment_size if i < n_segments - 1 else len(normalized)
            segments.append(np.mean(normalized[start:end]))

        return np.array(segments)

    @staticmethod
    def extract_frequency_features(prices: np.ndarray, n_coeff: int = 5) -> np.ndarray:
        """
        주파수 도메인 특징 추출 (FFT)
        """
        if len(prices) < n_coeff * 2:
            return np.zeros(n_coeff)

        # FFT 적용
        fft = np.fft.fft(prices)
        fft_abs = np.abs(fft)

        # 상위 N개 계수만 사용
        return fft_abs[1:n_coeff + 1]

    def create_embedding(self, prices: np.ndarray,
                        window_days: int = 60) -> np.ndarray:
        """
        종합 임베딩 벡터 생성
        """
        if len(prices) < window_days:
            # 데이터가 부족하면 0 벡터 반환
            return np.zeros(25)  # 10 + 10 + 5

        # 최근 window_days 데이터만 사용
        recent_prices = prices[-window_days:]

        # 특징 추출
        stat_features = self.extract_statistical_features(recent_prices)        # 10
        shape_features = self.extract_shape_features(recent_prices, 10)         # 10
        freq_features = self.extract_frequency_features(recent_prices, 5)       # 5

        # 결합
        embedding = np.concatenate([stat_features, shape_features, freq_features])

        # 정규화
        embedding = embedding / (np.linalg.norm(embedding) + 1e-10)

        return embedding


class VectorDBService:
    """벡터 DB 서비스 (Qdrant)"""

    def __init__(self, host: str = "localhost", port: int = 6333,
                 collection_name: str = "stock_timeseries"):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self.embedding_dim = 25
        self.embedder = TimeSeriesEmbedding()

    def initialize_collection(self) -> None:
        """컬렉션 초기화"""
        try:
            # 기존 컬렉션 삭제
            self.client.delete_collection(self.collection_name)
        except:
            pass

        # 새 컬렉션 생성
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.embedding_dim,
                distance=Distance.COSINE
            )
        )

        print(f"✅ 컬렉션 '{self.collection_name}' 생성 완료")

    def index_stock(self, stock_code: str, prices: np.ndarray,
                   metadata: Optional[Dict] = None) -> None:
        """주식 시계열 데이터 인덱싱"""
        # 임베딩 생성
        embedding = self.embedder.create_embedding(prices)

        # 메타데이터
        if metadata is None:
            metadata = {}

        metadata['stock_code'] = stock_code
        metadata['indexed_at'] = datetime.now().isoformat()

        # Qdrant에 저장
        point = PointStruct(
            id=hash(stock_code) % (2**63),  # 고유 ID 생성
            vector=embedding.tolist(),
            payload=metadata
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

    def search_similar_stocks(self, stock_code: str,
                             top_k: int = 10) -> List[Tuple[str, float]]:
        """유사한 주식 검색"""
        # 해당 주식의 벡터 가져오기
        stock_id = hash(stock_code) % (2**63)

        try:
            stock_point = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[stock_id]
            )

            if not stock_point:
                return []

            vector = stock_point[0].vector

            # 유사도 검색
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=top_k + 1  # 자기 자신 제외
            )

            # 결과 파싱
            similar_stocks = []
            for result in search_results:
                code = result.payload.get('stock_code')
                if code != stock_code:  # 자기 자신 제외
                    similar_stocks.append((code, result.score))

            return similar_stocks[:top_k]

        except Exception as e:
            print(f"검색 실패: {e}")
            return []

    def batch_index_stocks(self, stock_codes: List[str],
                          db_path: str = "data/cybos.db",
                          window_days: int = 252) -> None:
        """배치 인덱싱"""
        print(f"🔄 {len(stock_codes)}개 종목 인덱싱 시작...")

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=window_days * 1.5)).strftime("%Y-%m-%d")

        success_count = 0

        with get_connection_context(db_path) as conn:
            for i, code in enumerate(stock_codes):
                if (i + 1) % 10 == 0:
                    print(f"  진행률: {i + 1}/{len(stock_codes)} ({(i + 1) / len(stock_codes) * 100:.1f}%)")

                try:
                    # 히스토리 데이터 조회
                    history_list = HistoryTable.get_history(
                        conn, code, HistoryTimeframe.DAILY, start_date, end_date
                    )

                    if len(history_list) >= window_days:
                        prices = np.array([h.close_price for h in history_list])

                        # 메타데이터
                        metadata = {
                            'total_records': len(history_list),
                            'start_date': history_list[0].date,
                            'end_date': history_list[-1].date
                        }

                        # 인덱싱
                        self.index_stock(code, prices, metadata)
                        success_count += 1

                except Exception as e:
                    print(f"  ⚠️  {code} 인덱싱 실패: {e}")

        print(f"✅ {success_count}개 종목 인덱싱 완료")


def main():
    """메인 함수"""
    print("🚀 벡터 DB 서비스 시작")
    print("=" * 60)

    # 벡터 DB 서비스 초기화
    vector_db = VectorDBService()

    try:
        vector_db.initialize_collection()
    except Exception as e:
        print(f"⚠️  Qdrant 연결 실패: {e}")
        print("Docker로 Qdrant를 실행하세요:")
        print("  docker run -p 6333:6333 qdrant/qdrant")
        return

    # KOSPI200 종목 인덱싱
    from src.database.models.stock import StockTable

    with get_connection_context() as conn:
        kospi200_stocks = StockTable.get_kospi200_stocks(conn)
        stock_codes = [stock.code for stock in kospi200_stocks[:50]]  # 테스트용 50개

    # 배치 인덱싱
    vector_db.batch_index_stocks(stock_codes)

    # 유사 종목 검색 테스트
    if stock_codes:
        test_code = stock_codes[0]
        print(f"\n🔍 '{test_code}' 와 유사한 종목 검색:")

        similar = vector_db.search_similar_stocks(test_code, top_k=5)

        for i, (code, score) in enumerate(similar, 1):
            print(f"  {i}. {code} (유사도: {score:.4f})")


if __name__ == "__main__":
    main()

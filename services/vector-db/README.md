# 벡터 DB 서비스 (Vector Database Service)

시계열 임베딩 및 유사도 검색을 통한 페어 후보 필터링

## 🎯 목적

페어 트레이딩에서 **조합 폭발 문제** 해결:

```
KOSPI200 (200개 종목):
- 2-way: C(200,2) = 19,900개
- 3-way: C(200,3) = 1,313,400개 ← 분석 불가능!

벡터 DB 필터링 적용:
- 유사한 종목끼리만 페어 분석
- 19,900개 → 2,000개 (90% 감소)
- 분석 시간: 수일 → 수시간
```

## 🏗️ 아키텍처

```
히스토리 데이터 (OHLCV)
      ↓
시계열 임베딩 (25차원 벡터)
  ├─ 통계 특징 (10차원)
  ├─ 형태 특징 (10차원)
  └─ 주파수 특징 (5차원)
      ↓
Qdrant 벡터 DB 저장
      ↓
유사도 검색 (Cosine Similarity)
      ↓
페어 후보군 (Top 10)
```

## 🔧 설치 및 실행

### Qdrant 실행 (Docker)

```bash
# docker-compose로 실행
docker-compose up -d qdrant

# 또는 직접 실행
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### Python 의존성

```bash
cd services/vector-db
pip install -r requirements.txt
```

### 기본 실행

```bash
python main.py
```

## 📊 시계열 임베딩

### 1. 통계적 특징 (10차원)

```python
def extract_statistical_features(prices: np.ndarray) -> np.ndarray:
    """
    수익률 기반 통계 특징 추출
    """
    returns = np.diff(np.log(prices))

    return [
        np.mean(returns),              # 1. 평균 수익률
        np.std(returns),               # 2. 변동성
        skew(returns),                 # 3. 왜도 (비대칭성)
        kurtosis(returns),             # 4. 첨도 (꼬리 두께)
        sharpe_ratio,                  # 5. 샤프 비율
        max_drawdown,                  # 6. 최대 낙폭
        returns[-5:].mean(),           # 7. 최근 5일 모멘텀
        returns[-20:].mean(),          # 8. 최근 20일 모멘텀
        returns[-60:].mean(),          # 9. 최근 60일 모멘텀
        volatility_ratio,              # 10. 변동성 비율
    ]
```

### 2. 형태 특징 (10차원)

```python
def extract_shape_features(prices: np.ndarray) -> np.ndarray:
    """
    Piecewise Aggregate Approximation (PAA)
    시계열을 10개 구간으로 나눠 각 구간의 평균
    """
    normalized = (prices - mean) / std
    segments = split_into_10_segments(normalized)
    return [segment.mean() for segment in segments]
```

**예시:**
```
가격: [100, 102, 105, 103, ...] (60일)
정규화: [0.0, 0.2, 0.5, 0.3, ...]
10구간 평균: [0.2, 0.4, 0.3, 0.1, ...]
```

### 3. 주파수 특징 (5차원)

```python
def extract_frequency_features(prices: np.ndarray) -> np.ndarray:
    """
    Fast Fourier Transform (FFT)
    주기적 패턴 추출
    """
    fft = np.fft.fft(prices)
    fft_abs = np.abs(fft)
    return fft_abs[1:6]  # 상위 5개 주파수 성분
```

**해석:**
- 저주파: 장기 트렌드
- 고주파: 단기 변동

## 🚀 사용법

### 기본 인덱싱

```python
from main import VectorDBService

vector_db = VectorDBService(
    host="localhost",
    port=6333,
    collection_name="stock_timeseries"
)

# 컬렉션 초기화
vector_db.initialize_collection()

# 단일 종목 인덱싱
prices = np.array([...])  # 252일 종가 데이터
vector_db.index_stock('005930', prices, metadata={'name': '삼성전자'})

# 배치 인덱싱
stock_codes = ['005930', '000660', '035420', ...]
vector_db.batch_index_stocks(stock_codes, window_days=252)
```

### 유사 종목 검색

```python
# 삼성전자와 유사한 종목 상위 10개
similar = vector_db.search_similar_stocks('005930', top_k=10)

for code, score in similar:
    print(f"{code}: {score:.4f}")

# 출력:
# 000660: 0.8945  (SK하이닉스)
# 051910: 0.8523  (LG화학)
# 006400: 0.8312  (삼성SDI)
# ...
```

### 페어 후보 생성

```python
# 모든 KOSPI200 종목의 유사 종목
candidates = {}

for stock in kospi200_stocks:
    similar = vector_db.search_similar_stocks(stock, top_k=10)
    candidates[stock] = similar

# 총 페어 후보: 200 × 10 = 2,000개
# (원래 C(200,2) = 19,900개에서 90% 감소)
```

## 🎯 유사도 측정

### Cosine Similarity

```python
similarity = cos(θ) = (A · B) / (||A|| × ||B||)

# 범위: -1 ~ 1
#  1.0: 완전히 같은 패턴
#  0.0: 무관계
# -1.0: 정반대 패턴
```

### 유사도 해석

```
> 0.9: 거의 동일 (같은 업종, ETF 구성 종목)
0.8-0.9: 매우 유사 (관련 업종)
0.7-0.8: 유사 (페어 트레이딩 후보)
0.6-0.7: 약간 유사
< 0.6: 낮은 유사도
```

## 📈 성능 최적화

### HNSW 그래프 파라미터

```python
# Qdrant 컬렉션 생성 시
vectors_config = VectorParams(
    size=25,
    distance=Distance.COSINE,
    hnsw_config={
        "m": 16,              # 그래프 연결 수 (높을수록 정확, 느림)
        "ef_construct": 100,  # 인덱싱 정확도
    }
)
```

### 검색 파라미터

```python
# 검색 시
search_params = {
    "hnsw_ef": 128,  # 검색 정확도 (높을수록 정확, 느림)
    "exact": False,  # True면 완전 탐색 (매우 느림)
}

results = vector_db.client.search(
    collection_name="stock_timeseries",
    query_vector=vector,
    limit=10,
    search_params=search_params
)
```

### 배치 인덱싱

```python
# 한 번에 여러 종목 인덱싱
points = [
    PointStruct(
        id=hash(code),
        vector=embedding.tolist(),
        payload={'stock_code': code}
    )
    for code, embedding in stock_embeddings.items()
]

vector_db.client.upsert(
    collection_name="stock_timeseries",
    points=points
)
```

## 🔍 고급 기능

### 메타데이터 필터링

```python
# 특정 업종만 검색
results = vector_db.client.search(
    collection_name="stock_timeseries",
    query_vector=vector,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="industry",
                match=MatchValue(value="반도체")
            )
        ]
    ),
    limit=10
)
```

### 시간대별 임베딩

```python
# 최근 60일, 120일, 252일 각각 임베딩
embeddings = {
    '60d': embedder.create_embedding(prices[-60:]),
    '120d': embedder.create_embedding(prices[-120:]),
    '252d': embedder.create_embedding(prices[-252:]),
}

# 단기/장기 유사도 비교
short_term_similar = search(embeddings['60d'])
long_term_similar = search(embeddings['252d'])
```

### 동적 임베딩 업데이트

```python
# 매일 장 마감 후 업데이트
def update_embeddings_daily():
    for stock in active_stocks:
        prices = get_latest_prices(stock, days=252)
        embedding = embedder.create_embedding(prices)

        vector_db.index_stock(
            stock_code=stock,
            prices=prices,
            metadata={'updated_at': datetime.now()}
        )
```

## 🎨 시각화

### t-SNE 차원 축소

```python
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

# 25차원 → 2차원
vectors = [...]  # 모든 종목 벡터
tsne = TSNE(n_components=2)
vectors_2d = tsne.fit_transform(vectors)

plt.scatter(vectors_2d[:, 0], vectors_2d[:, 1])
for i, code in enumerate(stock_codes):
    plt.annotate(code, (vectors_2d[i, 0], vectors_2d[i, 1]))
plt.title("Stock Embeddings (t-SNE)")
plt.show()
```

### 유사도 히트맵

```python
import seaborn as sns

# 종목 간 유사도 행렬
similarity_matrix = compute_similarity_matrix(stocks)

plt.figure(figsize=(12, 10))
sns.heatmap(similarity_matrix, cmap='coolwarm', center=0)
plt.title("Stock Similarity Matrix")
plt.show()
```

## 🧪 테스트

### 유닛 테스트

```python
def test_embedding_dimension():
    embedder = TimeSeriesEmbedding()
    prices = np.random.randn(252)

    embedding = embedder.create_embedding(prices)

    assert embedding.shape == (25,)
    assert np.linalg.norm(embedding) > 0

def test_similarity_symmetry():
    # sim(A, B) == sim(B, A)
    sim_ab = vector_db.compute_similarity(stock_a, stock_b)
    sim_ba = vector_db.compute_similarity(stock_b, stock_a)

    assert abs(sim_ab - sim_ba) < 1e-6
```

### 통합 테스트

```python
def test_end_to_end():
    # 1. 인덱싱
    vector_db.index_stock('005930', prices_samsung)
    vector_db.index_stock('000660', prices_sk)

    # 2. 검색
    similar = vector_db.search_similar_stocks('005930', top_k=5)

    # 3. 검증
    assert '000660' in [code for code, _ in similar]
```

## 🐛 트러블슈팅

### Qdrant 연결 실패

```bash
# 컨테이너 상태 확인
docker ps | grep qdrant

# 로그 확인
docker logs cybos-qdrant

# 재시작
docker-compose restart qdrant
```

### 임베딩 차원 불일치

```python
# 컬렉션 재생성
vector_db.client.delete_collection("stock_timeseries")
vector_db.initialize_collection()
```

### 메모리 부족

```python
# 배치 크기 줄이기
def batch_index_stocks_chunked(stock_codes, chunk_size=10):
    for i in range(0, len(stock_codes), chunk_size):
        chunk = stock_codes[i:i+chunk_size]
        batch_index_stocks(chunk)
```

## 📊 벤치마크

### 검색 속도

```
- 100개 종목: < 10ms
- 1,000개 종목: < 50ms
- 10,000개 종목: < 200ms
```

### 정확도

```
Recall@10 (상위 10개 정확도):
- HNSW (ef=128): 95%
- HNSW (ef=64): 90%
- Linear Search: 100% (매우 느림)
```

## 🔮 향후 계획

1. **딥러닝 임베딩**
   - Transformer 기반 시계열 임베딩
   - 자기지도 학습 (Self-supervised)

2. **다중 시간 해상도**
   - 1분봉, 5분봉, 일봉 통합

3. **온라인 학습**
   - 실시간 임베딩 업데이트

## 📚 참고 자료

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [HNSW Algorithm](https://arxiv.org/abs/1603.09320)
- [Time Series Embedding](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf)

## 🤝 기여

새로운 특징 추출 방법이나 임베딩 모델이 있다면 PR 환영합니다!

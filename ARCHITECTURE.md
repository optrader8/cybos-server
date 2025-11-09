# 시스템 아키텍처

## 📐 전체 시스템 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                        사용자 인터페이스                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Trading Dashboard (Next.js + TypeScript)         │   │
│  │  - 페어 모니터링   - 실시간 시세   - 신호 알림              │   │
│  │  - 백테스트 결과   - 포트폴리오 관리                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │ WebSocket / REST API
┌───────────────────────────────┴─────────────────────────────────┐
│                         API Gateway Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ REST API     │  │ WebSocket    │  │ GraphQL (Optional)   │  │
│  │ FastAPI      │  │ Server       │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────┴─────────────────────────────────┐
│                      서비스 레이어 (Services)                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  1. 데이터 수집 서비스 (Cybos Plus → SQLite)              │   │
│  │     - 실시간 시세 수집                                    │   │
│  │     - 과거 데이터 배치 수집 (KOSPI200)                    │   │
│  │     - 종목 마스터 데이터 동기화                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  2. 공적분 분석 엔진 (Cointegration Engine)              │   │
│  │     - Engle-Granger 검정 (2-way 페어)                    │   │
│  │     - Johansen 검정 (N-way 페어)                         │   │
│  │     - 반감기 계산                                        │   │
│  │     - 헤지 비율 산출                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  3. 벡터 DB 서비스 (Vector DB Service)                   │   │
│  │     - 시계열 임베딩 (통계/형태/주파수 특징)               │   │
│  │     - 유사 종목 검색 (Cosine Similarity)                 │   │
│  │     - 페어 후보군 필터링                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  4. 신호 생성 서비스 (Signal Generator)                  │   │
│  │     - Z-score 계산                                       │   │
│  │     - 진입/청산 신호 생성                                │   │
│  │     - 리스크 관리                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────┴─────────────────────────────────┐
│                       데이터 레이어 (Data Layer)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  SQLite      │  │  Qdrant      │  │  Redis (Optional)    │  │
│  │              │  │              │  │                      │  │
│  │ - stocks     │  │ - 시계열      │  │ - 실시간 시세 캐시    │  │
│  │ - prices     │  │   임베딩      │  │ - 신호 큐           │  │
│  │ - historical │  │ - 유사도      │  │                      │  │
│  │ - pairs ⭐   │  │   인덱스      │  │                      │  │
│  │ - coint ⭐   │  │              │  │                      │  │
│  │ - signals ⭐ │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────┴─────────────────────────────────┐
│                      데이터 소스 (Data Sources)                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Cybos Plus API (대신증권 - Windows Only)          │   │
│  │  - CpUtil.CpCybos        (연결 관리)                     │   │
│  │  - CpUtil.CpCodeMgr      (종목 코드)                     │   │
│  │  - DsCbo1.StockMst       (종목 마스터)                   │   │
│  │  - CpSysDib.StockChart   (과거 데이터)                   │   │
│  │  - DsCbo1.StockCur       (실시간 시세)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 데이터 흐름

### 1. 데이터 수집 파이프라인

```
Cybos Plus API
      │
      ├─→ 실시간 시세
      │        │
      │        ├─→ SQLite (prices 테이블)
      │        └─→ WebSocket → 프론트엔드
      │
      └─→ 과거 데이터 (일봉)
               │
               ├─→ SQLite (historical_prices 테이블)
               └─→ 공적분 분석 엔진
```

### 2. 페어 트레이딩 파이프라인

```
historical_prices (SQLite)
      │
      ├─→ 벡터 임베딩
      │        │
      │        └─→ Qdrant 저장
      │                 │
      │                 └─→ 유사 종목 검색
      │                          │
      │                          └─→ 페어 후보군 (100개 → 10개)
      │
      └─→ 공적분 분석
               │
               ├─→ Engle-Granger (2-way)
               ├─→ Johansen (N-way)
               │
               ├─→ cointegration_results (p-value < 0.05)
               │
               └─→ pairs 테이블
                        │
                        ├─→ 신호 생성 (Z-score)
                        │        │
                        │        └─→ pair_signals 테이블
                        │
                        └─→ 백테스팅
                                 │
                                 └─→ 성과 메트릭 업데이트
```

### 3. 신호 생성 파이프라인

```
실시간 시세 (prices)
      │
      ├─→ 페어별 스프레드 계산
      │        │
      │        └─→ spread = price1 - hedge_ratio * price2
      │
      ├─→ Z-score 계산
      │        │
      │        └─→ z = (spread - mean) / std
      │
      └─→ 신호 생성
               │
               ├─→ z > +2.0  → ENTRY_SHORT
               ├─→ z < -2.0  → ENTRY_LONG
               ├─→ |z| < 0.5 → EXIT
               │
               └─→ pair_signals 테이블
                        │
                        └─→ WebSocket → 프론트엔드 알림
```

## 🗄️ 데이터베이스 스키마

### SQLite 테이블 구조

```sql
-- 기존 테이블
stocks              -- 종목 정보
prices              -- 실시간 시세
historical_prices   -- 과거 시세 (OHLCV)

-- 페어 트레이딩 테이블 ⭐
pairs               -- 페어 정보 및 성과
  - pair_id (PK)
  - stock_codes (JSON)
  - cointegration_score
  - hedge_ratios (JSON)
  - sharpe_ratio
  - status

cointegration_results  -- 공적분 분석 결과
  - result_id (PK)
  - pair_id
  - p_value
  - half_life
  - method

pair_signals        -- 트레이딩 신호
  - signal_id (PK)
  - pair_id
  - signal_type
  - z_score
  - position_sizes (JSON)
```

### Qdrant 컬렉션 구조

```python
collection: "stock_timeseries"
  - vector_size: 25
  - distance: COSINE
  - payload:
      - stock_code
      - total_records
      - start_date
      - end_date
```

## 🎯 페어 조합 전략

### Phase 1: 벡터 DB 사전 필터링

```python
# KOSPI200 200개 종목 → 유사도 기반 필터링
for stock in kospi200_stocks:
    similar_stocks = vector_db.search_similar(stock, top_k=10)
    # 200개 × 10개 = 2,000개 후보 페어

# 조합 수 감소: C(200, 2) = 19,900 → 2,000개
```

### Phase 2: 공적분 검정

```python
# 2,000개 후보 페어에 대해 공적분 검정
for pair in candidate_pairs:
    result = engle_granger_test(pair)
    if result.p_value < 0.05:
        pairs.append(result)

# 유의한 페어: ~200-500개 (예상)
```

### Phase 3: 성과 기반 필터링

```python
# 백테스팅 후 상위 페어 선정
top_pairs = pairs.sort_by('sharpe_ratio').head(50)

# 최종 활성 페어: 50-100개
```

## 🔐 보안 및 인증

```
프론트엔드
    ↓ JWT Token
API Gateway
    ↓ 서비스 간 통신
서비스 레이어
    ↓ API Key
Cybos Plus
```

## 📊 모니터링 스택

```
Prometheus → Grafana
    ↓
- 서비스 헬스체크
- API 응답 시간
- 페어 성과 메트릭
- 신호 생성 빈도
```

## 🚀 확장성 고려사항

### 수평 확장 (Horizontal Scaling)

```
공적분 분석 엔진 → 멀티 인스턴스
    - 종목별 파티셔닝
    - 병렬 분석 처리

벡터 DB → Qdrant 클러스터
    - 샤딩
    - 복제

API Gateway → 로드 밸런서
    - Nginx / HAProxy
    - Auto Scaling
```

### 성능 최적화

1. **캐싱 전략**
   - Redis: 실시간 시세 캐시 (TTL: 1초)
   - 공적분 결과 캐시 (TTL: 1일)

2. **배치 처리**
   - 공적분 재분석: 매일 장 마감 후
   - 벡터 임베딩 업데이트: 주 1회

3. **인덱스 최적화**
   - SQLite: pair_id, p_value, sharpe_ratio
   - Qdrant: HNSW 그래프

## 🔄 CI/CD 파이프라인 (향후)

```
GitHub Actions
    ↓
    ├─→ Lint & Test
    ├─→ Build Docker Images
    ├─→ Deploy to Staging
    └─→ Deploy to Production
```

## 📈 확장 로드맵

1. **Phase 1** (현재)
   - 2-way 페어 트레이딩
   - KOSPI200 대상

2. **Phase 2** (3개월)
   - 3-way, 4-way 페어
   - KOSDAQ 확장

3. **Phase 3** (6개월)
   - ML 기반 신호 최적화
   - 자동 매매 시스템 연동

4. **Phase 4** (1년)
   - 해외 주식 확장
   - 멀티 에셋 페어 트레이딩

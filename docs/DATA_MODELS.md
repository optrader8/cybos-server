# 데이터 모델 문서

페어 트레이딩 시스템의 전체 데이터 모델 명세

## 📊 데이터베이스 ERD

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────┐
│   stocks    │         │ historical_prices│         │   pairs     │
├─────────────┤         ├──────────────────┤         ├─────────────┤
│ code (PK)   │────────>│ code (FK)        │<────┐   │ pair_id (PK)│
│ name        │         │ date             │     │   │ stock_codes │
│ market_kind │         │ timeframe        │     │   │ hedge_ratios│
│ ...         │         │ open_price       │     └───│ ...         │
└─────────────┘         │ close_price      │         └─────────────┘
                        │ volume           │               │
                        │ ...              │               │
                        └──────────────────┘               │
                                                           │
┌──────────────────────┐         ┌──────────────────┐    │
│ cointegration_results│         │  pair_signals    │    │
├──────────────────────┤         ├──────────────────┤    │
│ result_id (PK)       │         │ signal_id (PK)   │    │
│ pair_id (FK)         │<────────│ pair_id (FK)     │<───┘
│ p_value              │         │ signal_type      │
│ half_life            │         │ z_score          │
│ ...                  │         │ ...              │
└──────────────────────┘         └──────────────────┘
```

## 1. 기존 모델 (Cybos Plus)

### 1.1 stocks (종목 정보)

**용도:** 전체 상장 종목의 기본 정보 및 메타데이터

```python
@dataclass
class StockInfo:
    # 식별자
    code: str                    # 종목코드 (예: "005930")
    name: str                    # 종목명 (예: "삼성전자")

    # 시장 정보
    market_kind: int             # 1: KOSPI, 2: KOSDAQ
    section_kind: int            # 1: 주권, 10: ETF, ...

    # 가격 정보
    std_price: int               # 기준가
    max_price: int               # 상한가
    min_price: int               # 하한가

    # KOSPI200 정보
    kospi200_kind: int           # 0: 미포함, 1: 포함

    # 메타데이터
    created_at: str
    updated_at: str
```

**테이블 스키마:**
```sql
CREATE TABLE stocks (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    market_kind INTEGER NOT NULL,
    section_kind INTEGER NOT NULL,
    std_price INTEGER DEFAULT 0,
    max_price INTEGER DEFAULT 0,
    min_price INTEGER DEFAULT 0,
    kospi200_kind INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stocks_market ON stocks(market_kind);
CREATE INDEX idx_stocks_kospi200 ON stocks(kospi200_kind);
```

**주요 메서드:**
```python
# KOSPI200 종목만 조회
kospi200_stocks = StockTable.get_kospi200_stocks(conn)

# 시장별 조회
kospi_stocks = StockTable.get_stocks_by_market(conn, MarketKind.KOSPI)
```

### 1.2 prices (실시간 시세)

**용도:** 실시간 시세 스냅샷 저장 (틱 데이터)

```python
@dataclass
class PriceInfo:
    # 식별자
    code: str                    # 종목코드
    name: str                    # 종목명
    time: str                    # 시간 (HHMM)

    # 가격 정보
    current_price: int           # 현재가
    change: int                  # 전일대비
    change_rate: float           # 등락률

    # OHLC
    open_price: int
    high_price: int
    low_price: int

    # 거래량
    volume: int                  # 거래량 (주)
    amount: int                  # 거래대금 (천원)

    # 호가
    ask_price: int               # 매도호가
    bid_price: int               # 매수호가

    # 메타데이터
    created_at: str
```

**사용 예시:**
```python
# 최신 시세 조회
latest = PriceTable.get_latest_price(conn, '005930')
print(f"{latest.name}: {latest.current_price}원")

# 시간대별 조회
prices = PriceTable.get_prices_by_time(conn, '09:00', '15:30')
```

### 1.3 historical_prices (과거 시세)

**용도:** 일봉/주봉/월봉 OHLCV 데이터

```python
@dataclass
class HistoryInfo:
    # 식별자
    code: str                    # 종목코드
    timeframe: str               # 'D': 일봉, 'W': 주봉, 'M': 월봉
    date: str                    # 날짜 (YYYY-MM-DD)

    # OHLC
    open_price: int
    high_price: int
    low_price: int
    close_price: int

    # 거래량
    volume: int                  # 거래량
    amount: int                  # 거래대금

    # 메타데이터
    updated_at: str
```

**복합 기본 키:**
```sql
PRIMARY KEY (code, timeframe, date)
```

**사용 예시:**
```python
# 최근 1년 일봉
history = HistoryTable.get_history(
    conn, '005930', HistoryTimeframe.DAILY,
    '2023-01-01', '2023-12-31'
)

# 최신 데이터 날짜
latest_date = HistoryTable.get_latest_date(conn, '005930', HistoryTimeframe.DAILY)
```

## 2. 페어 트레이딩 모델 ⭐

### 2.1 pairs (페어 정보)

**용도:** N-way 페어의 메타데이터 및 성과 관리

```python
@dataclass
class PairInfo:
    # 식별자
    pair_id: str                 # "005930_000660" (종목코드 조합)
    pair_type: PairType          # 2-WAY, 3-WAY, 4-WAY, N-WAY
    stock_codes: List[str]       # ["005930", "000660"]

    # 상태
    status: PairStatus           # ACTIVE, INACTIVE, MONITORING

    # 공적분 정보
    cointegration_score: float   # p-value (작을수록 유의)
    half_life: float             # 반감기 (일)
    hedge_ratios: List[float]    # 헤지 비율 [1.0, 0.547]

    # 통계 정보
    correlation: float           # 상관계수
    spread_mean: float           # 스프레드 평균
    spread_std: float            # 스프레드 표준편차

    # 성과 메트릭
    sharpe_ratio: float          # 샤프 비율
    max_drawdown: float          # 최대 낙폭
    win_rate: float              # 승률
    total_trades: int            # 총 거래 횟수

    # 메타데이터
    created_at: str
    updated_at: str
    last_analyzed_at: str
```

**테이블 스키마:**
```sql
CREATE TABLE pairs (
    pair_id TEXT PRIMARY KEY,
    pair_type TEXT NOT NULL,
    stock_codes TEXT NOT NULL,  -- JSON 배열
    status TEXT DEFAULT 'MONITORING',
    cointegration_score REAL DEFAULT 0.0,
    half_life REAL DEFAULT 0.0,
    hedge_ratios TEXT,          -- JSON 배열
    sharpe_ratio REAL DEFAULT 0.0,
    max_drawdown REAL DEFAULT 0.0,
    win_rate REAL DEFAULT 0.0,
    total_trades INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_analyzed_at TEXT
);

CREATE INDEX idx_pairs_status ON pairs(status);
CREATE INDEX idx_pairs_sharpe ON pairs(sharpe_ratio);
```

**주요 메서드:**
```python
# 상위 페어 조회
top_pairs = PairTable.get_top_pairs(conn, limit=20, min_sharpe=0.5)

# 활성 페어 조회
active = PairTable.get_active_pairs(conn, pair_type=PairType.TWO_WAY)

# 특정 종목 포함 페어
pairs = PairTable.get_pairs_by_stock(conn, '005930')
```

**페어 타입별 조합 수:**
```python
# KOSPI200 (200개) 기준
2-WAY: C(200, 2) = 19,900개
3-WAY: C(200, 3) = 1,313,400개
4-WAY: C(200, 4) = 64,684,950개
```

### 2.2 cointegration_results (공적분 분석 결과)

**용도:** 공적분 검정 결과 및 통계 정보 저장

```python
@dataclass
class CointegrationResult:
    # 식별자
    result_id: str               # 결과 ID (pair_id + timestamp)
    pair_id: str                 # 페어 ID
    stock_codes: List[str]       # 종목 코드 리스트

    # 검정 결과
    method: str                  # ENGLE_GRANGER, JOHANSEN
    test_statistic: float        # 검정 통계량
    p_value: float               # p-value
    critical_values: Dict        # {"1%": -3.43, "5%": -2.86, ...}

    # 공적분 벡터
    cointegration_vector: List[float]  # [1.0, -0.547]
    hedge_ratios: List[float]          # [1.0, 0.547]
    intercept: float                    # 절편

    # 잔차 통계
    residuals_mean: float
    residuals_std: float
    half_life: float             # 반감기

    # ADF 검정
    adf_statistic: float
    adf_p_value: float

    # 데이터 정보
    sample_size: int             # 샘플 크기
    start_date: str              # 분석 시작일
    end_date: str                # 분석 종료일
    window_days: int             # 분석 기간 (252일)

    # 유의성
    significance: str            # HIGHLY_SIG, SIGNIFICANT, MARGINAL

    # 메타데이터
    created_at: str
```

**사용 예시:**
```python
# 최신 공적분 결과
latest = CointegrationTable.get_latest_result(conn, pair_id='005930_000660')

if latest.is_cointegrated(alpha=0.05):
    print(f"공적분 존재! p-value: {latest.p_value:.4f}")

# 유의한 결과만 조회
significant = CointegrationTable.get_significant_results(conn, max_p_value=0.05)
```

### 2.3 pair_signals (트레이딩 신호)

**용도:** Z-score 기반 진입/청산 신호 관리

```python
@dataclass
class PairSignal:
    # 식별자
    signal_id: str               # 신호 ID
    pair_id: str                 # 페어 ID
    stock_codes: List[str]       # 종목 코드

    # 신호 정보
    signal_type: SignalType      # ENTRY_LONG, EXIT_SHORT, ...
    status: SignalStatus         # ACTIVE, EXECUTED, CANCELLED

    # 가격 정보
    current_prices: Dict         # {"005930": 75000, "000660": 135000}
    entry_prices: Dict           # 진입가
    target_prices: Dict          # 목표가
    stop_prices: Dict            # 손절가

    # 스프레드 정보
    spread: float                # 현재 스프레드
    spread_mean: float           # 스프레드 평균
    spread_std: float            # 스프레드 표준편차
    z_score: float               # Z-score

    # 포지션 정보
    position_sizes: Dict         # {"005930": 100, "000660": -55}
    hedge_ratios: List[float]    # [1.0, 0.547]

    # 메타데이터
    confidence: float            # 신호 신뢰도 (0-1)
    expected_return: float       # 기대 수익률
    risk_level: int              # 위험도 (1-5)

    created_at: str
    executed_at: str
    expired_at: str
```

**신호 타입:**
```python
class SignalType(Enum):
    ENTRY_LONG = "ENTRY_LONG"       # z < -2.0
    ENTRY_SHORT = "ENTRY_SHORT"     # z > +2.0
    EXIT_LONG = "EXIT_LONG"         # z > -0.5
    EXIT_SHORT = "EXIT_SHORT"       # z < +0.5
    STOP_LOSS = "STOP_LOSS"         # 손절
    TAKE_PROFIT = "TAKE_PROFIT"     # 익절
```

**사용 예시:**
```python
# 활성 신호 조회
active_signals = SignalTable.get_active_signals(conn)

for signal in active_signals:
    print(f"{signal.pair_id}: z-score={signal.z_score:.2f}")

# 신호 상태 업데이트
SignalTable.update_signal_status(conn, signal_id, SignalStatus.EXECUTED)
```

## 3. Qdrant 벡터 DB

### stock_timeseries 컬렉션

**용도:** 시계열 임베딩 저장 및 유사도 검색

```python
# 벡터 설정
VectorParams(
    size=25,                     # 임베딩 차원
    distance=Distance.COSINE     # 코사인 유사도
)

# 페이로드 (메타데이터)
payload = {
    'stock_code': '005930',
    'total_records': 252,
    'start_date': '2023-01-01',
    'end_date': '2023-12-31',
    'indexed_at': '2024-01-15T10:30:00'
}
```

**임베딩 구조:**
```python
embedding = [
    # 통계 특징 (10차원)
    mean_return,
    volatility,
    skewness,
    kurtosis,
    sharpe_ratio,
    max_drawdown,
    momentum_5d,
    momentum_20d,
    momentum_60d,
    vol_ratio,

    # 형태 특징 (10차원)
    segment_1_mean,
    segment_2_mean,
    ...,
    segment_10_mean,

    # 주파수 특징 (5차원)
    fft_coeff_1,
    fft_coeff_2,
    fft_coeff_3,
    fft_coeff_4,
    fft_coeff_5,
]  # Total: 25 dimensions
```

## 4. 데이터 흐름

### 실시간 시세 → 신호 생성

```python
# 1. 실시간 시세 수신
price1 = prices['005930'].current_price  # 75,000원
price2 = prices['000660'].current_price  # 135,000원

# 2. 페어 조회
pair = PairTable.get_pair(conn, '005930_000660')

# 3. 스프레드 계산
hedge_ratio = pair.hedge_ratios[1]  # 0.547
spread = price1 - hedge_ratio * price2
# spread = 75,000 - 0.547 × 135,000 = 1,155

# 4. Z-score 계산
z_score = (spread - pair.spread_mean) / pair.spread_std
# z_score = (1,155 - 0) / 1,500 = 0.77

# 5. 신호 판단
if z_score > 2.0:
    signal_type = SignalType.ENTRY_SHORT
elif z_score < -2.0:
    signal_type = SignalType.ENTRY_LONG
```

### 히스토리 데이터 → 페어 생성

```python
# 1. 히스토리 데이터 조회 (252일)
history1 = HistoryTable.get_history(conn, '005930', ...)
history2 = HistoryTable.get_history(conn, '000660', ...)

# 2. 공적분 검정
result = engine.test_pairwise_cointegration('005930', '000660')

# 3. 유의하면 페어 생성
if result.p_value < 0.05:
    pair = PairInfo(
        pair_id='005930_000660',
        cointegration_score=result.p_value,
        hedge_ratios=result.hedge_ratios,
        half_life=result.half_life
    )
    PairTable.upsert_pair(conn, pair)
```

## 5. 데이터 관리

### 데이터 정리

```python
# 오래된 시세 데이터 삭제 (30일 이상)
PriceTable.cleanup_old_data(conn, days=30)

# 공적분 결과 아카이빙 (페어당 최신 10개만 유지)
```

### 백업 및 복원

```bash
# SQLite 백업
cp data/cybos.db data/backup/cybos_20240115.db

# 또는 Python으로
db_manager.backup_database('backup/cybos_20240115.db')
```

### 데이터베이스 최적화

```python
# VACUUM으로 공간 회수
db_manager.vacuum_database()

# 인덱스 재구축
conn.execute("REINDEX")
```

## 6. 스키마 마이그레이션

### 버전 1.0 → 1.1 예시

```python
# 새 컬럼 추가
conn.execute("""
    ALTER TABLE pairs
    ADD COLUMN last_signal_at TEXT
""")

# 인덱스 추가
conn.execute("""
    CREATE INDEX idx_pairs_last_signal
    ON pairs(last_signal_at)
""")
```

## 📚 참고

- SQLite 공식 문서: https://www.sqlite.org/docs.html
- Qdrant 문서: https://qdrant.tech/documentation/
- 데이터 정규화: https://en.wikipedia.org/wiki/Database_normalization

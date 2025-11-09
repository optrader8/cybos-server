# Cybos Trading Monorepo

공적분 기반 N-way 페어 트레이딩 시스템 모노레포

## 🏗️ 프로젝트 구조

```
cybos-server/
├── src/                        # 기존 Cybos Plus 데이터 수집 서버
│   ├── core/                   # 핵심 타입 및 인터페이스
│   ├── cybos/                  # Cybos Plus API 래핑
│   ├── database/               # SQLite 데이터 모델
│   │   └── models/
│   │       ├── stock.py        # 주식 정보
│   │       ├── price.py        # 실시간 시세
│   │       ├── history.py      # 과거 시세
│   │       ├── pair.py         # 페어 정보 ⭐
│   │       ├── cointegration.py # 공적분 결과 ⭐
│   │       └── signal.py       # 트레이딩 신호 ⭐
│   └── services/               # 비즈니스 로직
│
├── services/                   # 마이크로서비스
│   ├── cointegration-engine/   # 공적분 분석 엔진
│   │   ├── main.py
│   │   └── requirements.txt
│   └── vector-db/              # 벡터 DB 서비스
│       ├── main.py
│       └── requirements.txt
│
├── apps/                       # 프론트엔드 애플리케이션
│   └── trading-dashboard/      # 트레이딩 대시보드
│       ├── src/
│       │   ├── types/          # TypeScript 타입
│       │   ├── lib/            # WebSocket 클라이언트
│       │   └── components/     # React 컴포넌트
│       └── package.json
│
├── packages/                   # 공유 패키지 (향후 확장)
│
├── docker-compose.yml          # 인프라 구성
├── package.json                # 루트 패키지 설정
├── pnpm-workspace.yaml         # pnpm 워크스페이스
└── turbo.json                  # Turborepo 설정
```

## 🎯 핵심 기능

### 1. N-way 페어 트레이딩 지원

- **2-way**: 전통적인 페어 트레이딩 (삼성전자 ↔ SK하이닉스)
- **3-way**: 세 종목 조합 (현대차 ↔ 기아 ↔ 현대모비스)
- **4-way+**: 다중 종목 포트폴리오 페어

### 2. 데이터 모델 설계

#### PairInfo (페어 정보)
```python
@dataclass
class PairInfo:
    pair_id: str                    # "005930_000660"
    pair_type: PairType             # 2-WAY, 3-WAY, ...
    stock_codes: List[str]          # ["005930", "000660"]

    # 공적분 정보
    cointegration_score: float      # p-value
    half_life: float                # 반감기 (일)
    hedge_ratios: List[float]       # 헤지 비율

    # 성과 정보
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
```

#### CointegrationResult (공적분 분석)
```python
@dataclass
class CointegrationResult:
    pair_id: str
    method: CointegrationMethod     # ENGLE_GRANGER, JOHANSEN
    p_value: float                  # 통계적 유의성
    cointegration_vector: List[float]
    hedge_ratios: List[float]
    half_life: float
```

#### PairSignal (트레이딩 신호)
```python
@dataclass
class PairSignal:
    signal_id: str
    pair_id: str
    signal_type: SignalType         # ENTRY_LONG, EXIT_SHORT, ...

    # 스프레드 정보
    spread: float
    z_score: float                  # Z-score 기반 신호

    # 포지션 정보
    position_sizes: Dict[str, int]
    hedge_ratios: List[float]
```

### 3. 공적분 분석 엔진

```python
from services.cointegration_engine.main import CointegrationEngine

engine = CointegrationEngine()

# KOSPI200 종목에서 공적분 페어 찾기
results = engine.find_cointegrated_pairs(
    stock_codes=['005930', '000660', '035420', ...],
    max_p_value=0.05,
    window_days=252
)

# 페어 생성
pairs = engine.create_pairs_from_cointegration()
```

### 4. 벡터 DB 유사도 검색

```python
from services.vector_db.main import VectorDBService

vector_db = VectorDBService()

# 시계열 데이터 인덱싱
vector_db.batch_index_stocks(stock_codes)

# 유사한 주식 검색
similar = vector_db.search_similar_stocks('005930', top_k=10)
# [('000660', 0.95), ('051910', 0.89), ...]
```

### 5. 실시간 시세 WebSocket

```typescript
import { getPriceWebSocket } from '@/lib/websocket';

const ws = getPriceWebSocket();

// 종목 구독
ws.subscribe('005930', (price) => {
  console.log(`삼성전자: ${price.current_price}원`);
});
```

## 🚀 빠른 시작

### 1. 인프라 실행

```bash
# Docker 컨테이너 실행 (Qdrant, Redis, PostgreSQL 등)
docker-compose up -d

# Qdrant: http://localhost:6333
# Grafana: http://localhost:3001 (admin/admin)
# Prometheus: http://localhost:9090
```

### 2. 데이터베이스 초기화

```bash
# 페어 트레이딩 테이블 포함 초기화
cd cybos-server
python -c "from src.database.connection import initialize_database; initialize_database()"
```

### 3. 서비스 실행

```bash
# 공적분 분석 엔진
cd services/cointegration-engine
pip install -r requirements.txt
python main.py

# 벡터 DB 서비스
cd services/vector-db
pip install -r requirements.txt
python main.py

# 프론트엔드 대시보드
cd apps/trading-dashboard
pnpm install
pnpm dev
# http://localhost:3000
```

## 📊 데이터 흐름

```
1. Cybos Plus → SQLite (historical_prices)
2. SQLite → 공적분 분석 → pairs, cointegration_results
3. SQLite → 벡터 임베딩 → Qdrant
4. 실시간 시세 → WebSocket → 프론트엔드
5. 신호 생성 → pair_signals → 트레이딩 실행
```

## 🔄 페어 조합 최적화

KOSPI200 (200개 종목) 기준:
- **2-way**: C(200, 2) = **19,900개** 조합
- **3-way**: C(200, 3) = **1,313,400개** 조합 (벡터 DB로 사전 필터링)
- **4-way+**: 유사도 기반 후보군 선정 후 분석

### 효율화 전략

1. **벡터 DB 사전 필터링**
   - 유사한 시계열 패턴을 가진 종목만 조합
   - 상위 10% 후보군으로 축소

2. **증분 분석**
   - 기존 페어 결과 재활용
   - 변동성 높은 페어만 재분석

3. **병렬 처리**
   - 멀티프로세싱으로 조합 병렬 분석

## 🔧 주요 알고리즘

### 공적분 검정
- **Engle-Granger** (2-way 페어)
- **Johansen** (N-way 페어)

### Z-score 계산
```python
spread = price1 - hedge_ratio * price2
z_score = (spread - spread_mean) / spread_std

# 진입/청산 신호
if z_score > 2.0:   # 매도 신호
if z_score < -2.0:  # 매수 신호
if abs(z_score) < 0.5:  # 청산 신호
```

### 반감기 계산
```python
# AR(1) 모델
residuals[t] = λ * residuals[t-1] + ε
half_life = -log(2) / log(λ)
```

## 📈 성능 메트릭

- **샤프 비율** (Sharpe Ratio): 위험 대비 수익
- **최대 낙폭** (Max Drawdown): 최대 손실
- **승률** (Win Rate): 수익 거래 비율
- **반감기** (Half-life): 스프레드 회귀 속도

## ⚠️ 주의사항

1. **Windows 32bit Python 필수** (Cybos Plus 제약)
2. **Cybos Plus HTS 로그인 필수**
3. **API 호출 제한 준수** (분당 200회)
4. **충분한 히스토리 데이터 필요** (최소 252일)

## 📚 참고 자료

- [Cointegration Testing](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.coint.html)
- [Pairs Trading Strategy](https://en.wikipedia.org/wiki/Pairs_trade)
- [Qdrant Vector Database](https://qdrant.tech/)

## 🤝 기여

이슈 및 PR은 언제나 환영합니다!

## 📄 라이선스

MIT License

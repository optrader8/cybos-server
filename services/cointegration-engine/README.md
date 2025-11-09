# 공적분 분석 엔진 (Cointegration Engine)

N-way 페어 트레이딩을 위한 공적분 분석 엔진

## 🎯 목적

- KOSPI200 종목 간 공적분 관계 탐색
- 2-way, 3-way, N-way 페어 자동 발견
- 통계적으로 유의한 페어만 선별 (p < 0.05)

## 📊 공적분이란?

두 개 이상의 비정상(Non-stationary) 시계열이 선형 결합으로 정상(Stationary) 시계열을 만들 수 있을 때, **공적분 관계**가 있다고 합니다.

### 예시: 삼성전자 vs SK하이닉스

```
삼성전자 가격: 비정상 시계열 (계속 오르내림)
SK하이닉스 가격: 비정상 시계열

스프레드 = 삼성전자 - β × SK하이닉스
→ 스프레드가 평균 회귀(Mean Reversion) → 공적분!
```

## 🔬 검정 방법

### 1. Engle-Granger 검정 (2-way 페어)

```python
# 1단계: OLS 회귀로 헤지 비율 추정
y = α + β × x + ε

# 2단계: 잔차의 단위근 검정 (ADF Test)
ADF(residuals) → p-value

# p-value < 0.05 → 공적분 관계 존재
```

**장점:**
- 빠르고 간단
- 2개 종목에 최적화

**단점:**
- 3개 이상 종목은 부정확

### 2. Johansen 검정 (N-way 페어)

```python
# 벡터 자기회귀(VAR) 모델 기반
# 공적분 벡터 개수 추정

# 추적 통계량(Trace Statistic)
# 최대 고유값 통계량(Max Eigenvalue)
```

**장점:**
- 3개 이상 종목 정확
- 다중 공적분 벡터 식별

**단점:**
- 계산 복잡도 높음
- 해석 어려움

## 🚀 사용법

### 기본 실행

```bash
cd services/cointegration-engine
pip install -r requirements.txt
python main.py
```

### Python API

```python
from main import CointegrationEngine

engine = CointegrationEngine(db_path="data/cybos.db")

# 2개 종목 공적분 검정
result = engine.test_pairwise_cointegration('005930', '000660')

if result and result.is_cointegrated(alpha=0.05):
    print(f"공적분 발견! p-value: {result.p_value:.4f}")
    print(f"헤지 비율: {result.hedge_ratios}")
    print(f"반감기: {result.half_life:.2f}일")

# 전체 종목 페어 검색
results = engine.find_cointegrated_pairs(
    stock_codes=['005930', '000660', '035420', ...],
    max_p_value=0.05,
    window_days=252
)

# 페어 생성
pairs = engine.create_pairs_from_cointegration()
```

## 📈 출력 결과

### CointegrationResult

```python
@dataclass
class CointegrationResult:
    pair_id: str                    # "005930_000660"
    p_value: float                  # 0.0234 (< 0.05 유의함)

    # 헤지 비율
    hedge_ratios: [1.0, 0.547]      # [삼성전자, SK하이닉스]

    # 반감기
    half_life: float                # 15.3일 (스프레드 회귀 속도)

    # 잔차 통계
    residuals_mean: 0.0
    residuals_std: 1523.4

    # ADF 검정
    adf_p_value: 0.0123             # 잔차가 정상 시계열
```

### PairInfo

```python
@dataclass
class PairInfo:
    pair_id: "005930_000660"
    stock_codes: ["005930", "000660"]

    cointegration_score: 0.0234     # p-value
    half_life: 15.3                 # 반감기

    # 성과 메트릭 (백테스팅 후)
    sharpe_ratio: 1.25
    max_drawdown: -0.15
    win_rate: 0.62
```

## 🔧 주요 파라미터

### window_days (분석 기간)

```python
window_days=252  # 1년 (기본값, 권장)
window_days=504  # 2년 (더 안정적)
window_days=126  # 6개월 (빠른 변화 감지)
```

**권장:** 252일 (1년)
- 충분한 데이터 포인트
- 최근 시장 환경 반영

### max_p_value (유의 수준)

```python
max_p_value=0.05  # 5% (기본값)
max_p_value=0.01  # 1% (더 엄격)
max_p_value=0.10  # 10% (더 느슨)
```

**권장:** 0.05 (5%)
- 통계적 표준
- 과적합 방지

## 📊 반감기 (Half-life)

스프레드가 평균으로 돌아가는 데 걸리는 시간

### 계산 방법

```python
# AR(1) 모델
residuals[t] = λ × residuals[t-1] + ε

# 반감기
half_life = -log(2) / log(λ)
```

### 해석

```
half_life = 5일   → 매우 빠른 회귀 (고빈도 트레이딩)
half_life = 15일  → 적당한 회귀 (일반 트레이딩)
half_life = 30일  → 느린 회귀 (장기 포지션)
half_life = 100일 → 너무 느림 (페어 부적합)
```

**권장 범위:** 5-30일

## ⚡ 성능 최적화

### 배치 처리

```python
# 나쁜 예 (순차 처리)
for code1, code2 in combinations(codes, 2):
    result = engine.test_pairwise_cointegration(code1, code2)

# 좋은 예 (병렬 처리)
from multiprocessing import Pool

def analyze_pair(pair):
    return engine.test_pairwise_cointegration(*pair)

with Pool(8) as pool:
    results = pool.map(analyze_pair, combinations(codes, 2))
```

### 증분 분석

```python
# 기존 결과 재사용
with get_connection_context() as conn:
    existing = CointegrationTable.get_latest_result(conn, pair_id)

    # 최근 분석이면 스킵
    if existing and (now - existing.created_at).days < 7:
        return existing
```

## 🎯 페어 선정 기준

### 1단계: 통계적 유의성

```python
p_value < 0.05  # 공적분 존재
```

### 2단계: 실용성

```python
5 <= half_life <= 30  # 적당한 회귀 속도
adf_p_value < 0.05    # 잔차 정상성
```

### 3단계: 안정성

```python
residuals_std < threshold  # 변동성 관리
correlation > 0.6          # 기본 상관관계
```

## 📈 백테스팅 연동

```python
# 공적분 결과로 백테스팅
from services.backtesting import BacktestEngine

backtest = BacktestEngine()

for result in coint_results:
    if result.is_cointegrated():
        perf = backtest.run(result.pair_id)

        # PairInfo 업데이트
        pair.sharpe_ratio = perf.sharpe
        pair.max_drawdown = perf.max_dd
        pair.win_rate = perf.win_rate
```

## 🔬 고급 기능 (향후)

### Johansen 검정 (3-way+)

```python
# 3개 종목 공적분
result = engine.test_johansen_cointegration(
    stock_codes=['005930', '000660', '051910'],
    window_days=252
)
```

### Rolling Window 분석

```python
# 시간에 따른 공적분 강도 변화
rolling_results = engine.rolling_cointegration(
    code1='005930',
    code2='000660',
    window=252,
    step=20
)
```

### 조건부 공적분

```python
# 시장 상태별 공적분
result = engine.conditional_cointegration(
    codes=['005930', '000660'],
    condition='bull_market'  # 상승장에서만
)
```

## 📊 시각화

```python
import matplotlib.pyplot as plt

# 스프레드 시각화
def plot_spread(result: CointegrationResult):
    prices1 = get_prices(result.stock_codes[0])
    prices2 = get_prices(result.stock_codes[1])

    spread = prices1 - result.hedge_ratios[1] * prices2

    plt.figure(figsize=(12, 6))
    plt.plot(spread)
    plt.axhline(spread.mean(), color='r', linestyle='--')
    plt.axhline(spread.mean() + 2*spread.std(), color='orange')
    plt.axhline(spread.mean() - 2*spread.std(), color='orange')
    plt.title(f"Spread: {result.pair_id}")
    plt.show()
```

## 🐛 디버깅

### 데이터 부족 에러

```python
# 최소 30개 데이터 포인트 필요
if len(prices) < 30:
    print("데이터 부족: 히스토리 데이터 수집 필요")
```

### 공적분 없음

```python
# 모든 페어가 유의하지 않은 경우
# 1. 종목 선택 재검토 (관련 업종)
# 2. 분석 기간 조정 (window_days)
# 3. 벡터 DB 사전 필터링 사용
```

## 📚 참고 문헌

- Engle, R. F., & Granger, C. W. J. (1987). "Co-integration and error correction"
- Johansen, S. (1991). "Estimation and hypothesis testing of cointegration vectors"
- [Statsmodels Documentation](https://www.statsmodels.org/stable/vector_ar.html)

## 🤝 기여

새로운 검정 방법이나 최적화 아이디어가 있다면 PR 환영합니다!

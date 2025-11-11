# 🚀 Cybos Plus REST API Server with Pair Trading

> **극단적 모듈화 & 마이크로 아키텍처** 기반의 국내 주식 시세 및 페어 트레이딩 서버

**실시간 국내 주식 시세 + 페어 트레이딩 + 알고리즘 트레이딩 API 서버**

## ✨ 주요 기능

### 📊 실시간 시세 데이터
- Cybos Plus를 통한 실시간 국내 주식 시세 수집
- SQLite 데이터베이스 저장 및 관리
- REST API를 통한 시세 조회
- WebSocket을 통한 실시간 스트리밍

### 🔄 페어 트레이딩
- N-way (2개 이상) 페어 트레이딩 지원
- 공적분(Cointegration) 분석 (Engle-Granger, Johansen)
- Z-score 기반 신호 생성
- 자동 스프레드 모니터링

### 📈 알고리즘 트레이딩
- 백테스트 엔진 (수수료, 슬리피지 포함)
- 포트폴리오 관리
- 성과 분석 (Sharpe, Sortino, Calmar Ratio 등)
- 리스크 관리 (VaR, 포지션 한도)

### 🔌 API 서버
- 40+ REST API 엔드포인트
- WebSocket 실시간 스트리밍 (시세, 신호)
- OpenAPI (Swagger) 문서
- CORS 지원

## ⚠️ 핵심 제약사항

- **Windows 32-bit Python 3.9** 전용
- **pywin32** 필수
- **Cybos Plus HTS 로그인** 필요
- **파일당 최대 300라인** 제한 (극단적 모듈화)

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd cybos-server

# 가상환경 생성 (32-bit Python 3.9)
python -m venv venv
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
copy .env.example .env
# .env 파일을 수정하여 설정 조정
```

### 2. 데이터베이스 초기화

```bash
# 데이터베이스 테이블 생성
python scripts/init_database.py

# 종목 코드 동기화
python scripts/sync_stock_codes.py
```

### 3. 서버 실행

```bash
# FastAPI 서버 시작
python src/main.py
```

서버가 시작되면:
- API 문서: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health
- WebSocket: ws://localhost:8000/ws/prices

## 📚 API 엔드포인트

### Health Check
- `GET /api/health` - 헬스 체크
- `GET /api/health/detailed` - 상세 헬스 체크

### 주식 정보
- `GET /api/stocks` - 주식 목록 조회
- `GET /api/stocks/{code}` - 특정 주식 조회
- `POST /api/stocks/sync` - 주식 정보 동기화

### 시세 데이터
- `GET /api/prices/{code}` - 현재가 조회
- `GET /api/prices/{code}/history` - 과거 시세 조회
- `POST /api/prices/fetch` - 시세 수집 실행

### 페어 트레이딩
- `GET /api/pairs` - 페어 목록 조회
- `GET /api/pairs/{pair_id}` - 페어 상세 조회
- `POST /api/pairs` - 페어 생성
- `GET /api/pairs/top/performers` - 상위 성과 페어
- `GET /api/pairs/search/by-stock` - 종목별 페어 검색

### 트레이딩 신호
- `GET /api/signals` - 신호 목록 조회
- `GET /api/signals/{signal_id}` - 신호 상세 조회
- `GET /api/signals/active/list` - 활성 신호 목록
- `POST /api/signals` - 신호 생성
- `PUT /api/signals/{signal_id}` - 신호 업데이트
- `POST /api/signals/execute` - 신호 실행
- `GET /api/signals/stats/summary` - 신호 통계

### 공적분 분석
- `GET /api/cointegration/{pair_id}` - 최신 공적분 결과
- `GET /api/cointegration/{pair_id}/history` - 공적분 이력
- `GET /api/cointegration/significant/pairs` - 유의한 페어
- `POST /api/cointegration/analyze` - 공적분 분석 실행
- `GET /api/cointegration/summary/stats` - 공적분 요약

### 알고리즘 트레이딩
- `POST /api/trading/backtest` - 백테스트 실행
- `GET /api/trading/portfolio` - 포트폴리오 조회
- `POST /api/trading/execute` - 거래 실행
- `GET /api/trading/performance` - 성과 분석
- `GET /api/trading/signals/active` - 활성 트레이딩 신호
- `GET /api/trading/pairs/tradeable` - 거래 가능 페어
- `GET /api/trading/risk/exposure` - 리스크 노출도

### WebSocket 스트리밍
- `ws://localhost:8000/ws/prices` - 실시간 시세 스트리밍
- `ws://localhost:8000/ws/signals` - 실시간 신호 스트리밍

## 🏗️ 프로젝트 구조

```
cybos-server/
├── src/
│   ├── core/                 # 핵심 추상화 레이어
│   ├── cybos/                # Cybos Plus 연동
│   │   ├── connection/       # 연결 관리
│   │   ├── codes/            # 종목 코드
│   │   └── price/            # 시세 데이터
│   ├── database/             # 데이터베이스 레이어
│   │   ├── models/           # 데이터 모델
│   │   │   ├── stock.py      # 주식 정보
│   │   │   ├── price.py      # 시세 데이터
│   │   │   ├── pair.py       # 페어 정보
│   │   │   ├── signal.py     # 트레이딩 신호
│   │   │   └── cointegration.py  # 공적분 결과
│   │   └── connection.py     # DB 연결
│   ├── api/                  # REST API 레이어
│   │   ├── routes/           # API 라우터
│   │   ├── schemas/          # Pydantic 스키마
│   │   └── middleware/       # 미들웨어
│   ├── services/             # 백그라운드 서비스
│   │   ├── backtest_engine/  # 백테스트 엔진
│   │   │   ├── engine.py     # 메인 엔진
│   │   │   ├── portfolio.py  # 포트폴리오 관리
│   │   │   ├── simulator.py  # 거래 시뮬레이터
│   │   │   └── metrics.py    # 성과 지표
│   │   └── signal_generator/ # 신호 생성기
│   │       ├── generator.py  # 신호 생성
│   │       ├── analyzer.py   # 스프레드 분석
│   │       └── monitor.py    # 모니터링
│   └── main.py               # 서버 진입점
├── scripts/                  # 유틸리티 스크립트
│   ├── init_database.py      # DB 초기화
│   └── sync_stock_codes.py   # 종목 동기화
├── data/                     # 데이터 저장소
│   └── cybos.db             # SQLite 데이터베이스
├── requirements.txt          # Python 의존성
├── .env.example             # 환경 변수 템플릿
└── README.md                # 프로젝트 문서
```

## 🛠️ 설정

### 환경 변수

`.env` 파일에서 다음 설정을 조정할 수 있습니다:

#### 기본 설정
```env
DATABASE_PATH=./data/cybos.db
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

#### 페어 트레이딩 설정
```env
# 공적분 분석
COINTEGRATION_METHOD=johansen
COINTEGRATION_WINDOW_DAYS=252
COINTEGRATION_MAX_P_VALUE=0.05

# 페어 선택
PAIR_MIN_CORRELATION=0.7
PAIR_MIN_TRADING_VOLUME=100000

# 신호 생성
SIGNAL_ENTRY_Z_SCORE=2.0
SIGNAL_EXIT_Z_SCORE=0.5
SIGNAL_MIN_CONFIDENCE=0.6
SIGNAL_LOOKBACK_PERIOD=60
```

#### 백테스트 설정
```env
BACKTEST_INITIAL_CAPITAL=100000000
BACKTEST_COMMISSION_RATE=0.0015
BACKTEST_SLIPPAGE_RATE=0.001
BACKTEST_RISK_FREE_RATE=0.03
```

#### 리스크 관리
```env
RISK_MAX_PORTFOLIO_EXPOSURE=0.8
RISK_MAX_PAIR_EXPOSURE=0.2
RISK_MAX_DRAWDOWN_PCT=0.15
RISK_VAR_CONFIDENCE=0.95
```

#### 백그라운드 서비스
```env
# 신호 생성기 활성화
SIGNAL_GENERATOR_ENABLED=true
SIGNAL_GENERATOR_INTERVAL=300
SIGNAL_GENERATOR_MAX_SIGNALS=100
```

## 📖 사용 예제

### Python API 클라이언트

```python
import requests

# 현재가 조회
response = requests.get("http://localhost:8000/api/prices/005930")
print(response.json())

# 페어 목록 조회
response = requests.get("http://localhost:8000/api/pairs")
pairs = response.json()

# 활성 신호 조회
response = requests.get("http://localhost:8000/api/signals/active/list")
signals = response.json()

# 백테스트 실행
backtest_request = {
    "pair_ids": ["005930_000660"],
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "initial_capital": 100000000
}
response = requests.post(
    "http://localhost:8000/api/trading/backtest",
    json=backtest_request
)
results = response.json()
```

### WebSocket 클라이언트

```python
import asyncio
import websockets
import json

async def stream_prices():
    uri = "ws://localhost:8000/ws/prices"
    async with websockets.connect(uri) as websocket:
        # 종목 구독
        await websocket.send(json.dumps({
            "action": "subscribe",
            "codes": ["005930", "000660"]
        }))

        # 실시간 수신
        async for message in websocket:
            data = json.loads(message)
            print(f"Price update: {data}")

asyncio.run(stream_prices())
```

## 🧪 테스트

```bash
# 단위 테스트
pytest tests/

# 커버리지 리포트
pytest --cov=src tests/

# 특정 테스트만 실행
pytest tests/test_backtest_engine.py
```

## 📊 성과 지표

백테스트 엔진은 다음 성과 지표를 제공합니다:

- **수익률**: 총 수익률, 연환산 수익률
- **위험 조정 지표**: Sharpe Ratio, Sortino Ratio, Calmar Ratio
- **위험 지표**: 최대 낙폭 (MDD), 변동성 (Volatility)
- **거래 통계**: 승률, 손익비, 평균 수익/손실, 평균 보유 기간

## 🔒 보안

- API Key 인증 지원 (`X-API-Key` 헤더)
- JWT 토큰 지원 (선택적)
- CORS 설정으로 허용된 도메인만 접근
- 요청 속도 제한

## 🚨 문제 해결

### "Failed to initialize COM objects" 오류
- Cybos Plus가 설치되고 로그인되어 있는지 확인
- 32-bit Python 환경에서 실행 중인지 확인

### "Database is locked" 오류
- 다른 프로세스가 데이터베이스를 사용 중인지 확인
- 서버를 중지하고 다시 시작

### WebSocket 연결 실패
- 방화벽 설정 확인
- `WEBSOCKET_ENABLED=true` 환경 변수 확인

## 📝 라이센스

MIT License

## 🤝 기여

이슈와 풀 리퀘스트를 환영합니다!

## 📧 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.

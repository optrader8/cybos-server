# 빠른 시작 가이드

공적분 기반 N-way 페어 트레이딩 시스템을 10분 안에 실행하는 방법

## 📋 사전 요구사항

### Windows 환경 (Cybos Plus 서버)
- ✅ Windows 10/11 (32bit 또는 64bit)
- ✅ Python 3.9 32bit
- ✅ Cybos Plus HTS 설치 및 로그인
- ✅ 대신증권 계정

### 개발 환경 (Linux/Mac/Windows)
- ✅ Docker & Docker Compose
- ✅ Python 3.9+
- ✅ Node.js 18+
- ✅ pnpm 8+

## 🚀 5분 빠른 시작

### Step 1: 저장소 클론

```bash
git clone https://github.com/optrader8/cybos-server.git
cd cybos-server
```

### Step 2: 인프라 실행 (Docker)

```bash
# Qdrant, Redis, PostgreSQL 등 실행
docker-compose up -d

# 확인
docker-compose ps
```

**실행되는 서비스:**
- Qdrant: http://localhost:6333
- Grafana: http://localhost:3001 (admin/admin)
- Prometheus: http://localhost:9090
- Redis: localhost:6379
- PostgreSQL: localhost:5432

### Step 3: 데이터베이스 초기화

```bash
# Windows (Cybos Plus 서버)
python -c "from src.database.connection import initialize_database; initialize_database()"

# 확인
python -c "from src.database.connection import get_db_info; print(get_db_info())"
```

**생성되는 테이블:**
- `stocks` - 종목 정보
- `prices` - 실시간 시세
- `historical_prices` - 과거 데이터
- `pairs` - 페어 정보 ⭐
- `cointegration_results` - 공적분 분석 결과 ⭐
- `pair_signals` - 트레이딩 신호 ⭐

### Step 4: 히스토리 데이터 수집 (Windows)

```bash
# KOSPI200 일봉 데이터 수집 (3-7시간 소요)
python kospi200_daily_batch.py

# 또는 테스트용 소량 데이터
python kospi200_daily_batch.py --dry-run
```

### Step 5: 공적분 분석 실행

```bash
cd services/cointegration-engine

# 의존성 설치
pip install -r requirements.txt

# 분석 실행 (KOSPI200 50개 종목 테스트)
python main.py
```

**예상 결과:**
```
🔍 50개 종목에서 1,225개 페어 조합 분석 중...
✅ 45개 공적분 페어 발견 (p < 0.05)
📊 45개 페어 생성 완료
```

### Step 6: 벡터 DB 인덱싱

```bash
cd services/vector-db

# 의존성 설치
pip install -r requirements.txt

# 인덱싱 실행
python main.py
```

**예상 결과:**
```
🔄 50개 종목 인덱싱 시작...
✅ 50개 종목 인덱싱 완료

🔍 '005930' 와 유사한 종목 검색:
  1. 000660 (유사도: 0.8945)
  2. 051910 (유사도: 0.8523)
```

### Step 7: 프론트엔드 대시보드 실행

```bash
cd apps/trading-dashboard

# 의존성 설치
pnpm install

# 개발 서버 실행
pnpm dev
```

**접속:** http://localhost:3000

## 📊 데이터 확인

### SQLite 데이터 확인

```python
from src.database.connection import get_connection_context
from src.database.models.pair import PairTable

# 상위 페어 조회
with get_connection_context() as conn:
    top_pairs = PairTable.get_top_pairs(conn, limit=10)

    for pair in top_pairs:
        print(f"{pair.pair_id}: Sharpe={pair.sharpe_ratio:.2f}, p={pair.cointegration_score:.4f}")
```

### Qdrant 데이터 확인

```python
from services.vector_db.main import VectorDBService

vector_db = VectorDBService()

# 유사 종목 검색
similar = vector_db.search_similar_stocks('005930', top_k=5)
print(similar)
```

## 🔧 트러블슈팅

### Cybos Plus 연결 실패

```bash
# 연결 상태 확인
python -c "from src.cybos.connection.status import get_detailed_status; print(get_detailed_status())"
```

**해결 방법:**
1. Cybos Plus HTS 로그인 확인
2. COM 객체 등록: `fix_com_registration.bat` 실행
3. 32bit Python 확인: `python -c "import sys; print(sys.maxsize <= 2**32)"`

### Qdrant 연결 실패

```bash
# Qdrant 컨테이너 상태 확인
docker-compose ps qdrant

# 로그 확인
docker-compose logs qdrant

# 재시작
docker-compose restart qdrant
```

### 공적분 분석 데이터 부족

```bash
# 히스토리 데이터 확인
python -c "
from src.database.connection import get_connection_context
from src.database.models.history import HistoryTable, HistoryTimeframe

with get_connection_context() as conn:
    latest = HistoryTable.get_latest_date(conn, '005930', HistoryTimeframe.DAILY)
    print(f'삼성전자 최신 데이터: {latest}')
"
```

## 📈 다음 단계

### 1. 실전 데이터 수집

```bash
# KOSPI200 전체 데이터 수집 (3-7시간)
python kospi200_daily_batch.py --min-delay 0.2 --max-delay 1.0
```

### 2. 전체 종목 분석

```python
# services/cointegration-engine/main.py 수정
stock_codes = [stock.code for stock in kospi200_stocks]  # 전체 200개
```

### 3. 실시간 신호 생성 구현

```python
# services/signal-generator/ 생성 (향후)
```

### 4. 프론트엔드 UI 완성

```bash
cd apps/trading-dashboard
# 컴포넌트 개발
```

## 🎯 개발 워크플로우

### 1. 새로운 페어 분석

```bash
# 1. 히스토리 데이터 수집
python kospi200_daily_batch.py

# 2. 공적분 분석
cd services/cointegration-engine && python main.py

# 3. 결과 확인
python -c "from src.database.models.pair import PairTable; ..."
```

### 2. 백테스팅

```python
# 페어 성과 분석 (향후 구현)
from services.backtesting import BacktestEngine

engine = BacktestEngine()
results = engine.run_backtest(pair_id='005930_000660')
```

### 3. 실시간 모니터링

```bash
# Grafana 대시보드
open http://localhost:3001

# 프론트엔드 대시보드
open http://localhost:3000
```

## 💡 유용한 스크립트

### 데이터베이스 통계

```bash
python -c "
from src.database.connection import get_db_info
import json
print(json.dumps(get_db_info(), indent=2))
"
```

### 페어 성과 요약

```python
from src.database.connection import get_connection_context
from src.database.models.pair import PairTable

with get_connection_context() as conn:
    stats = PairTable.count_pairs_by_type(conn)
    print(f"페어 통계: {stats}")

    top_pairs = PairTable.get_top_pairs(conn, limit=5, min_sharpe=0.5)
    for pair in top_pairs:
        print(f"{pair.pair_id}: Sharpe={pair.sharpe_ratio:.2f}")
```

### 실시간 시세 스트림

```python
from src.cybos.price.realtime import RealtimePrice

rt = RealtimePrice()
rt.subscribe('005930', lambda price: print(f"삼성전자: {price.current_price}"))
```

## 📚 추가 문서

- [시스템 아키텍처](ARCHITECTURE.md)
- [모노레포 가이드](README_MONOREPO.md)
- [공적분 분석 가이드](services/cointegration-engine/README.md)
- [벡터 DB 가이드](services/vector-db/README.md)
- [API 문서](docs/API.md) (향후)

## ❓ FAQ

**Q: Windows 없이 개발 가능한가요?**
A: 데이터 수집은 Windows 필수이지만, 분석/프론트엔드는 Linux/Mac 가능

**Q: 얼마나 많은 페어를 분석할 수 있나요?**
A: 벡터 DB 필터링으로 수백만 조합도 가능 (C(200,3) = 130만개)

**Q: 실시간 매매 가능한가요?**
A: 신호 생성까지 구현됨, 주문 실행은 추가 개발 필요

**Q: 다른 증권사 API는?**
A: 현재 Cybos Plus만 지원, 추후 확장 가능

## 🆘 도움말

- 이슈: https://github.com/optrader8/cybos-server/issues
- 위키: https://github.com/optrader8/cybos-server/wiki
- 디스코드: (추후 개설)

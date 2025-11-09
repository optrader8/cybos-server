# 📚 문서 인덱스

전체 프로젝트 문서 가이드

## 🚀 시작하기

처음 시작하는 분들을 위한 문서:

1. **[빠른 시작 가이드](QUICKSTART.md)** ⭐
   - 10분 안에 시스템 실행
   - Docker 환경 구성
   - 기본 테스트 실행

2. **[README](README.md)**
   - 프로젝트 개요
   - 주요 기능 소개
   - 기본 사용법

3. **[모노레포 가이드](README_MONOREPO.md)** ⭐
   - 전체 프로젝트 구조
   - N-way 페어 트레이딩 설명
   - 실행 방법 상세

## 🏗️ 아키텍처

시스템 구조를 이해하기 위한 문서:

1. **[시스템 아키텍처](ARCHITECTURE.md)** ⭐
   - 전체 시스템 구조도
   - 데이터 흐름
   - 서비스 레이어 설명
   - 확장성 고려사항

2. **[데이터 모델](docs/DATA_MODELS.md)** ⭐
   - ERD (Entity Relationship Diagram)
   - 테이블 스키마
   - 데이터 흐름
   - 벡터 DB 구조

3. **[PRD (Product Requirements Document)](PRD.md)**
   - 제품 요구사항
   - 기능 명세
   - 비기능 요구사항

## 🔧 서비스별 문서

### Cybos Plus 데이터 수집 (src/)

**기본 문서:**
- [기존 README](README.md) - Cybos Plus 서버 설명
- [KOSPI200 배치 가이드](KOSPI200_BATCH_README.md) - 일봉 데이터 수집
- [KOSPI200 배치 개선사항](KOSPI200_BATCH_IMPROVEMENTS.md)

**Cybos Plus API 문서 (docs/):**
- [CpCybos](docs/CpCybos.md) - 연결 관리
- [CpCodeMgr](docs/CpCodeMgr.md) - 종목 코드 관리
- [CpStockCode](docs/CpStockCode.md) - 종목 정보
- [StockMst](docs/CpDib/StockMst.md) - 종목 마스터 데이터
- [StockMst2](docs/CpDib/StockMst2.md)
- [StockMstM](docs/CpDib/StockMstM.md)

### 공적분 분석 엔진 (services/cointegration-engine/)

**[공적분 엔진 README](services/cointegration-engine/README.md)** ⭐
- 공적분이란?
- Engle-Granger vs Johansen 검정
- 반감기 계산
- 사용법 및 예제
- 성능 최적화

**주요 내용:**
```python
# 2-way 페어 분석
result = engine.test_pairwise_cointegration('005930', '000660')

# 전체 종목 페어 검색
results = engine.find_cointegrated_pairs(kospi200_codes)
```

### 벡터 DB 서비스 (services/vector-db/)

**[벡터 DB README](services/vector-db/README.md)** ⭐
- 시계열 임베딩 기법
- 조합 폭발 문제 해결
- Qdrant 사용법
- 유사도 검색

**주요 내용:**
```python
# 유사 종목 검색
similar = vector_db.search_similar_stocks('005930', top_k=10)

# 페어 후보 필터링: 19,900개 → 2,000개
```

### 프론트엔드 대시보드 (apps/trading-dashboard/)

**구성 요소:**
- `src/types/pair.ts` - TypeScript 타입 정의
- `src/lib/websocket.ts` - WebSocket 클라이언트
- (향후) 컴포넌트 문서

## 📖 개념 가이드

### 페어 트레이딩

**기본 개념:**
1. **공적분 (Cointegration)**
   - 두 시계열의 장기 균형 관계
   - 스프레드의 평균 회귀 성질

2. **헤지 비율 (Hedge Ratio)**
   - 포지션 크기 결정
   - OLS 회귀로 추정: β = cov(y,x) / var(x)

3. **반감기 (Half-life)**
   - 스프레드 회귀 속도
   - 5-30일 권장

4. **Z-score**
   - 진입/청산 신호 생성
   - |z| > 2: 진입, |z| < 0.5: 청산

### N-way 페어 트레이딩

**조합 수:**
```
KOSPI200 (200개):
- 2-way: C(200,2) = 19,900개
- 3-way: C(200,3) = 1,313,400개
- 4-way: C(200,4) = 64,684,950개
```

**해결책:**
- 벡터 DB로 유사 종목 사전 필터링
- 유사도 상위 10개만 조합
- 19,900개 → 2,000개 (90% 감소)

## 🔬 알고리즘 상세

### 공적분 검정 (Engle-Granger)

```python
# 1단계: OLS 회귀
y = α + β × x + ε
hedge_ratio = β

# 2단계: 잔차 단위근 검정
residuals = y - β × x
ADF_test(residuals) → p-value

# p < 0.05 → 공적분 존재
```

### 시계열 임베딩

**25차원 벡터:**
- 통계 특징 (10): 수익률, 변동성, 샤프비율 등
- 형태 특징 (10): PAA 기반 패턴
- 주파수 특징 (5): FFT 계수

**유사도 측정:**
```python
similarity = cosine(embedding1, embedding2)
# 0.9+ : 매우 유사 (같은 업종)
# 0.7-0.9 : 유사 (페어 후보)
```

### 신호 생성

```python
# 스프레드 계산
spread = price1 - hedge_ratio × price2

# Z-score
z_score = (spread - mean) / std

# 신호
if z_score > 2.0:
    signal = ENTRY_SHORT
elif z_score < -2.0:
    signal = ENTRY_LONG
elif |z_score| < 0.5:
    signal = EXIT
```

## 🛠️ 개발 가이드

### 환경 설정

**Windows (Cybos Plus):**
```bash
# Python 3.9 32bit 설치
# Cybos Plus HTS 로그인
python -m pip install -r requirements.txt
```

**Linux/Mac (개발):**
```bash
# Docker 설치
docker-compose up -d

# pnpm 설치
npm install -g pnpm
```

### 코딩 규칙

1. **극단적 모듈화**
   - 파일당 최대 300라인
   - 함수당 최대 50라인
   - 단일 책임 원칙

2. **타입 힌트 필수**
   ```python
   def analyze_pair(code1: str, code2: str) -> Optional[CointegrationResult]:
       ...
   ```

3. **Docstring 작성**
   ```python
   def test_cointegration(prices1: np.ndarray, prices2: np.ndarray) -> float:
       """
       Engle-Granger 공적분 검정

       Args:
           prices1: 첫 번째 종목 가격
           prices2: 두 번째 종목 가격

       Returns:
           p-value (0-1)
       """
   ```

### 테스트

```bash
# 단위 테스트
pytest tests/unit/

# 통합 테스트
pytest tests/integration/

# 커버리지
pytest --cov=src tests/
```

## 📊 운영 가이드

### 모니터링

**Grafana 대시보드:**
- URL: http://localhost:3001
- 계정: admin / admin
- 메트릭: 페어 성과, API 응답시간, 신호 빈도

**Prometheus:**
- URL: http://localhost:9090
- 메트릭 수집 및 알림

### 데이터베이스 관리

```python
# 통계 조회
from src.database.connection import get_db_info
print(get_db_info())

# 백업
db_manager.backup_database('backup/cybos.db')

# 최적화
db_manager.vacuum_database()
```

### 배치 작업

```bash
# 매일 장 마감 후 실행
# 1. 히스토리 데이터 수집
python kospi200_daily_batch.py

# 2. 공적분 재분석
cd services/cointegration-engine && python main.py

# 3. 벡터 임베딩 업데이트
cd services/vector-db && python main.py
```

## 🐛 트러블슈팅

### 자주 발생하는 문제

1. **Cybos Plus 연결 실패**
   - HTS 로그인 확인
   - 32bit Python 확인
   - COM 등록: `fix_com_registration.bat`

2. **Qdrant 연결 실패**
   - Docker 컨테이너 확인: `docker ps`
   - 로그 확인: `docker logs cybos-qdrant`
   - 재시작: `docker-compose restart qdrant`

3. **공적분 분석 데이터 부족**
   - 히스토리 데이터 확인
   - 최소 252일 필요
   - `python kospi200_daily_batch.py` 실행

4. **메모리 부족**
   - 배치 크기 줄이기
   - 불필요한 데이터 정리
   - 서버 리소스 증설

## 🔮 로드맵

### Phase 1 (현재)
- ✅ 2-way 페어 트레이딩
- ✅ KOSPI200 대상
- ✅ 공적분 분석 엔진
- ✅ 벡터 DB 서비스

### Phase 2 (3개월)
- 3-way, 4-way 페어
- Johansen 검정 구현
- 실시간 신호 생성
- 백테스팅 엔진

### Phase 3 (6개월)
- ML 기반 신호 최적화
- 자동 매매 연동
- KOSDAQ 확장

### Phase 4 (1년)
- 해외 주식 확장
- 멀티 에셋 페어
- 클라우드 배포

## 📞 지원

- **GitHub Issues:** https://github.com/optrader8/cybos-server/issues
- **Wiki:** https://github.com/optrader8/cybos-server/wiki
- **디스코드:** (향후 개설)

## 🤝 기여

문서 개선, 오타 수정, 예제 추가 등 모든 기여 환영합니다!

**기여 방법:**
1. Fork 생성
2. Feature 브랜치 생성
3. 변경사항 커밋
4. Pull Request 생성

## 📄 라이선스

MIT License - 자유롭게 사용 가능

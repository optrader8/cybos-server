# 🚀 Cybos Plus 기반 실시간 증권 시세 서버

> **극단적 모듈화(Barrel Type) & 마이크로 아키텍처** 기반의 고성능 시세 서버

**실시간 국내 주식 시세를 Cybos Plus(대신증권)에서 받아와서 SQLite DB 저장 및 API 제공**

## ⚠️ 핵심 제약사항

- **Windows 32bit Python 3.9** 전용
- **pywin32** 필수 
- **Cybos Plus HTS 로그인** 필요
- **파일당 최대 300라인** 제한 (극단적 모듈화)

## 📁 프로젝트 구조 (Ultrathink Architecture)

```
cybos-server/
├─ src/
│   ├─ core/                     # 핵심 추상화 레이어
│   │   ├─ __init__.py
│   │   ├─ types.py              # 타입 정의
│   │   ├─ exceptions.py         # 예외 정의  
│   │   ├─ constants.py          # 상수 정의
│   │   └─ interfaces.py         # 인터페이스 정의
│   │
│   ├─ cybos/                    # Cybos Plus 연동 (COM 객체 래핑)
│   │   ├─ __init__.py
│   │   ├─ connection/           # 연결 관리
│   │   │   ├─ __init__.py
│   │   │   ├─ status.py         # 연결 상태 확인
│   │   │   └─ validator.py      # 연결 유효성 검증
│   │   ├─ codes/                # 종목 코드 관리
│   │   │   ├─ __init__.py
│   │   │   ├─ manager.py        # 코드 관리자
│   │   │   ├─ converter.py      # 코드 변환
│   │   │   └─ fetcher.py        # 코드 정보 조회
│   │   ├─ price/                # 시세 데이터
│   │   │   ├─ __init__.py
│   │   │   ├─ current.py        # 현재가 조회
│   │   │   ├─ history.py        # 과거 데이터
│   │   │   └─ realtime.py       # 실시간 시세
│   │   └─ utils/                # 유틸리티
│   │       ├─ __init__.py
│   │       ├─ com_wrapper.py    # COM 객체 래퍼
│   │       └─ rate_limiter.py   # 요청 제한 관리
│   │
│   ├─ database/                 # SQLite 데이터 계층
│   │   ├─ __init__.py
│   │   ├─ models/               # 모델 정의
│   │   │   ├─ __init__.py
│   │   │   ├─ stock.py          # 주식 모델
│   │   │   ├─ price.py          # 시세 모델
│   │   │   └─ metadata.py       # 메타데이터 모델
│   │   ├─ repositories/         # 리포지토리 패턴
│   │   │   ├─ __init__.py
│   │   │   ├─ stock_repo.py     # 주식 리포지토리
│   │   │   ├─ price_repo.py     # 시세 리포지토리
│   │   │   └─ base_repo.py      # 베이스 리포지토리
│   │   ├─ migrations/           # DB 마이그레이션
│   │   │   ├─ __init__.py
│   │   │   └─ v1_initial.py     # 초기 스키마
│   │   └─ connection.py         # DB 연결 관리
│   │
│   ├─ api/                      # REST API 레이어
│   │   ├─ __init__.py
│   │   ├─ app.py               # FastAPI 앱 생성
│   │   ├─ routes/              # API 엔드포인트
│   │   │   ├─ __init__.py
│   │   │   ├─ stocks.py        # 주식 관련 API
│   │   │   ├─ prices.py        # 시세 관련 API
│   │   │   └─ health.py        # 헬스체크 API
│   │   ├─ middleware/          # 미들웨어
│   │   │   ├─ __init__.py
│   │   │   ├─ cors.py          # CORS 설정
│   │   │   └─ logging.py       # 로깅 미들웨어
│   │   └─ schemas/             # Pydantic 스키마
│   │       ├─ __init__.py
│   │       ├─ stock.py         # 주식 스키마
│   │       └─ price.py         # 시세 스키마
│   │
│   ├─ services/                # 비즈니스 로직 레이어
│   │   ├─ __init__.py
│   │   ├─ stock_service.py     # 주식 서비스
│   │   ├─ price_service.py     # 시세 서비스
│   │   └─ sync_service.py      # 동기화 서비스
│   │
│   ├─ remote/                  # 원격 전송 레이어
│   │   ├─ __init__.py
│   │   ├─ clients/             # 클라이언트
│   │   │   ├─ __init__.py
│   │   │   ├─ rest_client.py   # REST 클라이언트
│   │   │   └─ websocket_client.py # WebSocket 클라이언트
│   │   ├─ formatters/          # 데이터 포맷터
│   │   │   ├─ __init__.py
│   │   │   └─ json_formatter.py # JSON 포맷터
│   │   └─ sender.py            # 전송 관리자
│   │
│   ├─ utils/                   # 공통 유틸리티
│   │   ├─ __init__.py
│   │   ├─ logger.py            # 로깅 유틸
│   │   ├─ config.py            # 설정 관리
│   │   └─ datetime_util.py     # 날짜/시간 유틸
│   │
│   └─ main.py                  # 애플리케이션 진입점
│
├─ scripts/                     # 관리 스크립트
│   ├─ __init__.py
│   ├─ init_database.py         # DB 초기화
│   ├─ sync_stock_codes.py      # 종목 코드 동기화
│   ├─ test_connection.py       # 연결 테스트
│   └─ start_server.py          # 서버 시작
│
├─ tests/                       # 테스트 코드
│   ├─ __init__.py
│   ├─ unit/                    # 단위 테스트
│   ├─ integration/             # 통합 테스트
│   └─ fixtures/                # 테스트 데이터
│
├─ config/                      # 설정 파일
│   ├─ __init__.py
│   ├─ development.py           # 개발 환경 설정
│   ├─ production.py            # 운영 환경 설정
│   └─ base.py                  # 기본 설정
│
├─ requirements.txt             # Python 의존성
├─ .env.example                 # 환경 변수 예시
├─ .gitignore                   # Git 무시 파일
├─ pyproject.toml              # Python 프로젝트 설정
└─ run_server.bat              # Windows 실행 스크립트
```

## 🎯 설계 철학

### 1. **극단적 모듈화 (Barrel Type)**
- 파일당 최대 **300라인** 제한
- 단일 책임 원칙 극한 적용
- 높은 응집도, 낮은 결합도

### 2. **계층화 아키텍처**
- **Core**: 타입, 인터페이스, 예외 정의
- **Cybos**: COM 객체 래핑 및 추상화
- **Database**: 데이터 영속성 계층
- **API**: REST API 인터페이스
- **Services**: 비즈니스 로직
- **Remote**: 원격 전송 로직

### 3. **확장성 고려**
- 인터페이스 기반 설계
- 의존성 주입 패턴
- 플러그인 아키텍처 준비

## 🚀 주요 기능

### 📊 시세 데이터 관리
- 실시간 주식 시세 수집
- SQLite 기반 데이터 저장
- 종목 코드 자동 동기화

### 🔗 API 서비스
- RESTful API 제공
- 실시간 데이터 조회
- 헬스체크 및 모니터링

### 📡 원격 전송
- 우분투 서버로 데이터 전송
- REST/WebSocket 프로토콜 지원
- 자동 재연결 및 오류 복구

## 🛠️ 기술 스택

- **Python 3.9** (32bit)
- **FastAPI** - REST API 프레임워크
- **SQLite3** - 데이터베이스
- **pywin32** - Windows COM 인터페이스
- **Pydantic** - 데이터 검증
- **asyncio** - 비동기 처리

## 🚀 빠른 시작

### 1. 환경 준비
```powershell
# Cybos Plus HTS 실행 및 로그인 후 진행
# Python 32bit 환경에서 실행

# 의존성 설치
python -m pip install -r requirements.txt
```

### 2. 데이터베이스 초기화
```powershell
python scripts/init_database.py
python scripts/sync_stock_codes.py
```

### 3. 서버 실행
```powershell
# 개발 환경
python src/main.py

# 또는 배치 파일 사용
run_server.bat
```

### 4. API 테스트
```bash
# 헬스체크
curl http://localhost:8000/api/health

# 주식 목록 조회
curl http://localhost:8000/api/stocks

# 특정 종목 시세 조회
curl http://localhost:8000/api/prices/005930  # 삼성전자
```

## 📡 API 엔드포인트

### 주식 정보
- `GET /api/stocks` - 전체 주식 목록
- `GET /api/stocks/{code}` - 특정 주식 정보
- `POST /api/stocks/sync` - 주식 정보 동기화

### 시세 정보
- `GET /api/prices/{code}` - 현재가 조회
- `GET /api/prices/{code}/history` - 과거 시세
- `WebSocket /ws/prices/{code}` - 실시간 시세

### 시스템
- `GET /api/health` - 헬스체크
- `GET /api/status` - 시스템 상태

## 🔧 설정

### 환경 변수 (.env)
```bash
# 데이터베이스
DATABASE_PATH=./data/cybos.db

# API 서버
API_HOST=0.0.0.0
API_PORT=8000

# 원격 서버
REMOTE_SERVER_URL=http://ubuntu-server:8080
REMOTE_API_KEY=your_api_key

# 로깅
LOG_LEVEL=INFO
LOG_FILE=./logs/cybos-server.log
```

## 📝 개발 가이드

### 코딩 규칙
- 파일당 최대 300라인
- 함수당 최대 50라인
- 클래스당 최대 10개 메서드
- Type Hints 필수 사용

### 테스트
```powershell
# 단위 테스트
python -m pytest tests/unit/

# 통합 테스트 (Cybos Plus 로그인 필요)
python -m pytest tests/integration/

# 전체 테스트
python -m pytest
```

### 새 모듈 추가 시
1. 인터페이스 먼저 정의 (`core/interfaces.py`)
2. 구현체 작성 (최대 300라인)
3. 테스트 코드 작성
4. 의존성 주입 설정

## 🚨 주의사항

- **Windows + Python 32bit 환경에서만 동작**
- **Cybos Plus HTS 로그인** 상태 유지 필수
- **API 호출 제한** 준수 (분당 200회)
- **실시간 데이터** 사용 시 라이선스 확인

## 📄 라이선스

이 프로젝트는 개인/교육 목적으로만 사용 가능하며, Cybos Plus API 이용약관을 준수해야 합니다.

## 🤝 기여

1. Fork the Project
2. Create Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit Changes (`git commit -m 'Add AmazingFeature'`)
4. Push to Branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📞 지원

문제 발생 시 [Issues](https://github.com/username/cybos-server/issues) 페이지에 문의해주세요.

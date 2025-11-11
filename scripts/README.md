# 스크립트 디렉토리

데이터베이스 초기화 및 관리를 위한 유틸리티 스크립트입니다.

## 스크립트 목록

### 1. init_database.py

데이터베이스 테이블을 초기화하고 인덱스를 생성합니다.

```bash
# 기본 경로로 초기화
python scripts/init_database.py

# 특정 경로로 초기화
python scripts/init_database.py --db-path data/my_db.db

# 기존 데이터베이스 삭제 후 재생성
python scripts/init_database.py --force
```

**옵션:**
- `--db-path PATH`: 데이터베이스 파일 경로 (기본값: 환경변수 `DATABASE_PATH` 또는 `data/cybos.db`)
- `--force`: 기존 데이터베이스를 삭제하고 재생성

### 2. sync_stock_codes.py

Cybos Plus에서 종목 정보를 가져와 데이터베이스에 저장합니다.

```bash
# 전체 시장 동기화 (기본 정보만)
python scripts/sync_stock_codes.py

# KOSPI만 동기화
python scripts/sync_stock_codes.py --market kospi

# 전체 시장 동기화 (상세 정보 포함, 느림)
python scripts/sync_stock_codes.py --detailed

# 특정 데이터베이스에 동기화
python scripts/sync_stock_codes.py --db-path data/my_db.db

# KOSDAQ 상세 정보 동기화
python scripts/sync_stock_codes.py --market kosdaq --detailed
```

**옵션:**
- `--market MARKET`: 동기화할 시장 (all, kospi, kosdaq, freeboard, krx) (기본값: all)
- `--detailed`: 상세 정보까지 수집 (느림)
- `--db-path PATH`: 데이터베이스 파일 경로 (기본값: 환경변수 `DATABASE_PATH` 또는 `data/cybos.db`)

## 초기 설정 워크플로우

프로젝트를 처음 설정할 때 다음 순서로 스크립트를 실행하세요:

```bash
# 1. 데이터베이스 초기화
python scripts/init_database.py

# 2. 종목 코드 동기화
python scripts/sync_stock_codes.py

# 3. 데이터베이스 확인
python scripts/init_database.py  # 테이블 정보 출력
```

## 주의사항

- **Windows 32-bit Python 환경 필요**: Cybos Plus는 Windows 32-bit에서만 작동합니다.
- **Cybos Plus 로그인 필요**: `sync_stock_codes.py` 실행 전에 Cybos Plus에 로그인해야 합니다.
- **API 요청 제한**: Cybos Plus는 요청 제한이 있으므로 대량 동기화 시 시간이 오래 걸릴 수 있습니다.

## 문제 해결

### "Failed to initialize COM objects" 오류

Cybos Plus가 설치되지 않았거나 로그인하지 않은 경우 발생합니다.

**해결 방법:**
1. Cybos Plus 설치 확인
2. Cybos Plus 실행 및 로그인
3. 32-bit Python 환경에서 실행 확인

### "Database is locked" 오류

다른 프로세스가 데이터베이스를 사용 중일 때 발생합니다.

**해결 방법:**
1. 다른 데이터베이스 연결 종료
2. 서버 중지 후 스크립트 실행

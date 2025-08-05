# 🚀 Cybos Plus 기반 실시간 증권 시세 서버

> **극단적 모듈화(Barrel Type) & 마이크로 아키텍처** 기반의 고성능 시세 서버

**실시간 국내 주식 시세를 Cybos Plus(대신증권)에서 받아와서 SQLite DB 저장 및 API 제공**

## ⚠️ 핵심 제약사항

- **Windows 32bit Python 3.9** 전용
- **pywin32** 필수 
- **Cybos Plus HTS 로그인** 필요
- **파일당 최대 300라인** 제한 (극단적 모듈화)

## 📁 프로젝트 구조 (Ultrathink Architecture)

```markdown
# Cybos Plus 기반 실시간 증권 시세 서버

**실시간 국내 주식 시세를 Cybos Plus(대신증권)에서 받아와서**
- 종목 기초정보와 시세를 SQLite DB에 저장
- REST API로 외부 프로그램(예: 리눅스/우분투 서버, 백엔드 등)에서 시세 데이터 조회/활용
- 실시간 시세 변동을 원격 서버(우분투)로 전송하고, 서버는 DB에 저장/활용

---

## ⚠️ 환경 필수 조건

- 반드시 **Windows 운영체제**에서만 동작  
- **Python 32bit 버전**만 지원 (예: Python 3.9 32bit)
- **pywin32** 필수 (pip로 설치: `pip install pywin32`)
- **Cybos Plus(대신증권 HTS) 설치/로그인** 필요  
- 원격 서버(DB 저장 등)는 우분투, DB는 SQLite3 기반(확장 가능)

> **64bit Python 또는 비윈도우 환경에서는 Cybos Plus 연동이 절대 불가!**

---

## 🏗️ 폴더/파일 구조

```

cybos-server/
├─ src/
│   ├─ cybos/          # Cybos Plus 연동(종목/시세/실시간)
│   ├─ db/             # SQLite 연동 및 모델
│   ├─ api/            # REST API (FastAPI 권장)
│   ├─ remote/         # 원격 전송 (REST/gRPC/WebSocket)
│   └─ config.py       # 설정 관리
├─ scripts/            # DB 초기화, 코드동기화 등
├─ tests/              # 테스트 코드
├─ requirements.txt
└─ run\_server.bat      # Windows용 실행 스크립트 (python32)

````

---

## 🧩 주요 컴포넌트 설명

- **src/cybos/**  
  - Cybos Plus API(COM) 연동, 종목조회, 시세조회, 실시간 시세 watch
- **src/db/**  
  - SQLite 모델/CRUD, 시세/종목 데이터 저장 및 조회
- **src/api/main.py**  
  - REST API 서버 (FastAPI)
- **src/remote/sender.py**  
  - 원격 서버(우분투 등)에 실시간 시세 전송 (REST/gRPC/WebSocket 등 선택적 지원)
- **scripts/init_db.py, fetch_codes.py**  
  - DB 및 종목코드 초기화, 동기화

---

## 🚀 실행 방법

1. **(필수) Cybos Plus HTS 실행 & 로그인 후 아래 절차 진행**
2. **Python 32bit 환경 준비**

   ```bash
   # (예시) 32비트 파이썬에서 의존성 설치
   python -m pip install -r requirements.txt
````

3. **DB 및 종목코드 초기화**

   ```bash
   python scripts/init_db.py
   python scripts/fetch_codes.py
   ```

4. **서버 실행**

   ```bash
   # Windows 명령줄, 관리자 권한 권장
   python src/api/main.py
   ```

5. **REST API 사용 예시**

   * GET `/api/stocks` : 종목 목록 조회
   * GET `/api/price/{code}` : 특정 종목 시세 조회
   * POST `/api/price/push` : 시세 수신/저장 (외부 서버용)

---

## ⚡️ 확장/연동 예시

* 원격 우분투 서버로 실시간 시세를 전송 (`remote/sender.py`), 서버에서는 별도 API로 수신 및 DB 저장
* 타 플랫폼/앱(리눅스, 웹, 기타)에서 시세 데이터 연동 가능

---

## 👨‍💻 참고 및 주의사항

* **Windows+Python 32bit+pywin32+HTS 로그인** 필수
* 실서비스에서는 데이터 무결성/중복/에러처리, 스케줄링, 실시간 이벤트처리 강화 필요
* (추후) DB, API, 원격 연동부는 필요에 따라 분리/모듈화 가능

---

## 📝 기타

* 본 프로젝트는 국내 HTS API 특성상 **Windows와 32bit Python 전용**으로 제한됩니다.
* Cybos Plus 라이선스/증권사 API 정책을 반드시 준수하십시오.
* 실사용시 개인 계정 보안/자동 로그인 등 주의

---

```

---

>  
실제 구현 코드, 각 모듈별 상세구성, FastAPI 기본 REST API 예시,  
원격 서버 연동 방식(REST/gRPC/WebSocket) 등의 샘플까지  
필요하시면 다음 단계에서 세부적으로 안내 가능합니다!

궁금한 구조나 세부 설계 방향, 자동화, 배포 등 추가 요청도 환영합니다!
```

@echo off
REM ====================================
REM Cybos Plus 기반 실시간 증권 시세 서버
REM Windows 32bit Python 3.9 전용
REM ====================================

title Cybos Server - 실시간 증권 시세 서버

echo.
echo =============================================
echo   Cybos Plus 실시간 증권 시세 서버 시작
echo =============================================
echo.

REM 현재 디렉토리를 스크립트 위치로 변경
cd /d "%~dp0"

REM Python 32bit 버전 확인
echo [1/5] Python 환경 확인 중...
python -c "import sys; print(f'Python {sys.version}'); print(f'Architecture: {sys.maxsize > 2**32 and \"64bit\" or \"32bit\"}')"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python이 설치되지 않았거나 PATH에 없습니다.
    echo Python 3.9 32bit 버전을 설치해주세요.
    pause
    exit /b 1
)

REM 32bit 확인 (간단한 방법)
python -c "import sys; exit(0 if sys.maxsize <= 2**32 else 1)" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: 64bit Python이 감지되었습니다.
    echo Cybos Plus는 32bit Python에서만 동작합니다.
    echo Python 3.9 32bit 버전을 설치하고 사용해주세요.
    echo.
    pause
    exit /b 1
)

echo ✓ Python 32bit 환경 확인 완료

REM pywin32 설치 확인
echo.
echo [2/5] pywin32 모듈 확인 중...
python -c "import win32com.client" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: pywin32가 설치되지 않았습니다.
    echo 자동 설치를 시도합니다...
    python -m pip install pywin32
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: pywin32 설치에 실패했습니다.
        echo 수동으로 'pip install pywin32'를 실행해주세요.
        pause
        exit /b 1
    )
)
echo ✓ pywin32 모듈 확인 완료

REM 의존성 설치 확인
echo.
echo [3/5] 필수 패키지 확인 중...
if exist requirements.txt (
    python -m pip install -r requirements.txt --quiet
    if %ERRORLEVEL% NEQ 0 (
        echo WARNING: 일부 패키지 설치에 실패했을 수 있습니다.
        echo 계속 진행합니다...
    )
) else (
    echo WARNING: requirements.txt 파일을 찾을 수 없습니다.
)
echo ✓ 패키지 확인 완료

REM 데이터 디렉토리 생성
echo.
echo [4/5] 디렉토리 구조 확인 중...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "temp" mkdir temp
echo ✓ 디렉토리 구조 확인 완료

REM Cybos Plus 연결 상태 확인
echo.
echo [5/5] Cybos Plus 연결 상태 확인 중...
python -c "
try:
    import win32com.client
    cybos = win32com.client.Dispatch('CpUtil.CpCybos')
    if cybos.IsConnect == 1:
        server_type = cybos.ServerType
        server_name = ['연결끊김', 'CybosPlus', 'HTS일반'][server_type] if server_type <= 2 else '알수없음'
        print(f'✓ Cybos Plus 연결 상태: 정상 ({server_name})')
        exit(0)
    else:
        print('WARNING: Cybos Plus가 연결되지 않았습니다.')
        print('CybosPlus HTS를 실행하고 로그인한 후 다시 시도해주세요.')
        exit(1)
except Exception as e:
    print(f'ERROR: Cybos Plus 확인 중 오류 발생: {e}')
    print('CybosPlus HTS가 설치되어 있는지 확인해주세요.')
    exit(1)
"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ===============================================
    echo   Cybos Plus 연결 문제가 있습니다.
    echo ===============================================
    echo.
    echo 해결 방법:
    echo 1. CybosPlus HTS를 실행하세요
    echo 2. 증권사 계정으로 로그인하세요  
    echo 3. 로그인 완료 후 이 스크립트를 다시 실행하세요
    echo.
    echo 그래도 문제가 있다면 'python scripts/test_connection.py'를 실행해보세요.
    echo.
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   모든 준비가 완료되었습니다!
echo ===============================================
echo.

REM 서버 시작
echo 서버를 시작합니다...
echo 종료하려면 Ctrl+C를 누르세요.
echo.

REM 환경 변수 설정 (있다면)
if exist .env (
    echo ✓ .env 파일 발견 - 환경 변수 적용
)

REM 메인 애플리케이션 실행
python src/main.py

REM 오류 발생 시 처리
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ===============================================
    echo   서버 실행 중 오류가 발생했습니다.
    echo ===============================================
    echo.
    echo 오류 코드: %ERRORLEVEL%
    echo.
    echo 문제 해결:
    echo 1. logs/ 폴더의 로그 파일을 확인하세요
    echo 2. Cybos Plus 연결 상태를 확인하세요
    echo 3. Python 의존성이 올바르게 설치되었는지 확인하세요
    echo.
)

echo.
echo 서버가 종료되었습니다.
pause

@echo off
echo COM 객체 등록 문제 해결 스크립트
echo =====================================

echo.
echo 1. 관리자 권한으로 PowerShell 실행하기
echo    - Windows 키 + X 누르기
echo    - "Windows PowerShell (관리자)" 선택
echo    - 아래 명령어 실행:
echo.
echo    cd "d:\dev\cybos-server"
echo    python test_price_update.py
echo.

echo 2. 또는 이 배치 파일을 관리자 권한으로 실행
echo    - 마우스 우클릭 후 "관리자 권한으로 실행" 선택
echo.

pause

REM 관리자 권한이 있을 때만 실행
net session >nul 2>&1
if %errorLevel% == 0 (
    echo 관리자 권한 확인됨. Python 테스트 실행...
    cd /d "d:\dev\cybos-server"
    python test_price_update.py
) else (
    echo 관리자 권한이 필요합니다!
    echo 이 파일을 마우스 우클릭하여 "관리자 권한으로 실행"하세요.
)

pause

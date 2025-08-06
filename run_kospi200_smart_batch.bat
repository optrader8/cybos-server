@echo off
echo ========================================
echo KOSPI200 Smart Daily History Batch Runner
echo ========================================
echo.

REM 현재 시간 출력
echo 시작 시간: %date% %time%
echo.

REM Python 가상환경 활성화 (있는 경우)
if exist "env\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call env\Scripts\activate.bat
    echo.
)

REM KOSPI200 스마트 일봉 히스토리 배치 실행
echo KOSPI200 스마트 일봉 히스토리 배치 시작...
echo 스마트 모드: 누락일수 + 10일 버퍼만 요청
echo 대기시간: 12-60초 랜덤
echo.

python kospi200_daily_batch_update.py --min-delay 0.2 --max-delay 1.0 --buffer 10

echo.
echo 완료 시간: %date% %time%
echo ========================================
pause

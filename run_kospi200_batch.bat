@echo off
echo ========================================
echo KOSPI200 Daily History Batch Runner
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

REM KOSPI200 일봉 히스토리 배치 실행
echo KOSPI200 일봉 히스토리 배치 시작...
echo 대기시간: 3-10분 랜덤
echo.

python kospi200_daily_batch.py --min-delay 3 --max-delay 10

echo.
echo 완료 시간: %date% %time%
echo ========================================
pause

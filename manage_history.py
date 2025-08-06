"""
History Management Commands - 히스토리 데이터 관리 명령어들

히스토리 데이터의 상태 확인, 백업, 복구 등의 관리 기능을 제공합니다.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_connection_context
from src.database.models.history import HistoryTable, HistoryTimeframe
from src.database.models.stock import StockTable
from src.services.history_integration_service import HistoryIntegrationService


def check_history_status():
    """히스토리 데이터 상태 확인"""
    print("📊 히스토리 데이터 상태 확인")
    print("=" * 50)
    
    with get_connection_context("data/cybos.db") as conn:
        # 전체 히스토리 레코드 수
        cursor = conn.execute(f"SELECT COUNT(*) FROM {HistoryTable.TABLE_NAME}")
        total_records = cursor.fetchone()[0]
        
        # 타임프레임별 레코드 수
        timeframe_stats = {}
        for timeframe in ['D', 'W', 'M']:
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM {HistoryTable.TABLE_NAME} 
                WHERE timeframe = ?
            """, (timeframe,))
            timeframe_stats[timeframe] = cursor.fetchone()[0]
        
        # 종목별 데이터 현황 (상위 10개)
        cursor = conn.execute(f"""
            SELECT code, timeframe, COUNT(*) as count, 
                   MIN(date) as earliest, MAX(date) as latest
            FROM {HistoryTable.TABLE_NAME}
            WHERE timeframe = 'D'
            GROUP BY code, timeframe
            ORDER BY count DESC
            LIMIT 10
        """)
        
        top_stocks = cursor.fetchall()
        
        print(f"📈 전체 히스토리 레코드: {total_records:,}개")
        print(f"   일봉: {timeframe_stats['D']:,}개")
        print(f"   주봉: {timeframe_stats['W']:,}개")
        print(f"   월봉: {timeframe_stats['M']:,}개")
        
        print(f"\n📋 일봉 데이터 보유 종목 Top 10:")
        for stock in top_stocks:
            print(f"   {stock[0]}: {stock[2]:,}개 ({stock[3]} ~ {stock[4]})")


def check_stock_completeness(code: str, days: int = 30):
    """특정 종목의 데이터 완전성 검사"""
    print(f"🔍 {code} 종목 데이터 완전성 검사 ({days}일)")
    print("=" * 50)
    
    service = HistoryIntegrationService()
    result = service.check_data_completeness(code, days)
    
    print(f"📊 검사 결과:")
    print(f"   종목코드: {result['code']}")
    print(f"   검사 기간: {result['start_date']} ~ {result['end_date']}")
    print(f"   히스토리 레코드: {result['history_records']:,}개")
    print(f"   오늘 실시간 레코드: {result['realtime_records_today']:,}개")
    print(f"   최신 히스토리 날짜: {result['latest_history_date']}")
    print(f"   오늘 실시간 데이터: {'있음' if result['has_today_realtime'] else '없음'}")
    print(f"   데이터 공백: {result['data_gap_days']}일")
    
    if result['data_gap_days'] > 7:
        print(f"⚠️  주의: {result['data_gap_days']}일 이상의 데이터 공백이 있습니다.")
    elif result['data_gap_days'] > 3:
        print(f"🔸 알림: {result['data_gap_days']}일의 데이터 공백이 있습니다.")
    else:
        print(f"✅ 데이터 상태 양호")


def sync_realtime_to_history():
    """오늘의 실시간 데이터를 히스토리로 동기화"""
    print("🔄 실시간 데이터 → 히스토리 동기화")
    print("=" * 50)
    
    service = HistoryIntegrationService()
    
    # 오늘 실시간 데이터가 있는 종목들 찾기
    with get_connection_context("data/cybos.db") as conn:
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor = conn.execute(f"""
            SELECT DISTINCT code 
            FROM prices
            WHERE date(created_at) = ?
            ORDER BY code
        """, (today,))
        
        codes = [row[0] for row in cursor.fetchall()]
    
    print(f"📊 오늘 실시간 데이터가 있는 종목: {len(codes)}개")
    
    if not codes:
        print("⚠️  동기화할 실시간 데이터가 없습니다.")
        return
    
    # 확인
    response = input(f"\n{len(codes)}개 종목을 동기화하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        print("취소되었습니다.")
        return
    
    success_count = 0
    for i, code in enumerate(codes):
        print(f"🔄 {i+1}/{len(codes)}: {code}")
        if service.sync_today_data(code):
            success_count += 1
    
    print(f"\n✅ 동기화 완료: {success_count}/{len(codes)}개 성공")


def export_history_csv(code: str, start_date: str, end_date: str):
    """히스토리 데이터 CSV 내보내기"""
    print(f"📤 {code} 히스토리 데이터 CSV 내보내기")
    print(f"기간: {start_date} ~ {end_date}")
    print("=" * 50)
    
    import csv
    
    service = HistoryIntegrationService()
    data = service.get_complete_daily_data(code, start_date, end_date)
    
    if not data:
        print("❌ 내보낼 데이터가 없습니다.")
        return
    
    # CSV 파일명 생성
    csv_filename = f"history_{code}_{start_date}_{end_date}.csv"
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # 헤더
        writer.writerow([
            'Code', 'Date', 'Open', 'High', 'Low', 'Close', 
            'Volume', 'Amount', 'Source'
        ])
        
        # 데이터
        for candle in data:
            writer.writerow([
                candle.code,
                candle.date,
                candle.open_price,
                candle.high_price,
                candle.low_price,
                candle.close_price,
                candle.volume,
                candle.amount,
                'Realtime' if candle.is_realtime else 'History'
            ])
    
    print(f"✅ CSV 파일 생성 완료: {csv_filename}")
    print(f"📊 총 {len(data)}개 레코드 내보내기")


def validate_history_data():
    """히스토리 데이터 유효성 검증"""
    print("🔍 히스토리 데이터 유효성 검증")
    print("=" * 50)
    
    issues = []
    
    with get_connection_context("data/cybos.db") as conn:
        # 1. 가격이 0인 레코드 검사
        cursor = conn.execute(f"""
            SELECT code, date, timeframe
            FROM {HistoryTable.TABLE_NAME}
            WHERE close_price = 0 OR open_price = 0
        """)
        
        zero_price_records = cursor.fetchall()
        if zero_price_records:
            issues.append(f"가격이 0인 레코드: {len(zero_price_records)}개")
        
        # 2. 비정상적 가격 범위 검사 (고가 < 저가)
        cursor = conn.execute(f"""
            SELECT code, date, timeframe, high_price, low_price
            FROM {HistoryTable.TABLE_NAME}
            WHERE high_price < low_price
        """)
        
        invalid_range_records = cursor.fetchall()
        if invalid_range_records:
            issues.append(f"고가 < 저가인 레코드: {len(invalid_range_records)}개")
        
        # 3. 거래량이 음수인 레코드
        cursor = conn.execute(f"""
            SELECT code, date, timeframe
            FROM {HistoryTable.TABLE_NAME}
            WHERE volume < 0
        """)
        
        negative_volume_records = cursor.fetchall()
        if negative_volume_records:
            issues.append(f"거래량이 음수인 레코드: {len(negative_volume_records)}개")
        
        # 4. 중복 데이터 검사
        cursor = conn.execute(f"""
            SELECT code, date, timeframe, COUNT(*)
            FROM {HistoryTable.TABLE_NAME}
            GROUP BY code, date, timeframe
            HAVING COUNT(*) > 1
        """)
        
        duplicate_records = cursor.fetchall()
        if duplicate_records:
            issues.append(f"중복 레코드: {len(duplicate_records)}개 그룹")
    
    if issues:
        print("⚠️  발견된 문제점:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ 데이터 유효성 검증 통과")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="히스토리 데이터 관리")
    
    subparsers = parser.add_subparsers(dest="command", help="사용 가능한 명령어")
    
    # 상태 확인
    subparsers.add_parser("status", help="히스토리 데이터 상태 확인")
    
    # 종목별 완전성 검사
    check_parser = subparsers.add_parser("check", help="종목별 데이터 완전성 검사")
    check_parser.add_argument("code", help="종목코드")
    check_parser.add_argument("--days", type=int, default=30, help="검사 기간 (일)")
    
    # 동기화
    subparsers.add_parser("sync", help="실시간 데이터를 히스토리로 동기화")
    
    # CSV 내보내기
    export_parser = subparsers.add_parser("export", help="히스토리 데이터 CSV 내보내기")
    export_parser.add_argument("code", help="종목코드")
    export_parser.add_argument("start_date", help="시작 날짜 (YYYY-MM-DD)")
    export_parser.add_argument("end_date", help="끝 날짜 (YYYY-MM-DD)")
    
    # 유효성 검증
    subparsers.add_parser("validate", help="히스토리 데이터 유효성 검증")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print("🛠️  히스토리 데이터 관리 도구")
    print("=" * 50)
    
    # 명령어별 실행
    if args.command == "status":
        check_history_status()
    elif args.command == "check":
        check_stock_completeness(args.code, args.days)
    elif args.command == "sync":
        sync_realtime_to_history()
    elif args.command == "export":
        export_history_csv(args.code, args.start_date, args.end_date)
    elif args.command == "validate":
        validate_history_data()
    else:
        print(f"❌ 알 수 없는 명령어: {args.command}")


if __name__ == "__main__":
    main()

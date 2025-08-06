"""
Update Stock History - 주식 히스토리 데이터 업데이트 스크립트

StockChart API를 사용하여 일봉, 주봉, 월봉 히스토리 데이터를 수집하는 스크립트입니다.
기존 실시간 시세 시스템과 함께 작동하여 완전한 시계열 데이터를 구축합니다.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import win32com.client
    from src.database.connection import initialize_database, get_db_info
    from src.database.models.history import HistoryTable, HistoryTimeframe
    from src.database.models.stock import MarketKind
    from src.services.history_update_service import HistoryUpdateService, run_history_update
except ImportError as e:
    print(f"Import error: {e}")
    print("Please make sure you're running in the correct environment")
    sys.exit(1)


def check_cybos_connection():
    """Cybos Plus 연결 확인"""
    try:
        cybos = win32com.client.Dispatch("CpUtil.CpCybos")
        if cybos.IsConnect:
            print("✅ Cybos Plus 연결 상태: 정상")
            return True
        else:
            print("❌ Cybos Plus 연결되지 않음")
            print("   1. Cybos Plus를 실행하고 로그인하세요")
            print("   2. 모든 COM 등록이 완료되었는지 확인하세요")
            return False
    except Exception as e:
        print(f"❌ Cybos Plus 연결 확인 실패: {e}")
        return False


def check_database():
    """데이터베이스 상태 확인"""
    try:
        print("🗄️  데이터베이스 상태 확인...")
        db_info = get_db_info()
        print(f"   DB 경로: {db_info['path']}")
        print(f"   DB 크기: {db_info['size_mb']:.1f}MB")
        print(f"   총 테이블 수: {db_info['table_count']}")
        print("   ✅ 데이터베이스 상태: 정상")
        return True
    except Exception as e:
        print(f"❌ 데이터베이스 확인 실패: {e}")
        return False


def run_daily_update(args):
    """일봉 히스토리 업데이트"""
    print("📊 일봉 히스토리 데이터 업데이트")
    
    service = HistoryUpdateService(
        batch_size=args.batch_size,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        max_requests_per_hour=args.max_requests
    )
    
    market_kinds = []
    if args.kospi:
        market_kinds.append(MarketKind.KOSPI)
    if args.kosdaq:
        market_kinds.append(MarketKind.KOSDAQ)
    if not market_kinds:
        market_kinds = [MarketKind.KOSPI, MarketKind.KOSDAQ]
    
    result = service.run_full_history_update(
        market_kinds=market_kinds,
        timeframe=HistoryTimeframe.DAILY,
        incremental=args.incremental,
        dry_run=args.dry_run
    )
    
    return result


def run_weekly_update(args):
    """주봉 히스토리 업데이트"""
    print("📊 주봉 히스토리 데이터 업데이트")
    
    service = HistoryUpdateService(
        batch_size=args.batch_size,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        max_requests_per_hour=args.max_requests
    )
    
    market_kinds = []
    if args.kospi:
        market_kinds.append(MarketKind.KOSPI)
    if args.kosdaq:
        market_kinds.append(MarketKind.KOSDAQ)
    if not market_kinds:
        market_kinds = [MarketKind.KOSPI, MarketKind.KOSDAQ]
    
    result = service.run_full_history_update(
        market_kinds=market_kinds,
        timeframe=HistoryTimeframe.WEEKLY,
        incremental=args.incremental,
        dry_run=args.dry_run
    )
    
    return result


def run_monthly_update(args):
    """월봉 히스토리 업데이트"""
    print("📊 월봉 히스토리 데이터 업데이트")
    
    service = HistoryUpdateService(
        batch_size=args.batch_size,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        max_requests_per_hour=args.max_requests
    )
    
    market_kinds = []
    if args.kospi:
        market_kinds.append(MarketKind.KOSPI)
    if args.kosdaq:
        market_kinds.append(MarketKind.KOSDAQ)
    if not market_kinds:
        market_kinds = [MarketKind.KOSPI, MarketKind.KOSDAQ]
    
    result = service.run_full_history_update(
        market_kinds=market_kinds,
        timeframe=HistoryTimeframe.MONTHLY,
        incremental=args.incremental,
        dry_run=args.dry_run
    )
    
    return result


def run_kospi200_daily(args):
    """KOSPI200 일봉 히스토리 업데이트 (테스트용)"""
    print("📊 KOSPI200 일봉 히스토리 업데이트")
    
    # KOSPI200 대표 종목들 (테스트용)
    kospi200_codes = [
        'A005930', 'A000660', 'A207940', 'A005380', 'A006400',
        'A051910', 'A003550', 'A000270', 'A068270', 'A012330'
    ]
    
    print(f"🎯 KOSPI200 대표 종목 {len(kospi200_codes)}개 대상")
    
    if args.dry_run:
        estimated_time = len(kospi200_codes) * (args.max_delay + args.min_delay) / 2 / 60
        print(f"📊 예상 처리 시간: {estimated_time:.1f}분")
        return {"total_stocks": len(kospi200_codes), "successful_stocks": len(kospi200_codes)}
    
    # 히스토리 업데이트 서비스로 종목 목록 직접 전달
    service = HistoryUpdateService(
        batch_size=args.batch_size,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        max_requests_per_hour=args.max_requests
    )
    
    # 간단한 처리를 위해 직접 수집
    from src.database.connection import get_connection_context
    from src.database.models.stock import StockTable
    
    target_stocks = []
    with get_connection_context("data/cybos.db") as conn:
        for code in kospi200_codes:
            stock_info = StockTable.get_stock(conn, code)
            if stock_info:
                target_stocks.append({
                    'code': stock_info.code,
                    'name': stock_info.name,
                    'market_kind': stock_info.market_kind
                })
    
    # 작은 배치로 처리
    service.batch_size = min(args.batch_size, 5)
    
    print(f"\n📈 히스토리 데이터 수집 시작...")
    
    total_records = 0
    for i, stock in enumerate(target_stocks):
        print(f"🔄 {i+1}/{len(target_stocks)}: {stock['code']} ({stock['name']})")
        
        batch_records = service.update_history_batch(
            [stock], 
            HistoryTimeframe.DAILY,
            args.incremental
        )
        total_records += batch_records
        
        print(f"   ✅ {batch_records:,}개 레코드 저장")
    
    print(f"\n🎉 완료: 총 {total_records:,}개 히스토리 레코드 저장")
    
    return {
        "total_stocks": len(target_stocks),
        "successful_stocks": len(target_stocks),
        "total_history_records": total_records
    }


def cleanup_old_history(args):
    """오래된 히스토리 데이터 정리"""
    print(f"🗑️  {args.cleanup_days}일 이전 히스토리 데이터 정리")
    
    from src.database.connection import get_connection_context
    from src.database.models.history import HistoryTable
    from datetime import datetime, timedelta
    
    cutoff_date = (datetime.now() - timedelta(days=args.cleanup_days)).strftime('%Y-%m-%d')
    
    deleted_count = 0
    with get_connection_context("data/cybos.db") as conn:
        cursor = conn.execute(f"""
            DELETE FROM {HistoryTable.TABLE_NAME} 
            WHERE date < ?
        """, (cutoff_date,))
        deleted_count = cursor.rowcount
        conn.commit()
    
    print(f"✅ 정리 완료: {deleted_count:,}건 삭제")
    return {"deleted_count": deleted_count}


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="주식 히스토리 데이터 업데이트")
    
    # 공통 인수
    parser.add_argument("--dry-run", action="store_true", help="실제 실행 없이 계획만 출력")
    parser.add_argument("--batch-size", type=int, default=10, help="배치 크기 (기본: 10)")
    parser.add_argument("--min-delay", type=float, default=3.0, help="최소 지연 시간 (초)")
    parser.add_argument("--max-delay", type=float, default=8.0, help="최대 지연 시간 (초)")
    parser.add_argument("--max-requests", type=int, default=200, help="시간당 최대 요청 수")
    parser.add_argument("--incremental", action="store_true", default=True, help="증분 업데이트 (기존 데이터가 있으면 최근 데이터만)")
    parser.add_argument("--full", action="store_true", help="전체 업데이트 (기존 데이터 무시하고 전체 수집)")
    
    # 시장 선택
    parser.add_argument("--kospi", action="store_true", help="KOSPI 종목만")
    parser.add_argument("--kosdaq", action="store_true", help="KOSDAQ 종목만")
    
    # 서브 명령어
    subparsers = parser.add_subparsers(dest="command", help="사용 가능한 명령어")
    
    # 일봉 업데이트
    subparsers.add_parser("daily", help="일봉 히스토리 업데이트")
    
    # 주봉 업데이트
    subparsers.add_parser("weekly", help="주봉 히스토리 업데이트")
    
    # 월봉 업데이트
    subparsers.add_parser("monthly", help="월봉 히스토리 업데이트")
    
    # KOSPI200 테스트
    subparsers.add_parser("kospi200", help="KOSPI200 일봉 히스토리 업데이트 (테스트)")
    
    # 데이터 정리
    cleanup_parser = subparsers.add_parser("cleanup", help="오래된 히스토리 데이터 정리")
    cleanup_parser.add_argument("--cleanup-days", type=int, default=365, 
                              help="보관할 데이터 기간 (일, 기본: 365일)")
    
    args = parser.parse_args()
    
    # 전체 업데이트 플래그 처리
    if args.full:
        args.incremental = False
    
    if not args.command:
        parser.print_help()
        return
    
    print("🚀 주식 히스토리 데이터 업데이트 시스템")
    print("=" * 50)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 사전 점검
    if not check_cybos_connection():
        return
    
    if not check_database():
        return
    
    # 데이터베이스 초기화 (히스토리 테이블 포함)
    print("\n🗄️  데이터베이스 초기화 중...")
    initialize_database()
    
    # 명령어별 실행
    command_map = {
        "daily": run_daily_update,
        "weekly": run_weekly_update, 
        "monthly": run_monthly_update,
        "kospi200": run_kospi200_daily,
        "cleanup": cleanup_old_history
    }
    
    if args.command in command_map:
        try:
            start_time = datetime.now()
            result = command_map[args.command](args)
            end_time = datetime.now()
            
            duration = end_time - start_time
            
            print(f"\n⏱️  총 소요 시간: {duration}")
            print(f"🎯 최종 결과: {result}")
            
        except KeyboardInterrupt:
            print("\n⚠️  사용자에 의해 중단되었습니다.")
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
    else:
        print(f"❌ 알 수 없는 명령어: {args.command}")


if __name__ == "__main__":
    main()

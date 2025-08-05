"""
Update Stock Prices - 주식 시세 업데이트 스크립트

매일 배치로 실행할 수 있는 시세 업데이트 스크립트입니다.
안전한 요청 제한과 불규칙한 지연 시간을 적용합니다.
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
    from src.database.models.price import PriceTable
    from src.services.price_update_service import PriceUpdateService, run_price_update
    from src.database.models.stock import MarketKind
except ImportError as e:
    print(f"Import error: {e}")
    print("Please make sure you're running in the correct environment")
    sys.exit(1)


def check_cybos_connection():
    """Cybos Plus 연결 확인"""
    try:
        cybos = win32com.client.Dispatch("CpUtil.CpCybos")
        if cybos.IsConnect != 1:
            print("❌ Cybos Plus가 연결되지 않았습니다.")
            print("   HTS를 실행하고 로그인 후 다시 시도하세요.")
            return False
        
        # 서버 타입 확인
        server_type = cybos.ServerType
        server_names = {0: "연결 끊김", 1: "CybosPlus", 2: "HTS 일반"}
        print(f"✅ Cybos Plus 연결 확인됨 (서버: {server_names.get(server_type, '알 수 없음')})")
        
        # 요청 제한 확인
        remain_count = cybos.GetLimitRemainCount(1)  # 시세 요청
        remain_time = cybos.LimitRequestRemainTime
        
        print(f"📊 요청 제한 현황:")
        print(f"   남은 요청 수: {remain_count}")
        print(f"   제한 재설정까지: {remain_time/1000:.1f}초")
        
        return True
    except Exception as e:
        print(f"❌ Cybos Plus 연결 확인 실패: {e}")
        return False


def setup_database():
    """데이터베이스 설정"""
    print("🗄️  데이터베이스 설정 중...")
    
    # 데이터베이스 초기화
    initialize_database()
    
    # Price 테이블이 없다면 생성
    from src.database.connection import get_connection_context
    with get_connection_context() as conn:
        PriceTable.create_table(conn)
        PriceTable.create_indexes(conn)
    
    # 데이터베이스 정보 출력
    db_info = get_db_info()
    print(f"   DB 경로: {db_info['db_path']}")
    print(f"   종목 수: {db_info.get('stocks_count', 'N/A'):,}")
    print(f"   기존 시세 레코드: {db_info.get('prices_count', 0):,}")


def run_kospi_update(args):
    """KOSPI 종목 시세 업데이트"""
    print("📈 KOSPI 종목 시세 업데이트")
    
    service = PriceUpdateService(
        batch_size=args.batch_size,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        max_requests_per_hour=args.max_requests
    )
    
    result = service.run_full_update(
        market_kinds=[MarketKind.KOSPI],
        dry_run=args.dry_run
    )
    
    return result


def run_kosdaq_update(args):
    """KOSDAQ 종목 시세 업데이트"""
    print("📈 KOSDAQ 종목 시세 업데이트")
    
    service = PriceUpdateService(
        batch_size=args.batch_size,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        max_requests_per_hour=args.max_requests
    )
    
    result = service.run_full_update(
        market_kinds=[MarketKind.KOSDAQ],
        dry_run=args.dry_run
    )
    
    return result


def run_all_update(args):
    """전체 시장 시세 업데이트"""
    print("📈 전체 시장 시세 업데이트")
    
    service = PriceUpdateService(
        batch_size=args.batch_size,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        max_requests_per_hour=args.max_requests
    )
    
    result = service.run_full_update(
        market_kinds=[MarketKind.KOSPI, MarketKind.KOSDAQ],
        dry_run=args.dry_run
    )
    
    return result


def cleanup_old_data(args):
    """오래된 시세 데이터 정리"""
    print(f"🗑️  {args.cleanup_days}일 이전 시세 데이터 정리")
    
    service = PriceUpdateService()
    deleted_count = service.cleanup_old_prices(args.cleanup_days)
    
    print(f"✅ 정리 완료: {deleted_count:,}건 삭제")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="주식 시세 업데이트 스크립트")
    
    # 실행 모드
    parser.add_argument("command", choices=["kospi", "kosdaq", "all", "cleanup"], 
                       help="실행할 명령")
    
    # 배치 설정
    parser.add_argument("--batch-size", type=int, default=30,
                       help="배치 크기 (기본: 30)")
    parser.add_argument("--min-delay", type=float, default=2.0,
                       help="최소 지연 시간(초) (기본: 2.0)")
    parser.add_argument("--max-delay", type=float, default=5.0,
                       help="최대 지연 시간(초) (기본: 5.0)")
    parser.add_argument("--max-requests", type=int, default=500,
                       help="시간당 최대 요청 수 (기본: 500)")
    
    # 기타 옵션
    parser.add_argument("--dry-run", action="store_true",
                       help="실제 업데이트 없이 시뮬레이션만 실행")
    parser.add_argument("--cleanup-days", type=int, default=30,
                       help="정리할 데이터 기준 일수 (기본: 30일)")
    
    args = parser.parse_args()
    
    print("🚀 주식 시세 업데이트 스크립트")
    print("=" * 50)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"명령: {args.command}")
    
    if args.dry_run:
        print("🔍 DRY RUN 모드")
    
    try:
        # 연결 확인 (cleanup 명령은 제외)
        if args.command != "cleanup":
            if not check_cybos_connection():
                return 1
        
        # 데이터베이스 설정
        setup_database()
        
        # 명령 실행
        result = None
        
        if args.command == "kospi":
            result = run_kospi_update(args)
        elif args.command == "kosdaq":
            result = run_kosdaq_update(args)
        elif args.command == "all":
            result = run_all_update(args)
        elif args.command == "cleanup":
            cleanup_old_data(args)
            return 0
        
        # 결과 검증
        if result:
            if args.dry_run:
                print("\n✅ DRY RUN 모드 실행이 성공적으로 완료되었습니다!")
                return 0
            elif result.get("successful_stocks", 0) > 0:
                print("\n✅ 시세 업데이트가 성공적으로 완료되었습니다!")
                return 0
            else:
                print("\n⚠️  시세 업데이트 중 문제가 발생했습니다.")
                return 1
        else:
            print("\n⚠️  시세 업데이트 중 문제가 발생했습니다.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  사용자에 의해 중단되었습니다.")
        return 1
    except Exception as e:
        print(f"\n❌ 시스템 오류: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

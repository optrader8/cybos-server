"""
Update Stock Prices - 주식 시세 업데이트 스크립트

매일 배치로 실행할 수 있는 시세 업데이트 스크립트입니다.
안전한 요청 제한과 불규칙한 지연 시간을 적용합니다.
"""

import sys
import argparse
import sqlite3
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


def run_kospi200_update(args):
    """KOSPI200 종목 시세 업데이트"""
    print("📈 KOSPI200 종목 시세 업데이트")
    print("� 알려진 KOSPI200 대표 종목들로 테스트 실행")
    
    # 현재 확실히 알고 있는 KOSPI200 종목들 (모든 코드에 A 접두사 적용)
    # 더 많은 KOSPI200 종목 추가
    kospi200_codes = [
        'A005930',
        'A000660',
        'A207940',
        'A005380',
        'A006400',
        'A051910',
        'A003550',
        'A000270',
        'A068270',
        'A012330',
        'A066570',
        'A096770',
        'A028260',
        'A323410',
        'A035420',
        'A035720',
        'A017670',
        'A033780',
        'A090430',
        'A003490',
        'A018260',
        'A034220',
        'A015760',
        'A105560',
        'A055550',
        'A086790',
        'A316140',
        'A024110',
        'A032830',
        'A009150',
        'A047050',
        'A011070',
        'A000810',
        'A010950',
        'A009540',
        'A034020',
        'A267250',
        'A010140',
        'A011200',
        'A138040',
        'A271560',
        'A030200',
        'A004370',
        'A010130',
        'A009830',
        'A000720',
        'A161390',
        'A042670',
        'A180640',
        'A004020',
        'A003230',
        'A267260',
        'A003670',
        'A241560',
        'A036570',
        'A018880',
        'A000880',
        'A011780',
        'A139480',
        'A004990',
        'A285130',
        'A034730',
        'A008770',
        'A000120',
        'A012450',
        'A000100',
        'A302440',
        'A097950',
        'A002380',
        'A195870',
        'A001040',
        'A010620',
        'A008930',
        'A064350',
        'A006260',
        'A003520',
        'A009970',
        'A002710',
        'A014680',
        'A128940',
        'A079550',
        'A006800',
        'A036460',
        'A020150',
        'A005490',
        'A192820',
        'A114090',
        'A006360',
        'A008560',
        'A298020',
        'A003410',
        'A375500',
        'A298050',
        'A014820',
        'A006110',
        'A051600',
        'A047040',
        'A028050',
        'A069960',
        'A192080',
        'A001450',
        'A004800',
        'A004170',
        'A097230',
        'A005940',
        'A011810',
        'A001120',
        'A010780',
        'A001680',
        'A003030',
        'A071050',
        'A023530',
        'A000150',
        'A003000',
        'A298040',
        'A006280',
        'A001430',
        'A006650',
        'A021240',
        'A000670',
        'A137310',
        'A008350',
        'A005300',
        'A003480',
        'A000240',
        'A004000',
        'A090080',
        'A012750',
        'A352820',
        'A000040',
        'A006840',
        'A005690',
        'A009240',
        'A004490',
        'A002320',
        'A001800',
        'A108320',
        'A005420',
        'A000050',
        'A001740',
        'A003620',
        'A007070',
        'A344820',
        'A175330',
        'A069620',
        'A003240',
        'A018670',
        'A002790',
        'A047810',
        'A081660',
        'A000370',
        'A051900',
        'A018250',
        'A138930',
        'A004430',
        'A005250',
        'A034300',
        'A192400',
        'A002350',
        'A003850',
        'A005385',
        'A008730',
        'A000390',
        'A010060',
        'A004250',
        'A000210',
        'A267270',
        'A298000',
        'A002600',
        'A002900',
        'A007310',
        'A336260',
        'A000640',
        'A008060',
        'A020560',
        'A298180',
        'A000980',
        'A006980',
        'A018470',
        'A280360',
        'A003090',
        'A002720',
        'A025540',
        'A016360',
        'A007540',
        'A004560',
        'A111770',
        'A081000',
        'A026940',
        'A044380',
        'A000500',
        'A005180',
        'A003160',
        'A271940',
        'A000680',
        'A078930',
        'A001060',
        'A025750',
        'A282330',
        'A450080',
        'A101530',
        'A010040',
        'A003570',
        'A001210',
        'A204320',
        'A248070',
        'A093370',
        'A003300',
        'A001500',
        'A001250'
    ]
    
    print(f"🎯 대표 KOSPI200 종목 {len(kospi200_codes)}개 대상")
    
    if args.dry_run:
        print(f"📊 예상 처리 시간: {len(kospi200_codes) * (args.max_delay + args.min_delay) / 2 / 60:.1f}분")
        return {"total_stocks": len(kospi200_codes), "successful_stocks": len(kospi200_codes)}
    
    # 시세 업데이트 서비스로 종목 목록 직접 전달
    service = PriceUpdateService(
        batch_size=args.batch_size,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        max_requests_per_hour=args.max_requests
    )
    
    result = service.update_prices_for_stocks(kospi200_codes, dry_run=args.dry_run)
    
    return result


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
    parser.add_argument("command", choices=["kospi", "kospi200", "kosdaq", "all", "cleanup"], 
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
        elif args.command == "kospi200":
            result = run_kospi200_update(args)
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

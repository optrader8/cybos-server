"""
Stock Database Test - 종목 정보 DB 저장 테스트

Cybos Plus에서 종목 정보를 수집하여 SQLite DB에 저장하는 테스트 스크립트입니다.
"""

import sys
import time
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import win32com.client
    from src.database.connection import get_connection_context, initialize_database, get_db_info
    from src.database.models.stock import StockTable, MarketKind
    from src.cybos.codes.fetcher import get_fetcher, get_stock_counts
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
        
        print("✅ Cybos Plus 연결 확인됨")
        return True
    except Exception as e:
        print(f"❌ Cybos Plus 연결 확인 실패: {e}")
        return False


def test_stock_counts():
    """종목 수 확인 테스트"""
    print("\n=== 종목 수 확인 테스트 ===")
    
    try:
        counts = get_stock_counts()
        print(f"KOSPI 종목 수: {counts['kospi']}")
        print(f"KOSDAQ 종목 수: {counts['kosdaq']}")
        print(f"FREEBOARD 종목 수: {counts['freeboard']}")
        print(f"KRX 종목 수: {counts['krx']}")
        print(f"전체 종목 수: {counts['total']}")
        return True
    except Exception as e:
        print(f"❌ 종목 수 확인 실패: {e}")
        return False


def test_basic_stock_info():
    """기본 종목 정보 테스트"""
    print("\n=== 기본 종목 정보 테스트 ===")
    
    try:
        fetcher = get_fetcher()
        
        # 샘플 종목들 (유명한 종목들)
        test_codes = ["005930", "000660", "035420", "051910"]  # 삼성전자, SK하이닉스, NAVER, LG화학
        
        for code in test_codes:
            stock_info = fetcher.get_basic_stock_info(code)
            if stock_info:
                print(f"  {code}: {stock_info.name} (시장: {stock_info.market_kind})")
            else:
                print(f"  {code}: 정보 조회 실패")
        
        return True
    except Exception as e:
        print(f"❌ 기본 종목 정보 테스트 실패: {e}")
        return False


def test_detailed_stock_info():
    """상세 종목 정보 테스트"""
    print("\n=== 상세 종목 정보 테스트 ===")
    
    try:
        fetcher = get_fetcher()
        
        # 삼성전자 상세 정보 테스트
        stock_info = fetcher.get_detailed_stock_info("005930")
        if stock_info:
            print(f"종목코드: {stock_info.code}")
            print(f"종목명: {stock_info.name}")
            print(f"시장구분: {stock_info.market_kind}")
            print(f"부구분: {stock_info.section_kind}")
            print(f"기준가: {stock_info.std_price:,}원")
            print(f"상한가: {stock_info.max_price:,}원")
            print(f"하한가: {stock_info.min_price:,}원")
            print(f"거래단위: {stock_info.meme_min}")
            print(f"업종코드: {stock_info.industry_code}")
            print(f"자본금규모: {stock_info.capital_size}")
            return True
        else:
            print("❌ 삼성전자 정보 조회 실패")
            return False
    except Exception as e:
        print(f"❌ 상세 종목 정보 테스트 실패: {e}")
        return False


def test_database_operations():
    """데이터베이스 작업 테스트"""
    print("\n=== 데이터베이스 작업 테스트 ===")
    
    try:
        # DB 초기화
        print("데이터베이스 초기화 중...")
        initialize_database()
        
        # DB 정보 확인
        db_info = get_db_info()
        print(f"DB 경로: {db_info['db_path']}")
        print(f"DB 크기: {db_info['db_size']:,} bytes")
        print(f"테이블 목록: {db_info['tables']}")
        
        # 샘플 종목 DB 저장 테스트
        fetcher = get_fetcher()
        test_codes = ["005930", "000660", "035420"]
        
        with get_connection_context() as conn:
            for code in test_codes:
                stock_info = fetcher.get_detailed_stock_info(code)
                if stock_info:
                    StockTable.insert_stock(conn, stock_info)
                    print(f"  {code} ({stock_info.name}) 저장 완료")
            
            conn.commit()
        
        # 저장된 데이터 확인
        with get_connection_context() as conn:
            count_info = StockTable.count_stocks(conn)
            print(f"저장된 종목 수: {count_info}")
        
        return True
    except Exception as e:
        print(f"❌ 데이터베이스 작업 테스트 실패: {e}")
        return False


def test_bulk_insert_kospi():
    """KOSPI 전체 종목 일괄 저장 테스트"""
    print("\n=== KOSPI 전체 종목 일괄 저장 테스트 ===")
    
    try:
        fetcher = get_fetcher()
        
        # KOSPI 종목만 수집 (기본 정보)
        print("KOSPI 종목 정보 수집 중...")
        start_time = time.time()
        kospi_stocks = fetcher.fetch_market_stocks(MarketKind.KOSPI, detailed=False)
        fetch_time = time.time() - start_time
        
        print(f"수집 완료: {len(kospi_stocks)}개 종목 ({fetch_time:.2f}초)")
        
        # DB에 저장
        print("데이터베이스 저장 중...")
        start_time = time.time()
        
        with get_connection_context() as conn:
            for i, stock_info in enumerate(kospi_stocks):
                StockTable.insert_stock(conn, stock_info)
                
                if (i + 1) % 100 == 0:
                    print(f"  저장 진행: {i + 1}/{len(kospi_stocks)}")
            
            conn.commit()
        
        save_time = time.time() - start_time
        print(f"저장 완료: {len(kospi_stocks)}개 종목 ({save_time:.2f}초)")
        
        # 결과 확인
        with get_connection_context() as conn:
            count_info = StockTable.count_stocks(conn)
            kospi_stocks_db = StockTable.get_stocks_by_market(conn, MarketKind.KOSPI)
            
        print(f"DB 저장된 전체 종목 수: {count_info}")
        print(f"KOSPI 종목 수: {len(kospi_stocks_db)}")
        
        # 몇 개 샘플 출력
        print("\n저장된 KOSPI 종목 샘플:")
        for stock in kospi_stocks_db[:5]:
            print(f"  {stock.code}: {stock.name}")
        
        return True
    except Exception as e:
        print(f"❌ KOSPI 일괄 저장 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 함수"""
    print("🚀 Cybos Plus 종목 정보 DB 저장 테스트 시작")
    print("=" * 50)
    
    # 1. 연결 확인
    if not check_cybos_connection():
        return
    
    # 2. 종목 수 확인
    if not test_stock_counts():
        return
    
    # 3. 기본 종목 정보 테스트
    if not test_basic_stock_info():
        return
    
    # 4. 상세 종목 정보 테스트
    if not test_detailed_stock_info():
        return
    
    # 5. 데이터베이스 작업 테스트
    if not test_database_operations():
        return
    
    # 6. 사용자 선택: KOSPI 전체 저장
    print("\n" + "=" * 50)
    response = input("KOSPI 전체 종목을 DB에 저장하시겠습니까? (y/N): ")
    
    if response.lower() == 'y':
        if test_bulk_insert_kospi():
            print("\n✅ 모든 테스트가 성공적으로 완료되었습니다!")
        else:
            print("\n❌ KOSPI 일괄 저장 테스트 실패")
    else:
        print("\n✅ 기본 테스트가 성공적으로 완료되었습니다!")
    
    print("\n📊 최종 데이터베이스 정보:")
    final_info = get_db_info()
    for key, value in final_info.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()

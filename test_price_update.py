"""
Price Update Test - 시세 업데이트 테스트

소수의 종목으로 시세 업데이트 기능을 테스트합니다.
"""

import sys
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import win32com.client
    from src.cybos.price.fetcher import get_price_fetcher
    from src.database.connection import get_connection_context
    from src.database.models.price import PriceTable
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


def check_cybos_connection():
    """Cybos Plus 연결 확인"""
    try:
        cybos = win32com.client.Dispatch("CpUtil.CpCybos")
        if cybos.IsConnect != 1:
            print("❌ Cybos Plus가 연결되지 않았습니다.")
            return False
        
        print("✅ Cybos Plus 연결 확인됨")
        
        # 요청 제한 정보
        remain_count = cybos.GetLimitRemainCount(1)
        remain_time = cybos.LimitRequestRemainTime
        print(f"📊 남은 요청 수: {remain_count}, 재설정까지: {remain_time/1000:.1f}초")
        
        return True
    except Exception as e:
        print(f"❌ 연결 확인 실패: {e}")
        return False


def test_single_price_fetch():
    """단일 종목 시세 조회 테스트"""
    print("\n=== 단일 종목 시세 조회 테스트 ===")
    
    fetcher = get_price_fetcher()
    test_codes = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
    
    for code in test_codes:
        try:
            price_info = fetcher.fetch_single_price(code)
            if price_info:
                print(f"✅ {code} ({price_info.name})")
                print(f"   현재가: {price_info.current_price:,}원")
                print(f"   전일대비: {price_info.change:+,}원")
                print(f"   상태: {price_info.get_status_name()}")
                print(f"   거래량: {price_info.volume:,}주")
            else:
                print(f"❌ {code}: 데이터 조회 실패")
        except Exception as e:
            print(f"❌ {code}: 오류 - {e}")


def test_multiple_price_fetch():
    """여러 종목 시세 일괄 조회 테스트"""
    print("\n=== 여러 종목 시세 일괄 조회 테스트 ===")
    
    fetcher = get_price_fetcher()
    test_codes = ["005930", "000660", "035420", "051910", "005380"]
    
    try:
        prices = fetcher.fetch_multiple_prices_batch(test_codes, len(test_codes))
        
        print(f"📊 조회 결과: {len(prices)}/{len(test_codes)}개 성공")
        
        for i, price in enumerate(prices):
            status_symbol = "📈" if price.change > 0 else "📉" if price.change < 0 else "➡️"
            print(f"   {status_symbol} {price.code} ({price.name}): {price.current_price:,}원 ({price.change:+,})")
            
    except Exception as e:
        print(f"❌ 일괄 조회 실패: {e}")


def test_database_save():
    """데이터베이스 저장 테스트"""
    print("\n=== 데이터베이스 저장 테스트 ===")
    
    # Price 테이블 생성
    with get_connection_context() as conn:
        PriceTable.create_table(conn)
        PriceTable.create_indexes(conn)
    
    # 샘플 시세 조회 및 저장
    fetcher = get_price_fetcher()
    test_code = "005930"  # 삼성전자
    
    try:
        price_info = fetcher.fetch_single_price(test_code)
        if price_info:
            with get_connection_context() as conn:
                PriceTable.insert_price(conn, price_info)
                conn.commit()
                
                # 저장된 데이터 확인
                saved_price = PriceTable.get_latest_price(conn, test_code)
                if saved_price:
                    print(f"✅ 데이터베이스 저장 성공")
                    print(f"   저장된 데이터: {saved_price.code} ({saved_price.name})")
                    print(f"   현재가: {saved_price.current_price:,}원")
                    print(f"   저장 시간: {saved_price.created_at}")
                else:
                    print("❌ 저장된 데이터 조회 실패")
        else:
            print("❌ 시세 조회 실패")
            
    except Exception as e:
        print(f"❌ 데이터베이스 저장 실패: {e}")


def main():
    """메인 테스트 함수"""
    print("🧪 시세 업데이트 기능 테스트")
    print("=" * 50)
    
    # 연결 확인
    if not check_cybos_connection():
        return
    
    # 테스트 실행
    test_single_price_fetch()
    test_multiple_price_fetch()
    test_database_save()
    
    print("\n✅ 모든 테스트 완료!")
    print("\n💡 실제 시세 업데이트 실행 방법:")
    print("   python update_prices.py kospi --dry-run  # KOSPI 시뮬레이션")
    print("   python update_prices.py kospi            # KOSPI 실제 업데이트")
    print("   python update_prices.py all              # 전체 시장 업데이트")


if __name__ == "__main__":
    main()

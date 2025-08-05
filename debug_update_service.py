"""
Price Update Debug - 시세 업데이트 디버깅

업데이트 서비스의 구체적인 오류를 확인합니다.
"""

import sys
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.price_update_service import PriceUpdateService
from src.database.connection import get_connection_context, DatabaseManager
from src.database.models.stock import StockTable

def debug_update_service():
    """업데이트 서비스 디버깅"""
    print("🔍 시세 업데이트 서비스 디버깅")
    print("=" * 50)
    
    try:
        # 데이터베이스 초기화
        print("🗄️  데이터베이스 초기화 중...")
        db_manager = DatabaseManager("data/cybos.db")
        db_manager.initialize_database()
        db_path = str(db_manager.db_path)
        print(f"   DB 경로: {db_path}")
        
        # 종목 데이터 확인
        with get_connection_context(db_path) as conn:
            stock_counts = StockTable.count_stocks(conn)
            total_stocks = sum(stock_counts.values())
            print(f"   종목 수: {total_stocks:,}")
            print(f"   시장별 현황: {stock_counts}")
            
            # KOSPI 종목 몇 개만 가져오기
            kospi_stocks = StockTable.get_stocks_by_market(conn, 1)[:5]  # market_kind는 단일 값
            print(f"   테스트 대상: {len(kospi_stocks)}개 KOSPI 종목")
            
            # 종목 데이터 구조 확인
            if kospi_stocks:
                print(f"\n📋 첫 번째 종목 데이터 구조:")
                first_stock = kospi_stocks[0]
                print(f"   타입: {type(first_stock)}")
                if hasattr(first_stock, '__dict__'):
                    for key, value in first_stock.__dict__.items():
                        print(f"     {key}: {value}")
                elif isinstance(first_stock, dict):
                    for key, value in first_stock.items():
                        print(f"     {key}: {value}")
                
                # StockInfo를 딕셔너리로 변환 (업데이트 서비스에서 필요)
                kospi_stocks_dict = []
                for stock in kospi_stocks:
                    if hasattr(stock, 'to_dict'):
                        kospi_stocks_dict.append(stock.to_dict())
                    elif hasattr(stock, '__dict__'):
                        kospi_stocks_dict.append(stock.__dict__)
                    else:
                        kospi_stocks_dict.append(stock)
                
                print(f"\n📋 변환된 딕셔너리 형태:")
                if kospi_stocks_dict:
                    first_dict = kospi_stocks_dict[0]
                    print(f"   타입: {type(first_dict)}")
                    if isinstance(first_dict, dict):
                        for key, value in list(first_dict.items())[:5]:  # 처음 5개만
                            print(f"     {key}: {value}")
            else:
                kospi_stocks_dict = []
        
        # 업데이트 서비스 생성
        print("\n🚀 업데이트 서비스 초기화...")
        service = PriceUpdateService(batch_size=3, db_path=db_path)
        
        # 작은 배치로 테스트
        print("\n📊 작은 배치 테스트 실행...")
        result = service.update_prices_batch(kospi_stocks_dict)
        
        print(f"✅ 배치 결과: {len(result)}개 성공")
        for price in result:
            print(f"   📈 {price.code} ({price.name}): {price.current_price:,}원")
        
        # 서비스 통계 출력
        print(f"\n📊 서비스 통계:")
        print(f"   총 요청: {service.stats['total_requests']}")
        print(f"   오류 수: {len(service.stats['errors'])}")
        
        if service.stats['errors']:
            print("   오류 목록:")
            for error in service.stats['errors']:
                print(f"     - {error}")
        
    except Exception as e:
        print(f"❌ 디버깅 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_update_service()

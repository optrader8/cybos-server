"""
KOSPI200 종목 처리 디버그
실제로 어떤 종목들이 데이터베이스에서 찾아지는지 확인
"""

import sqlite3
from pathlib import Path
import sys

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_db_info
from src.database.models.stock import StockTable

def debug_kospi200_codes():
    """KOSPI200 종목 코드들이 실제로 데이터베이스에 있는지 확인"""
    
    kospi200_codes = [
        '005930',  # 삼성전자 - 정보통신
        '000660',  # SK하이닉스 - 정보통신
        '207940',  # 삼성바이오로직스 - 건강관리
        '005380',  # 현대차 - 자유소비재
        '006400',  # 삼성SDI - 정보통신
        '051910',  # LG화학 - 에너지화학
        '003550',  # LG - 정보통신
        '000270',  # 기아 - 자유소비재
        '068270',  # 셀트리온 - 건강관리
        '012330',  # 현대모비스 - 자유소비재
        '066570',  # LG전자 - 정보통신
        '096770',  # SK이노베이션 - 에너지화학
        '028260',  # 삼성물산 - 건설
        '323410',  # 카카오뱅크 - 금융
        '000100',  # 유한양행 - 건강관리
    ]
    
    print("🔍 KOSPI200 종목 코드 데이터베이스 확인")
    print("=" * 50)
    
    db_path = get_db_info()['db_path']
    
    found_stocks = []
    missing_stocks = []
    
    with sqlite3.connect(db_path) as conn:
        for code in kospi200_codes:
            # 원본 코드로 조회
            stock_info = StockTable.get_stock(conn, code)
            if stock_info:
                found_stocks.append((code, stock_info.name))
                print(f"✅ {code} | {stock_info.name}")
            else:
                # A 접두사 버전으로 조회
                a_code = f"A{code}"
                stock_info = StockTable.get_stock(conn, a_code)
                if stock_info:
                    found_stocks.append((a_code, stock_info.name))
                    print(f"✅ {a_code} | {stock_info.name}")
                else:
                    missing_stocks.append(code)
                    print(f"❌ {code} | 종목을 찾을 수 없음")
    
    print(f"\n📊 결과 요약:")
    print(f"   찾은 종목: {len(found_stocks)}개")
    print(f"   누락 종목: {len(missing_stocks)}개")
    
    if missing_stocks:
        print(f"\n❌ 누락된 종목들:")
        for code in missing_stocks:
            print(f"   {code}")
    
    if found_stocks:
        print(f"\n✅ 찾은 종목들:")
        for code, name in found_stocks:
            print(f"   {code} | {name}")

if __name__ == "__main__":
    debug_kospi200_codes()

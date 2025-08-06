"""
Check Stock Database - 종목 데이터베이스 확인

현재 데이터베이스에 저장된 종목 정보를 분석하여
KOSPI200 종목을 정확히 식별합니다.
"""

import sys
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_connection_context, DatabaseManager
from src.database.models.stock import StockTable

def analyze_stock_database():
    """종목 데이터베이스 분석"""
    print("🔍 종목 데이터베이스 분석")
    print("=" * 50)
    
    try:
        # 데이터베이스 연결
        db_manager = DatabaseManager("data/cybos.db")
        db_path = str(db_manager.db_path)
        
        with get_connection_context(db_path) as conn:
            # 전체 종목 수 확인
            stock_counts = StockTable.count_stocks(conn)
            print(f"📊 전체 종목 현황: {stock_counts}")
            
            # KOSPI 종목 샘플 확인
            print(f"\n📋 KOSPI 종목 샘플 (처음 10개):")
            kospi_stocks = StockTable.get_stocks_by_market(conn, 1)[:10]
            
            for stock in kospi_stocks:
                print(f"   {stock.code} | {stock.name:15s} | kospi200_kind: {stock.kospi200_kind}")
            
            # kospi200_kind 값 분포 확인
            print(f"\n📊 KOSPI200 종류 분포 확인:")
            cursor = conn.execute("""
                SELECT kospi200_kind, COUNT(*) as count, 
                       GROUP_CONCAT(name, ', ') as sample_names
                FROM stocks 
                WHERE market_kind = 1  -- KOSPI만
                GROUP BY kospi200_kind 
                ORDER BY kospi200_kind
            """)
            
            for row in cursor.fetchall():
                kospi200_kind, count, sample_names = row
                # 샘플 이름을 처음 3개만 표시
                sample_list = sample_names.split(', ')[:3]
                samples = ', '.join(sample_list)
                if len(sample_list) < len(sample_names.split(', ')):
                    samples += f" 등 {count}개"
                
                print(f"   kospi200_kind {kospi200_kind}: {count:4d}개 - {samples}")
            
            # 실제 대표 종목들 확인
            print(f"\n🏢 대표 종목들의 kospi200_kind 확인:")
            major_stocks = [
                "005930",  # 삼성전자
                "000660",  # SK하이닉스  
                "035420",  # NAVER
                "005380",  # 현대차
                "051910",  # LG화학
                "068270",  # 셀트리온
                "006400",  # 삼성SDI
                "035720",  # 카카오
            ]
            
            for code in major_stocks:
                cursor = conn.execute("""
                    SELECT code, name, kospi200_kind 
                    FROM stocks 
                    WHERE code = ?
                """, (code,))
                
                row = cursor.fetchone()
                if row:
                    code, name, kospi200_kind = row
                    print(f"   {code} | {name:15s} | kospi200_kind: {kospi200_kind}")
            
            # KOSPI200으로 추정되는 종목 수 확인
            potential_kospi200_kinds = []
            cursor = conn.execute("""
                SELECT kospi200_kind, COUNT(*) as count
                FROM stocks 
                WHERE market_kind = 1 AND kospi200_kind != 0
                GROUP BY kospi200_kind 
                HAVING count <= 300  -- KOSPI200은 대략 200개 내외
                ORDER BY count DESC
            """)
            
            print(f"\n🎯 KOSPI200 후보 kospi200_kind 값들:")
            for row in cursor.fetchall():
                kospi200_kind, count = row
                potential_kospi200_kinds.append(kospi200_kind)
                print(f"   kospi200_kind {kospi200_kind}: {count}개 종목")
            
            # 가장 가능성 높은 KOSPI200 종목들 표시
            if potential_kospi200_kinds:
                top_kind = potential_kospi200_kinds[0]
                print(f"\n⭐ 가장 가능성 높은 KOSPI200 종목들 (kospi200_kind = {top_kind}):")
                
                cursor = conn.execute("""
                    SELECT code, name 
                    FROM stocks 
                    WHERE market_kind = 1 AND kospi200_kind = ?
                    ORDER BY name
                    LIMIT 20
                """, (top_kind,))
                
                for row in cursor.fetchall():
                    code, name = row
                    print(f"   {code} | {name}")
        
    except Exception as e:
        print(f"❌ 분석 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_stock_database()

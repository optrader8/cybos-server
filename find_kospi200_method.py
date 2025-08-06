"""
KOSPI200 종목 식별 방법 탐색
다양한 필드를 조합해서 KOSPI200 종목을 찾는 방법을 연구
"""

import sqlite3
from pathlib import Path

def analyze_all_fields():
    """모든 필드를 분석해서 KOSPI200 패턴 찾기"""
    
    db_path = Path("data/cybos.db")
    if not db_path.exists():
        print(f"❌ 데이터베이스를 찾을 수 없습니다: {db_path}")
        return
    
    print("🔍 KOSPI200 식별 방법 탐색")
    print("=" * 60)
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        
        # 1. 전체 통계
        cursor = conn.execute("SELECT COUNT(*) as total FROM stocks")
        total = cursor.fetchone()['total']
        print(f"\n📊 전체 종목 수: {total}개")
        
        # 2. market_kind 분석
        print(f"\n📋 market_kind 분포:")
        cursor = conn.execute("""
            SELECT market_kind, COUNT(*) as count 
            FROM stocks 
            GROUP BY market_kind 
            ORDER BY market_kind
        """)
        
        market_stats = cursor.fetchall()
        for stat in market_stats:
            print(f"   market_kind {stat['market_kind']}: {stat['count']}개")
        
        # 3. section_kind 분석  
        print(f"\n📋 section_kind 분포:")
        cursor = conn.execute("""
            SELECT section_kind, COUNT(*) as count 
            FROM stocks 
            GROUP BY section_kind 
            ORDER BY section_kind
        """)
        
        section_stats = cursor.fetchall()
        for stat in section_stats:
            print(f"   section_kind {stat['section_kind']}: {stat['count']}개")
        
        # 4. 주요 대형주들의 모든 필드 확인
        print(f"\n🏢 주요 대형주들의 모든 필드 확인:")
        major_stocks = [
            '005930',  # 삼성전자
            '000660',  # SK하이닉스  
            '035420',  # NAVER
            '207940',  # 삼성바이오로직스
            '005380',  # 현대차
            '006400',  # 삼성SDI
            '051910',  # LG화학
            '003550',  # LG
            '000270',  # 기아
            '068270',  # 셀트리온
        ]
        
        for code in major_stocks:
            cursor = conn.execute("""
                SELECT code, name, market_kind, section_kind, kospi200_kind,
                       control_kind, supervision_kind, stock_status_kind
                FROM stocks 
                WHERE code = ? OR code = ?
            """, (code, f'A{code}'))
            
            stock = cursor.fetchone()
            if stock:
                print(f"   {stock['code']} | {stock['name']:<12}")
                print(f"     market: {stock['market_kind']}, section: {stock['section_kind']}, kospi200: {stock['kospi200_kind']}")
                print(f"     control: {stock['control_kind']}, supervision: {stock['supervision_kind']}, status: {stock['stock_status_kind']}")
            else:
                print(f"   {code} | 종목을 찾을 수 없음")
        
        # 5. market_kind=1, section_kind=1 조합 확인 (KOSPI 일반주일 가능성)
        print(f"\n🎯 market_kind=1 AND section_kind=1 종목들:")
        cursor = conn.execute("""
            SELECT code, name, kospi200_kind
            FROM stocks 
            WHERE market_kind = 1 AND section_kind = 1
            ORDER BY code
            LIMIT 20
        """)
        
        potential_kospi200 = cursor.fetchall()
        print(f"   총 {len(potential_kospi200)}개 (처음 20개만 표시):")
        for stock in potential_kospi200:
            print(f"      {stock['code']} | {stock['name']:<15} | kospi200_kind: {stock['kospi200_kind']}")
        
        # 6. 전체 market_kind=1, section_kind=1 개수 확인
        cursor = conn.execute("""
            SELECT COUNT(*) as count
            FROM stocks 
            WHERE market_kind = 1 AND section_kind = 1
        """)
        total_potential = cursor.fetchone()['count']
        print(f"\n📈 market_kind=1 AND section_kind=1 총 개수: {total_potential}개")
        
        # 7. 다른 조합들도 확인
        combinations = [
            (1, 0),  # market=1, section=0
            (1, 2),  # market=1, section=2  
            (2, 1),  # market=2, section=1
        ]
        
        print(f"\n🔍 다른 market/section 조합들:")
        for market, section in combinations:
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM stocks 
                WHERE market_kind = ? AND section_kind = ?
            """, (market, section))
            count = cursor.fetchone()['count']
            print(f"   market_kind={market}, section_kind={section}: {count}개")

if __name__ == "__main__":
    analyze_all_fields()

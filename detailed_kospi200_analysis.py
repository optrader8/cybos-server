"""
KOSPI200 종목 상세 분석
kospi200_kind 값들의 의미를 파악하기 위한 추가 분석
"""

import sqlite3
from pathlib import Path

def analyze_kospi200_detailed():
    """KOSPI200 종목 상세 분석"""
    
    db_path = Path("data/cybos.db")
    if not db_path.exists():
        print(f"❌ 데이터베이스를 찾을 수 없습니다: {db_path}")
        return
    
    print("🔍 KOSPI200 종목 상세 분석")
    print("=" * 50)
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        
        # 1. kospi200_kind별 상세 분석
        print("\n📊 kospi200_kind별 종목 상세 분석:")
        
        for kind in [5, 11]:
            cursor = conn.execute("""
                SELECT code, name, kospi200_kind 
                FROM stocks 
                WHERE kospi200_kind = ?
                ORDER BY code
            """, (kind,))
            
            stocks = cursor.fetchall()
            print(f"\n   📋 kospi200_kind = {kind} ({len(stocks)}개 종목):")
            
            for stock in stocks:
                print(f"      {stock['code']} | {stock['name']}")
        
        # 2. 주요 대형주들 확인
        print("\n🏢 주요 대형주들의 kospi200_kind 확인:")
        major_stocks = [
            '005930',  # 삼성전자
            '000660',  # SK하이닉스  
            '035420',  # NAVER
            '207940',  # 삼성바이오로직스
            '005380',  # 현대차
            '006400',  # 삼성SDI
            '051910',  # LG화학
            '003550',  # LG
            '096770',  # SK이노베이션
            '028260',  # 삼성물산
            '012330',  # 현대모비스
            '066570',  # LG전자
            '323410',  # 카카오뱅크
            '035900',  # JYP Ent.
            '000270',  # 기아
            '068270',  # 셀트리온
        ]
        
        for code in major_stocks:
            cursor = conn.execute("""
                SELECT code, name, kospi200_kind 
                FROM stocks 
                WHERE code = ? OR code = ?
            """, (code, f'A{code}'))
            
            stock = cursor.fetchone()
            if stock:
                print(f"   {stock['code']} | {stock['name']:<15} | kospi200_kind: {stock['kospi200_kind']}")
            else:
                print(f"   {code} | 종목을 찾을 수 없음")
        
        # 3. kospi200_kind가 0이 아닌 모든 종목 확인
        print(f"\n⭐ kospi200_kind가 0이 아닌 모든 종목:")
        cursor = conn.execute("""
            SELECT code, name, kospi200_kind 
            FROM stocks 
            WHERE kospi200_kind != 0
            ORDER BY kospi200_kind, code
        """)
        
        non_zero_stocks = cursor.fetchall()
        print(f"   총 {len(non_zero_stocks)}개 종목:")
        
        current_kind = None
        for stock in non_zero_stocks:
            if current_kind != stock['kospi200_kind']:
                current_kind = stock['kospi200_kind']
                print(f"\n   📋 kospi200_kind = {current_kind}:")
            
            print(f"      {stock['code']} | {stock['name']}")
        
        # 4. 통계 요약
        print(f"\n📈 통계 요약:")
        cursor = conn.execute("""
            SELECT kospi200_kind, COUNT(*) as count
            FROM stocks 
            WHERE kospi200_kind != 0
            GROUP BY kospi200_kind
            ORDER BY kospi200_kind
        """)
        
        stats = cursor.fetchall()
        total_non_zero = sum(stat['count'] for stat in stats)
        print(f"   kospi200_kind가 0이 아닌 종목: {total_non_zero}개")
        
        for stat in stats:
            print(f"   kospi200_kind {stat['kospi200_kind']}: {stat['count']}개")

if __name__ == "__main__":
    analyze_kospi200_detailed()

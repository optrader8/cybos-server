"""
Test KOSPI200 History Quick - KOSPI200 히스토리 데이터 빠른 검증

간단한 명령어로 빠르게 데이터를 확인할 수 있는 도구입니다.
"""

import sys
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_connection_context
from src.database.models.history import HistoryTable
from src.database.models.stock import StockTable


def quick_check():
    """빠른 데이터 현황 확인"""
    print("🚀 KOSPI200 히스토리 데이터 빠른 확인")
    print("=" * 50)
    
    try:
        with get_connection_context("data/cybos.db") as conn:
            # 전체 히스토리 레코드 수
            cursor = conn.execute(f"SELECT COUNT(*) FROM {HistoryTable.TABLE_NAME}")
            total_records = cursor.fetchone()[0]
            
            # 종목 수
            cursor = conn.execute(f"SELECT COUNT(DISTINCT code) FROM {HistoryTable.TABLE_NAME}")
            stock_count = cursor.fetchone()[0]
            
            # 최신 데이터
            cursor = conn.execute(f"SELECT MAX(date) FROM {HistoryTable.TABLE_NAME}")
            latest_date = cursor.fetchone()[0]
            
            # 최신 데이터가 있는 종목 샘플 (5개)
            cursor = conn.execute(f"""
                SELECT h.code, s.name, COUNT(*) as records
                FROM {HistoryTable.TABLE_NAME} h
                LEFT JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE h.timeframe = 'D'
                GROUP BY h.code, s.name
                ORDER BY records DESC
                LIMIT 5
            """)
            
            sample_stocks = cursor.fetchall()
            
            print(f"📊 전체 현황:")
            print(f"   총 히스토리 레코드: {total_records:,}개")
            print(f"   데이터 보유 종목: {stock_count:,}개")
            print(f"   최신 데이터 날짜: {latest_date}")
            
            print(f"\n📈 데이터 보유량 상위 5개 종목:")
            for stock in sample_stocks:
                code = stock[0]
                name = stock[1] or "Unknown"
                records = stock[2]
                print(f"   {code} ({name}): {records:,}개")
            
            # 간단한 데이터 품질 체크
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM {HistoryTable.TABLE_NAME}
                WHERE timeframe = 'D' AND (
                    high_price < low_price OR 
                    open_price <= 0 OR 
                    close_price <= 0 OR
                    volume < 0
                )
            """)
            
            quality_issues = cursor.fetchone()[0]
            
            print(f"\n🔍 데이터 품질:")
            if quality_issues > 0:
                print(f"   ⚠️  품질 이슈: {quality_issues:,}건")
            else:
                print(f"   ✅ 품질 상태: 양호")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def check_specific_stocks():
    """대표 KOSPI200 종목들 데이터 확인"""
    print("🎯 대표 KOSPI200 종목 데이터 확인")
    print("=" * 50)
    
    # 대표적인 KOSPI200 종목들
    test_stocks = [
        ('005930', '삼성전자'),
        ('000660', 'SK하이닉스'),
        ('207940', '삼성바이오로직스'),
        ('005380', '현대차'),
        ('035420', 'NAVER')
    ]
    
    try:
        with get_connection_context("data/cybos.db") as conn:
            print(f"{'종목코드':<8} {'종목명':<15} {'레코드수':<8} {'최신날짜':<12} {'상태':<8}")
            print("-" * 60)
            
            for code, expected_name in test_stocks:
                cursor = conn.execute(f"""
                    SELECT COUNT(*), MAX(date) FROM {HistoryTable.TABLE_NAME}
                    WHERE code = ? AND timeframe = 'D'
                """, (code,))
                
                result = cursor.fetchone()
                record_count = result[0]
                latest_date = result[1] or "없음"
                
                # 종목명 확인
                cursor = conn.execute(f"SELECT name FROM {StockTable.TABLE_NAME} WHERE code = ?", (code,))
                name_result = cursor.fetchone()
                actual_name = name_result[0] if name_result else "없음"
                
                status = "✅" if record_count > 0 else "❌"
                print(f"{code:<8} {actual_name:<15} {record_count:>7,}개 {latest_date:<12} {status:<8}")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def export_sample_csv():
    """샘플 데이터 CSV 내보내기"""
    print("📤 샘플 데이터 CSV 내보내기")
    print("=" * 50)
    
    try:
        with get_connection_context("data/cybos.db") as conn:
            # 가장 많은 데이터를 가진 종목 찾기
            cursor = conn.execute(f"""
                SELECT code, COUNT(*) as records
                FROM {HistoryTable.TABLE_NAME}
                WHERE timeframe = 'D'
                GROUP BY code
                ORDER BY records DESC
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            if not result:
                print("❌ 히스토리 데이터가 없습니다.")
                return
            
            sample_code = result[0]
            record_count = result[1]
            
            # 종목명 조회
            cursor = conn.execute(f"SELECT name FROM {StockTable.TABLE_NAME} WHERE code = ?", (sample_code,))
            name_result = cursor.fetchone()
            sample_name = name_result[0] if name_result else "Unknown"
            
            print(f"샘플 종목: {sample_code} ({sample_name}) - {record_count:,}개 레코드")
            
            # CSV 내보내기
            from test_kospi200_history import KOSPI200HistoryVerifier
            
            verifier = KOSPI200HistoryVerifier()
            csv_file = verifier.export_stock_to_csv(sample_code)
            
            print(f"✅ CSV 파일 생성: {csv_file}")
            
            # 파일 크기 확인
            file_path = Path(csv_file)
            if file_path.exists():
                file_size = file_path.stat().st_size
                print(f"   파일 크기: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def main():
    """메인 함수"""
    print("🛠️  KOSPI200 히스토리 데이터 빠른 검증")
    print()
    
    # 1. 빠른 현황 확인
    quick_check()
    print()
    
    # 2. 대표 종목들 확인
    check_specific_stocks()
    print()
    
    # 3. 샘플 CSV 내보내기
    export_sample_csv()


if __name__ == "__main__":
    main()

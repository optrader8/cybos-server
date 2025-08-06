"""
Test KOSPI200 History Compare - KOSPI200 히스토리 데이터 비교 검증

배치 실행 전후의 데이터를 비교하거나, 특정 기간의 데이터를 분석합니다.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_connection_context
from src.database.models.history import HistoryTable
from src.database.models.stock import StockTable


def analyze_data_completeness():
    """데이터 완전성 분석"""
    print("📊 KOSPI200 히스토리 데이터 완전성 분석")
    print("=" * 60)
    
    try:
        with get_connection_context("data/cybos.db") as conn:
            # 전체 KOSPI 종목 수
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM {StockTable.TABLE_NAME} 
                WHERE market_kind = 1
            """)
            total_kospi_stocks = cursor.fetchone()[0]
            
            # 히스토리 데이터가 있는 KOSPI 종목 수
            cursor = conn.execute(f"""
                SELECT COUNT(DISTINCT h.code) FROM {HistoryTable.TABLE_NAME} h
                JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE s.market_kind = 1 AND h.timeframe = 'D'
            """)
            kospi_with_history = cursor.fetchone()[0]
            
            # KOSPI200 종목 수 (DB 기준)
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM {StockTable.TABLE_NAME} 
                WHERE market_kind = 1 AND kospi200_kind != 0
            """)
            kospi200_in_db = cursor.fetchone()[0]
            
            # 히스토리 데이터가 있는 KOSPI200 종목 수
            cursor = conn.execute(f"""
                SELECT COUNT(DISTINCT h.code) FROM {HistoryTable.TABLE_NAME} h
                JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE s.market_kind = 1 AND s.kospi200_kind != 0 AND h.timeframe = 'D'
            """)
            kospi200_with_history = cursor.fetchone()[0]
            
            print(f"📈 종목 현황:")
            print(f"   전체 KOSPI 종목: {total_kospi_stocks:,}개")
            print(f"   히스토리 데이터 보유 KOSPI 종목: {kospi_with_history:,}개")
            print(f"   데이터 보유율: {(kospi_with_history/total_kospi_stocks)*100:.1f}%")
            print()
            print(f"   DB상 KOSPI200 종목: {kospi200_in_db:,}개")
            print(f"   히스토리 데이터 보유 KOSPI200 종목: {kospi200_with_history:,}개")
            print(f"   KOSPI200 데이터 보유율: {(kospi200_with_history/max(kospi200_in_db,1))*100:.1f}%")
            
            # 데이터량별 분포
            cursor = conn.execute(f"""
                SELECT 
                    CASE 
                        WHEN record_count >= 5000 THEN '5000개 이상'
                        WHEN record_count >= 1000 THEN '1000-4999개'
                        WHEN record_count >= 500 THEN '500-999개'
                        WHEN record_count >= 100 THEN '100-499개'
                        ELSE '100개 미만'
                    END as range_group,
                    COUNT(*) as stock_count
                FROM (
                    SELECT code, COUNT(*) as record_count
                    FROM {HistoryTable.TABLE_NAME}
                    WHERE timeframe = 'D'
                    GROUP BY code
                ) 
                GROUP BY range_group
                ORDER BY 
                    CASE range_group
                        WHEN '5000개 이상' THEN 1
                        WHEN '1000-4999개' THEN 2
                        WHEN '500-999개' THEN 3
                        WHEN '100-499개' THEN 4
                        ELSE 5
                    END
            """)
            
            print(f"\n📊 데이터량별 종목 분포:")
            for row in cursor.fetchall():
                range_group = row[0]
                stock_count = row[1]
                print(f"   {range_group}: {stock_count:,}개 종목")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def check_recent_batch_results():
    """최근 배치 실행 결과 확인"""
    print("🔍 최근 배치 실행 결과 분석")
    print("=" * 60)
    
    try:
        with get_connection_context("data/cybos.db") as conn:
            # 오늘 업데이트된 데이터
            today = datetime.now().strftime('%Y-%m-%d')
            cursor = conn.execute(f"""
                SELECT COUNT(DISTINCT code) FROM {HistoryTable.TABLE_NAME}
                WHERE timeframe = 'D' AND date(updated_at) = ?
            """, (today,))
            today_updated_stocks = cursor.fetchone()[0]
            
            # 최근 7일간 업데이트된 데이터
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            cursor = conn.execute(f"""
                SELECT COUNT(DISTINCT code) FROM {HistoryTable.TABLE_NAME}
                WHERE timeframe = 'D' AND date(updated_at) >= ?
            """, (week_ago,))
            week_updated_stocks = cursor.fetchone()[0]
            
            # 최근 업데이트 시간별 분포
            cursor = conn.execute(f"""
                SELECT 
                    date(updated_at) as update_date,
                    COUNT(DISTINCT code) as stock_count,
                    COUNT(*) as record_count
                FROM {HistoryTable.TABLE_NAME}
                WHERE timeframe = 'D' AND date(updated_at) >= ?
                GROUP BY date(updated_at)
                ORDER BY update_date DESC
                LIMIT 10
            """, (week_ago,))
            
            update_history = cursor.fetchall()
            
            print(f"📅 업데이트 현황:")
            print(f"   오늘 업데이트된 종목: {today_updated_stocks:,}개")
            print(f"   최근 7일 업데이트된 종목: {week_updated_stocks:,}개")
            
            if update_history:
                print(f"\n📊 일별 업데이트 내역:")
                print(f"{'날짜':<12} {'종목수':<8} {'레코드수':<10}")
                print("-" * 35)
                for row in update_history:
                    update_date = row[0]
                    stock_count = row[1]
                    record_count = row[2]
                    print(f"{update_date:<12} {stock_count:>7,}개 {record_count:>9,}개")
            
            # 가장 최근에 데이터가 업데이트된 종목들
            cursor = conn.execute(f"""
                SELECT h.code, s.name, MAX(h.updated_at) as latest_update, COUNT(*) as records
                FROM {HistoryTable.TABLE_NAME} h
                LEFT JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE h.timeframe = 'D'
                GROUP BY h.code, s.name
                ORDER BY latest_update DESC
                LIMIT 10
            """)
            
            recent_updates = cursor.fetchall()
            
            print(f"\n📈 최근 업데이트 종목 (상위 10개):")
            print(f"{'종목코드':<8} {'종목명':<15} {'레코드수':<8} {'최종업데이트':<20}")
            print("-" * 60)
            for row in recent_updates:
                code = row[0]
                name = row[1] or "Unknown"
                records = row[3]
                latest_update = row[2][:19] if row[2] else "Unknown"  # 초 단위까지만
                print(f"{code:<8} {name:<15} {records:>7,}개 {latest_update:<20}")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def find_missing_kospi200():
    """누락된 KOSPI200 종목 찾기"""
    print("🔍 누락된 KOSPI200 종목 찾기")
    print("=" * 60)
    
    # 알려진 KOSPI200 대표 종목들
    known_kospi200 = [
        '005930', '000660', '207940', '005380', '006400',
        '051910', '003550', '000270', '068270', '012330',
        '066570', '096770', '028260', '323410', '035420',
        '035720', '017670', '033780', '003670', '316140'
    ]
    
    try:
        with get_connection_context("data/cybos.db") as conn:
            print(f"🎯 알려진 KOSPI200 대표 종목 {len(known_kospi200)}개 검사:")
            print(f"{'종목코드':<8} {'종목명':<15} {'히스토리':<8} {'상태':<10}")
            print("-" * 50)
            
            missing_count = 0
            total_records = 0
            
            for code in known_kospi200:
                # 종목 정보 조회
                cursor = conn.execute(f"SELECT name FROM {StockTable.TABLE_NAME} WHERE code = ?", (code,))
                stock_result = cursor.fetchone()
                name = stock_result[0] if stock_result else "없음"
                
                # 히스토리 데이터 조회
                cursor = conn.execute(f"""
                    SELECT COUNT(*) FROM {HistoryTable.TABLE_NAME}
                    WHERE code = ? AND timeframe = 'D'
                """, (code,))
                record_count = cursor.fetchone()[0]
                
                if record_count > 0:
                    status = "✅ 있음"
                    total_records += record_count
                else:
                    status = "❌ 없음"
                    missing_count += 1
                
                print(f"{code:<8} {name:<15} {record_count:>7,}개 {status:<10}")
            
            print(f"\n📊 검사 결과:")
            print(f"   검사 종목: {len(known_kospi200)}개")
            print(f"   데이터 있음: {len(known_kospi200) - missing_count}개")
            print(f"   데이터 없음: {missing_count}개")
            print(f"   총 레코드: {total_records:,}개")
            print(f"   완성도: {((len(known_kospi200) - missing_count) / len(known_kospi200) * 100):.1f}%")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def validate_data_integrity():
    """데이터 무결성 검증"""
    print("🔍 데이터 무결성 검증")
    print("=" * 60)
    
    try:
        with get_connection_context("data/cybos.db") as conn:
            # 1. 중복 데이터 검사
            cursor = conn.execute(f"""
                SELECT code, date, COUNT(*) as duplicate_count
                FROM {HistoryTable.TABLE_NAME}
                WHERE timeframe = 'D'
                GROUP BY code, date
                HAVING COUNT(*) > 1
                LIMIT 10
            """)
            
            duplicates = cursor.fetchall()
            
            # 2. 가격 데이터 이상 검사
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM {HistoryTable.TABLE_NAME}
                WHERE timeframe = 'D' AND (
                    high_price < low_price OR
                    open_price <= 0 OR
                    close_price <= 0 OR
                    high_price <= 0 OR
                    low_price <= 0
                )
            """)
            
            price_issues = cursor.fetchone()[0]
            
            # 3. 거래량 이상 검사
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM {HistoryTable.TABLE_NAME}
                WHERE timeframe = 'D' AND volume < 0
            """)
            
            volume_issues = cursor.fetchone()[0]
            
            # 4. 날짜 형식 검사
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM {HistoryTable.TABLE_NAME}
                WHERE timeframe = 'D' AND (
                    length(date) != 10 OR
                    date NOT LIKE '____-__-__'
                )
            """)
            
            date_issues = cursor.fetchone()[0]
            
            print(f"📊 무결성 검증 결과:")
            print(f"   중복 데이터: {len(duplicates)}건")
            print(f"   가격 데이터 이상: {price_issues:,}건")
            print(f"   거래량 이상: {volume_issues:,}건")
            print(f"   날짜 형식 이상: {date_issues:,}건")
            
            if duplicates:
                print(f"\n⚠️  중복 데이터 샘플:")
                for dup in duplicates:
                    print(f"     {dup[0]} ({dup[1]}): {dup[2]}건 중복")
            
            total_issues = len(duplicates) + price_issues + volume_issues + date_issues
            if total_issues == 0:
                print(f"\n✅ 데이터 무결성: 양호")
            else:
                print(f"\n⚠️  총 {total_issues:,}건의 무결성 이슈 발견")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def main():
    """메인 함수"""
    print("🛠️  KOSPI200 히스토리 데이터 비교 검증")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. 데이터 완전성 분석
    analyze_data_completeness()
    print()
    
    # 2. 최근 배치 결과 확인
    check_recent_batch_results()
    print()
    
    # 3. 누락된 KOSPI200 종목 찾기
    find_missing_kospi200()
    print()
    
    # 4. 데이터 무결성 검증
    validate_data_integrity()


if __name__ == "__main__":
    main()

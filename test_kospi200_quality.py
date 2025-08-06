"""
Test KOSPI200 Data Quality - KOSPI200 히스토리 데이터 품질 분석

수집된 데이터의 품질과 일관성을 자세히 분석합니다.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_connection_context
from src.database.models.history import HistoryTable
from src.database.models.stock import StockTable


def analyze_data_gaps():
    """데이터 공백 분석"""
    print("📊 데이터 연속성 및 공백 분석")
    print("=" * 60)
    
    try:
        with get_connection_context("data/cybos.db") as conn:
            # 종목별 최신 데이터와 최오래된 데이터
            cursor = conn.execute(f"""
                SELECT 
                    h.code,
                    s.name,
                    MIN(h.date) as oldest_date,
                    MAX(h.date) as latest_date,
                    COUNT(*) as total_records,
                    JULIANDAY(MAX(h.date)) - JULIANDAY(MIN(h.date)) as date_span_days
                FROM {HistoryTable.TABLE_NAME} h
                LEFT JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE h.timeframe = 'D' AND s.market_kind = 1 AND s.kospi200_kind != 0
                GROUP BY h.code, s.name
                ORDER BY date_span_days DESC
                LIMIT 20
            """)
            
            print(f"📈 KOSPI200 종목별 데이터 범위 (상위 20개):")
            print(f"{'종목코드':<8} {'종목명':<12} {'최오래된날짜':<12} {'최신날짜':<12} {'레코드':<8} {'기간(일)':<8}")
            print("-" * 75)
            
            total_stocks = 0
            avg_records = 0
            
            for row in cursor.fetchall():
                code = row[0]
                name = (row[1] or "Unknown")[:11]  # 최대 11자
                oldest = row[2]
                latest = row[3]
                records = row[4]
                span_days = int(row[5]) if row[5] else 0
                
                print(f"{code:<8} {name:<12} {oldest:<12} {latest:<12} {records:>7,}개 {span_days:>7}일")
                
                total_stocks += 1
                avg_records += records
            
            if total_stocks > 0:
                print(f"\n📊 요약:")
                print(f"   분석 종목: {total_stocks}개")
                print(f"   평균 레코드: {avg_records // total_stocks:,}개")
            
            # 최신 데이터가 오래된 종목 찾기
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            cursor = conn.execute(f"""
                SELECT 
                    h.code,
                    s.name,
                    MAX(h.date) as latest_date,
                    COUNT(*) as records
                FROM {HistoryTable.TABLE_NAME} h
                LEFT JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE h.timeframe = 'D' AND s.market_kind = 1 AND s.kospi200_kind != 0
                GROUP BY h.code, s.name
                HAVING MAX(h.date) < ?
                ORDER BY latest_date
                LIMIT 10
            """, (week_ago,))
            
            stale_data = cursor.fetchall()
            
            if stale_data:
                print(f"\n⚠️  오래된 데이터 종목 ({len(stale_data)}개):")
                print(f"{'종목코드':<8} {'종목명':<15} {'최신날짜':<12} {'레코드':<8}")
                print("-" * 50)
                for row in stale_data:
                    code = row[0]
                    name = (row[1] or "Unknown")[:14]
                    latest = row[2]
                    records = row[3]
                    print(f"{code:<8} {name:<15} {latest:<12} {records:>7,}개")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def analyze_price_patterns():
    """가격 패턴 분석"""
    print("📊 가격 데이터 패턴 분석")
    print("=" * 60)
    
    try:
        with get_connection_context("data/cybos.db") as conn:
            # 가격 범위별 분포
            cursor = conn.execute(f"""
                SELECT 
                    CASE 
                        WHEN close_price >= 100000 THEN '100,000원 이상'
                        WHEN close_price >= 50000 THEN '50,000-99,999원'
                        WHEN close_price >= 10000 THEN '10,000-49,999원'
                        WHEN close_price >= 1000 THEN '1,000-9,999원'
                        ELSE '1,000원 미만'
                    END as price_range,
                    COUNT(*) as record_count,
                    COUNT(DISTINCT code) as stock_count,
                    AVG(volume) as avg_volume
                FROM {HistoryTable.TABLE_NAME} h
                JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE h.timeframe = 'D' AND s.market_kind = 1 AND s.kospi200_kind != 0
                GROUP BY 
                    CASE 
                        WHEN close_price >= 100000 THEN '100,000원 이상'
                        WHEN close_price >= 50000 THEN '50,000-99,999원'
                        WHEN close_price >= 10000 THEN '10,000-49,999원'
                        WHEN close_price >= 1000 THEN '1,000-9,999원'
                        ELSE '1,000원 미만'
                    END
                ORDER BY 
                    CASE 
                        WHEN close_price >= 100000 THEN 1
                        WHEN close_price >= 50000 THEN 2
                        WHEN close_price >= 10000 THEN 3
                        WHEN close_price >= 1000 THEN 4
                        ELSE 5
                    END
            """)
            
            print(f"💰 가격대별 데이터 분포:")
            print(f"{'가격대':<15} {'레코드수':<12} {'종목수':<8} {'평균거래량':<12}")
            print("-" * 55)
            
            for row in cursor.fetchall():
                price_range = row[0]
                record_count = row[1]
                stock_count = row[2]
                avg_volume = int(row[3]) if row[3] else 0
                
                print(f"{price_range:<15} {record_count:>11,}개 {stock_count:>7}개 {avg_volume:>11,}주")
            
            # 극단적 가격 움직임 찾기
            cursor = conn.execute(f"""
                SELECT 
                    h.code,
                    s.name,
                    h.date,
                    h.open_price,
                    h.high_price,
                    h.low_price,
                    h.close_price,
                    ((h.high_price - h.low_price) / h.close_price * 100) as volatility
                FROM {HistoryTable.TABLE_NAME} h
                LEFT JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE h.timeframe = 'D' AND s.market_kind = 1 AND s.kospi200_kind != 0
                  AND ((h.high_price - h.low_price) / h.close_price * 100) > 15
                ORDER BY volatility DESC
                LIMIT 10
            """)
            
            extreme_moves = cursor.fetchall()
            
            if extreme_moves:
                print(f"\n📈 극단적 변동성 (15% 이상, 상위 10개):")
                print(f"{'종목코드':<8} {'종목명':<10} {'날짜':<12} {'변동폭':<8} {'종가':<10}")
                print("-" * 55)
                
                for row in extreme_moves:
                    code = row[0]
                    name = (row[1] or "Unknown")[:9]
                    date = row[2]
                    volatility = row[7]
                    close_price = int(row[6])
                    
                    print(f"{code:<8} {name:<10} {date:<12} {volatility:>7.1f}% {close_price:>9,}원")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def analyze_volume_patterns():
    """거래량 패턴 분석"""
    print("📊 거래량 패턴 분석")
    print("=" * 60)
    
    try:
        with get_connection_context("data/cybos.db") as conn:
            # 거래량별 분포
            cursor = conn.execute(f"""
                SELECT 
                    CASE 
                        WHEN volume >= 10000000 THEN '1천만주 이상'
                        WHEN volume >= 1000000 THEN '100만-999만주'
                        WHEN volume >= 100000 THEN '10만-99만주'
                        WHEN volume >= 10000 THEN '1만-9만주'
                        WHEN volume > 0 THEN '1-9999주'
                        ELSE '거래없음'
                    END as volume_range,
                    COUNT(*) as record_count,
                    COUNT(DISTINCT code) as stock_count
                FROM {HistoryTable.TABLE_NAME} h
                JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE h.timeframe = 'D' AND s.market_kind = 1 AND s.kospi200_kind != 0
                GROUP BY 
                    CASE 
                        WHEN volume >= 10000000 THEN '1천만주 이상'
                        WHEN volume >= 1000000 THEN '100만-999만주'
                        WHEN volume >= 100000 THEN '10만-99만주'
                        WHEN volume >= 10000 THEN '1만-9만주'
                        WHEN volume > 0 THEN '1-9999주'
                        ELSE '거래없음'
                    END
                ORDER BY 
                    CASE 
                        WHEN volume >= 10000000 THEN 1
                        WHEN volume >= 1000000 THEN 2
                        WHEN volume >= 100000 THEN 3
                        WHEN volume >= 10000 THEN 4
                        WHEN volume > 0 THEN 5
                        ELSE 6
                    END
            """)
            
            print(f"📊 거래량 구간별 분포:")
            print(f"{'거래량 구간':<15} {'레코드수':<12} {'종목수':<8}")
            print("-" * 40)
            
            for row in cursor.fetchall():
                volume_range = row[0]
                record_count = row[1]
                stock_count = row[2]
                
                print(f"{volume_range:<15} {record_count:>11,}개 {stock_count:>7}개")
            
            # 거래량 급증 케이스
            cursor = conn.execute(f"""
                WITH daily_avg AS (
                    SELECT code, AVG(volume) as avg_volume
                    FROM {HistoryTable.TABLE_NAME}
                    WHERE timeframe = 'D'
                    GROUP BY code
                    HAVING COUNT(*) >= 10
                )
                SELECT 
                    h.code,
                    s.name,
                    h.date,
                    h.volume,
                    da.avg_volume,
                    (h.volume / da.avg_volume) as volume_ratio
                FROM {HistoryTable.TABLE_NAME} h
                JOIN daily_avg da ON h.code = da.code
                LEFT JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE h.timeframe = 'D' 
                  AND s.market_kind = 1 AND s.kospi200_kind != 0
                  AND da.avg_volume > 0
                  AND (h.volume / da.avg_volume) > 10
                ORDER BY volume_ratio DESC
                LIMIT 10
            """)
            
            volume_spikes = cursor.fetchall()
            
            if volume_spikes:
                print(f"\n📈 거래량 급증 (평균 대비 10배 이상, 상위 10개):")
                print(f"{'종목코드':<8} {'종목명':<10} {'날짜':<12} {'거래량':<12} {'배수':<8}")
                print("-" * 58)
                
                for row in volume_spikes:
                    code = row[0]
                    name = (row[1] or "Unknown")[:9]
                    date = row[2]
                    volume = int(row[3])
                    ratio = row[5]
                    
                    print(f"{code:<8} {name:<10} {date:<12} {volume:>11,}주 {ratio:>7.1f}배")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def analyze_update_patterns():
    """업데이트 패턴 분석"""
    print("📊 데이터 업데이트 패턴 분석")
    print("=" * 60)
    
    try:
        with get_connection_context("data/cybos.db") as conn:
            # 시간대별 업데이트 분포
            cursor = conn.execute(f"""
                SELECT 
                    strftime('%H', updated_at) as hour,
                    COUNT(*) as update_count,
                    COUNT(DISTINCT code) as stock_count
                FROM {HistoryTable.TABLE_NAME} h
                JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE h.timeframe = 'D' 
                  AND s.market_kind = 1 AND s.kospi200_kind != 0
                  AND h.updated_at IS NOT NULL
                GROUP BY strftime('%H', updated_at)
                ORDER BY hour
            """)
            
            print(f"🕐 시간대별 업데이트 분포:")
            print(f"{'시간대':<8} {'업데이트수':<12} {'종목수':<8}")
            print("-" * 35)
            
            total_updates = 0
            
            for row in cursor.fetchall():
                hour = row[0]
                update_count = row[1]
                stock_count = row[2]
                total_updates += update_count
                
                print(f"{hour:>2}시     {update_count:>11,}개 {stock_count:>7}개")
            
            print(f"\n총 업데이트: {total_updates:,}개")
            
            # 최근 업데이트 빈도
            cursor = conn.execute(f"""
                SELECT 
                    date(updated_at) as update_date,
                    COUNT(*) as daily_updates,
                    COUNT(DISTINCT code) as daily_stocks
                FROM {HistoryTable.TABLE_NAME} h
                JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE h.timeframe = 'D' 
                  AND s.market_kind = 1 AND s.kospi200_kind != 0
                  AND date(updated_at) >= date('now', '-30 days')
                GROUP BY date(updated_at)
                ORDER BY update_date DESC
                LIMIT 10
            """)
            
            recent_updates = cursor.fetchall()
            
            if recent_updates:
                print(f"\n📅 최근 30일 업데이트 현황:")
                print(f"{'날짜':<12} {'업데이트수':<12} {'종목수':<8}")
                print("-" * 35)
                
                for row in recent_updates:
                    update_date = row[0]
                    daily_updates = row[1]
                    daily_stocks = row[2]
                    
                    print(f"{update_date:<12} {daily_updates:>11,}개 {daily_stocks:>7}개")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def generate_quality_report():
    """품질 보고서 생성"""
    print("📋 데이터 품질 종합 보고서 생성")
    print("=" * 60)
    
    try:
        with get_connection_context("data/cybos.db") as conn:
            report = {
                "generated_at": datetime.now().isoformat(),
                "summary": {},
                "quality_metrics": {},
                "recommendations": []
            }
            
            # 전체 요약
            cursor = conn.execute(f"""
                SELECT 
                    COUNT(DISTINCT h.code) as unique_stocks,
                    COUNT(*) as total_records,
                    MIN(h.date) as earliest_date,
                    MAX(h.date) as latest_date,
                    MAX(h.updated_at) as last_update
                FROM {HistoryTable.TABLE_NAME} h
                JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE h.timeframe = 'D' AND s.market_kind = 1 AND s.kospi200_kind != 0
            """)
            
            summary = cursor.fetchone()
            report["summary"] = {
                "unique_stocks": summary[0],
                "total_records": summary[1],
                "earliest_date": summary[2],
                "latest_date": summary[3],
                "last_update": summary[4]
            }
            
            # 품질 메트릭
            # 데이터 완성도
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM {StockTable.TABLE_NAME} 
                WHERE market_kind = 1 AND kospi200_kind != 0
            """)
            total_kospi200 = cursor.fetchone()[0]
            
            completeness = (summary[0] / max(total_kospi200, 1)) * 100
            
            # 최신성 (7일 이내 업데이트)
            cursor = conn.execute(f"""
                SELECT COUNT(DISTINCT code) FROM {HistoryTable.TABLE_NAME} h
                JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE h.timeframe = 'D' 
                  AND s.market_kind = 1 AND s.kospi200_kind != 0
                  AND date(h.updated_at) >= date('now', '-7 days')
            """)
            recent_stocks = cursor.fetchone()[0]
            freshness = (recent_stocks / max(summary[0], 1)) * 100
            
            # 데이터 품질 (오류 비율)
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM {HistoryTable.TABLE_NAME} h
                JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE h.timeframe = 'D' 
                  AND s.market_kind = 1 AND s.kospi200_kind != 0
                  AND (h.high_price < h.low_price OR h.close_price <= 0)
            """)
            quality_issues = cursor.fetchone()[0]
            quality_score = ((summary[1] - quality_issues) / max(summary[1], 1)) * 100
            
            report["quality_metrics"] = {
                "completeness": round(completeness, 1),
                "freshness": round(freshness, 1),
                "quality_score": round(quality_score, 1),
                "total_kospi200_expected": total_kospi200,
                "quality_issues_found": quality_issues
            }
            
            # 권장사항
            if completeness < 90:
                report["recommendations"].append(f"완성도 개선 필요: {completeness:.1f}% (목표: 90% 이상)")
            
            if freshness < 80:
                report["recommendations"].append(f"데이터 최신성 개선 필요: {freshness:.1f}% (목표: 80% 이상)")
            
            if quality_score < 99:
                report["recommendations"].append(f"데이터 품질 개선 필요: 오류 {quality_issues}건 발견")
            
            if len(report["recommendations"]) == 0:
                report["recommendations"].append("전반적으로 양호한 데이터 품질을 유지하고 있습니다")
            
            # 보고서 출력
            print(f"📊 품질 메트릭:")
            print(f"   완성도: {report['quality_metrics']['completeness']}%")
            print(f"   최신성: {report['quality_metrics']['freshness']}%")
            print(f"   품질점수: {report['quality_metrics']['quality_score']}%")
            
            print(f"\n📈 데이터 현황:")
            print(f"   수집 종목: {report['summary']['unique_stocks']:,}개 / {total_kospi200}개")
            print(f"   총 레코드: {report['summary']['total_records']:,}개")
            print(f"   데이터 기간: {report['summary']['earliest_date']} ~ {report['summary']['latest_date']}")
            print(f"   최종 업데이트: {report['summary']['last_update'][:19] if report['summary']['last_update'] else 'Unknown'}")
            
            print(f"\n💡 권장사항:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"   {i}. {rec}")
            
            # JSON 파일로 저장
            report_file = f"kospi200_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"\n📄 상세 보고서가 {report_file}에 저장되었습니다.")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def main():
    """메인 함수"""
    print("🔍 KOSPI200 히스토리 데이터 품질 분석")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. 데이터 공백 분석
        analyze_data_gaps()
        print()
        
        # 2. 가격 패턴 분석
        analyze_price_patterns()
        print()
        
        # 3. 거래량 패턴 분석
        analyze_volume_patterns()
        print()
        
        # 4. 업데이트 패턴 분석
        analyze_update_patterns()
        print()
        
        # 5. 품질 보고서 생성
        generate_quality_report()
        
    except Exception as e:
        print(f"❌ 전체 분석 중 오류 발생: {e}")


if __name__ == "__main__":
    main()

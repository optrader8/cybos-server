"""
Test KOSPI200 History Data - KOSPI200 히스토리 데이터 검증 도구

kospi200_daily_batch.py로 저장된 히스토리 데이터를 다양한 방법으로 검증합니다.
"""

import sys
import csv
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_connection_context
from src.database.models.history import HistoryTable, HistoryTimeframe
from src.database.models.stock import StockTable


class KOSPI200HistoryVerifier:
    """KOSPI200 히스토리 데이터 검증 클래스"""
    
    def __init__(self, db_path: str = "data/cybos.db"):
        self.db_path = db_path
    
    def get_all_history_stats(self) -> Dict[str, Any]:
        """전체 히스토리 데이터 통계"""
        with get_connection_context(self.db_path) as conn:
            # 전체 히스토리 레코드 수
            cursor = conn.execute(f"SELECT COUNT(*) FROM {HistoryTable.TABLE_NAME}")
            total_records = cursor.fetchone()[0]
            
            # 일봉 데이터 통계
            cursor = conn.execute(f"""
                SELECT COUNT(*) FROM {HistoryTable.TABLE_NAME} 
                WHERE timeframe = 'D'
            """)
            daily_records = cursor.fetchone()[0]
            
            # 종목별 일봉 데이터 현황
            cursor = conn.execute(f"""
                SELECT 
                    code,
                    COUNT(*) as record_count,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date
                FROM {HistoryTable.TABLE_NAME}
                WHERE timeframe = 'D'
                GROUP BY code
                ORDER BY record_count DESC
            """)
            
            stock_stats = []
            for row in cursor.fetchall():
                stock_stats.append({
                    'code': row[0],
                    'record_count': row[1],
                    'earliest_date': row[2],
                    'latest_date': row[3]
                })
            
            # 최근 데이터 현황 (최근 30일)
            recent_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            cursor = conn.execute(f"""
                SELECT COUNT(DISTINCT code) FROM {HistoryTable.TABLE_NAME}
                WHERE timeframe = 'D' AND date >= ?
            """, (recent_date,))
            recent_stocks_count = cursor.fetchone()[0]
            
            return {
                'total_records': total_records,
                'daily_records': daily_records,
                'stock_count': len(stock_stats),
                'stock_stats': stock_stats,
                'recent_stocks_count': recent_stocks_count
            }
    
    def get_stock_history_detail(self, code: str) -> Dict[str, Any]:
        """특정 종목의 히스토리 데이터 상세 정보"""
        with get_connection_context(self.db_path) as conn:
            # 종목 기본 정보
            stock_info = StockTable.get_stock(conn, code)
            
            if not stock_info:
                return {'error': f'종목 {code}를 찾을 수 없습니다.'}
            
            # 히스토리 데이터 조회
            cursor = conn.execute(f"""
                SELECT 
                    date, open_price, high_price, low_price, close_price, 
                    volume, amount, updated_at
                FROM {HistoryTable.TABLE_NAME}
                WHERE code = ? AND timeframe = 'D'
                ORDER BY date DESC
            """, (code,))
            
            history_data = []
            for row in cursor.fetchall():
                history_data.append({
                    'date': row[0],
                    'open': row[1],
                    'high': row[2],
                    'low': row[3],
                    'close': row[4],
                    'volume': row[5],
                    'amount': row[6],
                    'updated_at': row[7]
                })
            
            # 데이터 품질 검사
            quality_issues = []
            for data in history_data:
                # 가격 데이터 검증
                if data['high'] < data['low']:
                    quality_issues.append(f"{data['date']}: 고가({data['high']}) < 저가({data['low']})")
                
                if data['open'] <= 0 or data['close'] <= 0:
                    quality_issues.append(f"{data['date']}: 시가 또는 종가가 0")
                
                if data['volume'] < 0:
                    quality_issues.append(f"{data['date']}: 거래량이 음수")
            
            return {
                'stock_info': {
                    'code': stock_info.code,
                    'name': stock_info.name,
                    'market_kind': stock_info.market_kind,
                    'kospi200_kind': stock_info.kospi200_kind
                },
                'history_count': len(history_data),
                'history_data': history_data,
                'earliest_date': history_data[-1]['date'] if history_data else None,
                'latest_date': history_data[0]['date'] if history_data else None,
                'quality_issues': quality_issues
            }
    
    def export_stock_to_csv(self, code: str, output_file: str = None) -> str:
        """특정 종목의 히스토리 데이터를 CSV로 내보내기"""
        if not output_file:
            output_file = f"history_{code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        stock_detail = self.get_stock_history_detail(code)
        
        if 'error' in stock_detail:
            raise ValueError(stock_detail['error'])
        
        if not stock_detail['history_data']:
            raise ValueError(f"종목 {code}의 히스토리 데이터가 없습니다.")
        
        # CSV 파일 생성
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            
            # 헤더 정보
            writer.writerow(['# KOSPI200 History Data Export'])
            writer.writerow([f'# 종목코드: {stock_detail["stock_info"]["code"]}'])
            writer.writerow([f'# 종목명: {stock_detail["stock_info"]["name"]}'])
            writer.writerow([f'# 데이터 개수: {stock_detail["history_count"]}개'])
            writer.writerow([f'# 기간: {stock_detail["earliest_date"]} ~ {stock_detail["latest_date"]}'])
            writer.writerow([f'# 내보내기 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
            writer.writerow([])  # 빈 줄
            
            # 컬럼 헤더
            writer.writerow([
                'Date', 'Open', 'High', 'Low', 'Close', 
                'Volume', 'Amount', 'Updated_At'
            ])
            
            # 데이터 (최신순)
            for data in stock_detail['history_data']:
                writer.writerow([
                    data['date'],
                    data['open'],
                    data['high'],
                    data['low'],
                    data['close'],
                    data['volume'],
                    data['amount'],
                    data['updated_at']
                ])
        
        return output_file
    
    def find_kospi200_stocks_in_db(self) -> List[Dict[str, Any]]:
        """데이터베이스에서 히스토리 데이터가 있는 KOSPI200 종목들 찾기"""
        with get_connection_context(self.db_path) as conn:
            cursor = conn.execute(f"""
                SELECT DISTINCT h.code, s.name, s.kospi200_kind, COUNT(h.date) as record_count
                FROM {HistoryTable.TABLE_NAME} h
                JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                WHERE h.timeframe = 'D' 
                  AND s.market_kind = 1
                  AND s.kospi200_kind != 0
                GROUP BY h.code, s.name, s.kospi200_kind
                ORDER BY record_count DESC
            """)
            
            kospi200_stocks = []
            for row in cursor.fetchall():
                kospi200_stocks.append({
                    'code': row[0],
                    'name': row[1],
                    'kospi200_kind': row[2],
                    'record_count': row[3]
                })
            
            return kospi200_stocks
    
    def validate_recent_data(self, days: int = 7) -> Dict[str, Any]:
        """최근 N일간의 데이터 검증"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        with get_connection_context(self.db_path) as conn:
            # 최근 데이터가 있는 종목들
            cursor = conn.execute(f"""
                SELECT 
                    code,
                    COUNT(*) as recent_count,
                    MAX(date) as latest_date
                FROM {HistoryTable.TABLE_NAME}
                WHERE timeframe = 'D' AND date >= ?
                GROUP BY code
                ORDER BY recent_count DESC
            """, (cutoff_date,))
            
            recent_data = []
            for row in cursor.fetchall():
                recent_data.append({
                    'code': row[0],
                    'recent_count': row[1],
                    'latest_date': row[2]
                })
            
            # 데이터 품질 이슈 검사
            cursor = conn.execute(f"""
                SELECT code, date, 'High < Low' as issue
                FROM {HistoryTable.TABLE_NAME}
                WHERE timeframe = 'D' AND date >= ? AND high_price < low_price
                UNION ALL
                SELECT code, date, 'Zero Price' as issue
                FROM {HistoryTable.TABLE_NAME}
                WHERE timeframe = 'D' AND date >= ? 
                  AND (open_price <= 0 OR close_price <= 0)
                UNION ALL
                SELECT code, date, 'Negative Volume' as issue
                FROM {HistoryTable.TABLE_NAME}
                WHERE timeframe = 'D' AND date >= ? AND volume < 0
                ORDER BY code, date
            """, (cutoff_date, cutoff_date, cutoff_date))
            
            quality_issues = []
            for row in cursor.fetchall():
                quality_issues.append({
                    'code': row[0],
                    'date': row[1],
                    'issue': row[2]
                })
            
            return {
                'cutoff_date': cutoff_date,
                'stocks_with_recent_data': len(recent_data),
                'recent_data': recent_data,
                'quality_issues': quality_issues
            }


def print_db_overview():
    """데이터베이스 전체 현황 출력"""
    print("📊 KOSPI200 히스토리 데이터 전체 현황")
    print("=" * 60)
    
    verifier = KOSPI200HistoryVerifier()
    stats = verifier.get_all_history_stats()
    
    print(f"📈 전체 통계:")
    print(f"   총 히스토리 레코드: {stats['total_records']:,}개")
    print(f"   일봉 레코드: {stats['daily_records']:,}개")
    print(f"   히스토리 데이터 보유 종목: {stats['stock_count']:,}개")
    print(f"   최근 30일 데이터 보유 종목: {stats['recent_stocks_count']:,}개")
    
    print(f"\n📋 종목별 데이터 현황 (상위 20개):")
    print(f"{'종목코드':<8} {'레코드수':<8} {'시작일':<12} {'종료일':<12}")
    print("-" * 50)
    
    for stock in stats['stock_stats'][:20]:
        print(f"{stock['code']:<8} {stock['record_count']:>7,}개 {stock['earliest_date']:<12} {stock['latest_date']:<12}")
    
    if len(stats['stock_stats']) > 20:
        print(f"... 외 {len(stats['stock_stats']) - 20}개 종목")


def print_kospi200_stocks():
    """KOSPI200 종목 현황 출력"""
    print("🎯 KOSPI200 종목 히스토리 데이터 현황")
    print("=" * 60)
    
    verifier = KOSPI200HistoryVerifier()
    kospi200_stocks = verifier.find_kospi200_stocks_in_db()
    
    if not kospi200_stocks:
        print("❌ KOSPI200 종목의 히스토리 데이터를 찾을 수 없습니다.")
        return
    
    print(f"📊 KOSPI200 히스토리 데이터 보유 종목: {len(kospi200_stocks)}개")
    print()
    print(f"{'종목코드':<8} {'종목명':<20} {'구분':<4} {'레코드수':<8}")
    print("-" * 50)
    
    for stock in kospi200_stocks:
        kospi200_type = f"K{stock['kospi200_kind']}" if stock['kospi200_kind'] else "일반"
        print(f"{stock['code']:<8} {stock['name']:<20} {kospi200_type:<4} {stock['record_count']:>7,}개")
    
    # 통계 요약
    total_records = sum(stock['record_count'] for stock in kospi200_stocks)
    avg_records = total_records / len(kospi200_stocks) if kospi200_stocks else 0
    
    print(f"\n📈 KOSPI200 통계:")
    print(f"   전체 레코드: {total_records:,}개")
    print(f"   종목당 평균: {avg_records:.0f}개")


def test_stock_detail(code: str):
    """특정 종목 상세 검증"""
    print(f"🔍 {code} 종목 히스토리 데이터 상세 검증")
    print("=" * 60)
    
    verifier = KOSPI200HistoryVerifier()
    detail = verifier.get_stock_history_detail(code)
    
    if 'error' in detail:
        print(f"❌ {detail['error']}")
        return
    
    stock_info = detail['stock_info']
    print(f"📊 종목 정보:")
    print(f"   종목코드: {stock_info['code']}")
    print(f"   종목명: {stock_info['name']}")
    print(f"   시장구분: {stock_info['market_kind']} ({'KOSPI' if stock_info['market_kind'] == 1 else 'KOSDAQ'})")
    print(f"   KOSPI200: {'예' if stock_info['kospi200_kind'] != 0 else '아니오'}")
    
    print(f"\n📈 히스토리 데이터:")
    print(f"   총 레코드 수: {detail['history_count']:,}개")
    print(f"   데이터 기간: {detail['earliest_date']} ~ {detail['latest_date']}")
    
    if detail['quality_issues']:
        print(f"\n⚠️  데이터 품질 이슈 ({len(detail['quality_issues'])}건):")
        for issue in detail['quality_issues'][:10]:  # 최대 10개만 표시
            print(f"     - {issue}")
        if len(detail['quality_issues']) > 10:
            print(f"     ... 외 {len(detail['quality_issues']) - 10}건")
    else:
        print(f"\n✅ 데이터 품질: 양호")
    
    # 최근 10일 데이터 샘플 표시
    print(f"\n📋 최근 데이터 샘플 (최대 10개):")
    print(f"{'날짜':<12} {'시가':<8} {'고가':<8} {'저가':<8} {'종가':<8} {'거래량':<10}")
    print("-" * 70)
    
    for data in detail['history_data'][:10]:
        print(f"{data['date']:<12} {data['open']:>7,} {data['high']:>7,} {data['low']:>7,} {data['close']:>7,} {data['volume']:>9,}")


def export_stock_csv(code: str, output_file: str = None):
    """특정 종목을 CSV로 내보내기"""
    print(f"📤 {code} 종목 CSV 내보내기")
    print("=" * 60)
    
    verifier = KOSPI200HistoryVerifier()
    
    try:
        csv_file = verifier.export_stock_to_csv(code, output_file)
        
        # 파일 정보 확인
        file_path = Path(csv_file)
        file_size = file_path.stat().st_size
        
        print(f"✅ CSV 파일 생성 완료:")
        print(f"   파일명: {csv_file}")
        print(f"   파일 크기: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print(f"   절대 경로: {file_path.absolute()}")
        
        # 파일 내용 미리보기
        print(f"\n📋 파일 내용 미리보기 (처음 10줄):")
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            for i, line in enumerate(f):
                if i >= 10:
                    break
                print(f"   {line.rstrip()}")
        
    except Exception as e:
        print(f"❌ CSV 내보내기 실패: {e}")


def validate_recent_data(days: int = 7):
    """최근 데이터 검증"""
    print(f"🔍 최근 {days}일 데이터 검증")
    print("=" * 60)
    
    verifier = KOSPI200HistoryVerifier()
    validation = verifier.validate_recent_data(days)
    
    print(f"📅 검증 기준일: {validation['cutoff_date']} 이후")
    print(f"📊 최근 데이터 보유 종목: {validation['stocks_with_recent_data']:,}개")
    
    if validation['recent_data']:
        print(f"\n📈 최근 데이터 현황 (상위 20개):")
        print(f"{'종목코드':<8} {'최근레코드':<10} {'최신날짜':<12}")
        print("-" * 35)
        
        for data in validation['recent_data'][:20]:
            print(f"{data['code']:<8} {data['recent_count']:>9}개 {data['latest_date']:<12}")
    
    if validation['quality_issues']:
        print(f"\n⚠️  데이터 품질 이슈 ({len(validation['quality_issues'])}건):")
        for issue in validation['quality_issues'][:20]:  # 최대 20개만 표시
            print(f"     - {issue['code']} ({issue['date']}): {issue['issue']}")
        if len(validation['quality_issues']) > 20:
            print(f"     ... 외 {len(validation['quality_issues']) - 20}건")
    else:
        print(f"\n✅ 데이터 품질: 이상 없음")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="KOSPI200 히스토리 데이터 검증 도구")
    
    subparsers = parser.add_subparsers(dest="command", help="검증 명령어")
    
    # 전체 현황
    subparsers.add_parser("overview", help="데이터베이스 전체 현황 출력")
    
    # KOSPI200 현황
    subparsers.add_parser("kospi200", help="KOSPI200 종목 현황 출력")
    
    # 특정 종목 상세
    detail_parser = subparsers.add_parser("detail", help="특정 종목 상세 검증")
    detail_parser.add_argument("code", help="종목코드")
    
    # CSV 내보내기
    csv_parser = subparsers.add_parser("export", help="특정 종목 CSV 내보내기")
    csv_parser.add_argument("code", help="종목코드")
    csv_parser.add_argument("--output", "-o", help="출력 파일명")
    
    # 최근 데이터 검증
    recent_parser = subparsers.add_parser("recent", help="최근 데이터 검증")
    recent_parser.add_argument("--days", type=int, default=7, help="검증할 최근 일수 (기본: 7)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print("🛠️  KOSPI200 히스토리 데이터 검증 도구")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        if args.command == "overview":
            print_db_overview()
        elif args.command == "kospi200":
            print_kospi200_stocks()
        elif args.command == "detail":
            test_stock_detail(args.code)
        elif args.command == "export":
            export_stock_csv(args.code, args.output)
        elif args.command == "recent":
            validate_recent_data(args.days)
        else:
            print(f"❌ 알 수 없는 명령어: {args.command}")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    main()

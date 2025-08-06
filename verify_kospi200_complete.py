"""
KOSPI200 Complete Verification - 코스피200 전체 종목 일봉 데이터 검증

CpCodeMgr API를 사용하여 실제 코스피200 전체 종목을 검색하고,
각 종목별로 저장된 일봉 데이터의 개수와 현황을 상세히 검증합니다.
"""

import sys
import time
from pathlib import Path
from datetime import datetime
import csv

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import win32com.client
    from src.database.connection import get_connection_context
    from src.database.models.history import HistoryTable
    from src.database.models.stock import StockTable
except ImportError as e:
    print(f"Import error: {e}")
    print("Cybos Plus 환경에서 실행해주세요.")
    sys.exit(1)


class KOSPI200CompleteVerifier:
    """코스피200 전체 종목 검증 클래스"""
    
    def __init__(self):
        self.db_path = "data/cybos.db"
        self.kospi200_stocks = []
        self.verification_results = []
    
    def check_cybos_connection(self) -> bool:
        """Cybos Plus 연결 확인"""
        try:
            cybos = win32com.client.Dispatch("CpUtil.CpCybos")
            if cybos.IsConnect:
                print("✅ Cybos Plus 연결 상태: 정상")
                return True
            else:
                print("❌ Cybos Plus 연결되지 않음")
                return False
        except Exception as e:
            print(f"❌ Cybos Plus 연결 확인 실패: {e}")
            return False
    
    def get_all_kospi200_stocks(self) -> list:
        """실제 코스피200 전체 종목 조회"""
        print("🔍 실제 코스피200 전체 종목 조회 중...")
        print("   (CpCodeMgr.GetStockKospi200Kind() 사용)")
        
        kospi200_stocks = []
        
        try:
            # CpCodeMgr COM 객체 생성
            code_mgr = win32com.client.Dispatch("CpUtil.CpCodeMgr")
            
            # KOSPI 전체 종목 리스트 조회
            kospi_codes = code_mgr.GetStockListByMarket(1)  # 1 = KOSPI
            
            print(f"📊 KOSPI 전체 종목 수: {len(kospi_codes)}개")
            print("🔄 각 종목의 KOSPI200 포함 여부 확인 중...")
            
            kospi200_count = 0
            
            # 각 종목의 KOSPI200 여부 확인
            for i, code in enumerate(kospi_codes):
                try:
                    # 진행 상황 출력 (50개마다)
                    if (i + 1) % 50 == 0:
                        progress = (i + 1) / len(kospi_codes) * 100
                        print(f"   📈 진행률: {i + 1}/{len(kospi_codes)} ({progress:.1f}%) - KOSPI200: {kospi200_count}개 발견")
                    
                    # KOSPI200 종목 여부 확인
                    kospi200_kind = code_mgr.GetStockKospi200Kind(code)
                    
                    # 0이 아니면 KOSPI200 종목
                    if kospi200_kind != 0:
                        name = code_mgr.CodeToName(code)
                        stock_info = {
                            'code': code,
                            'name': name,
                            'kospi200_kind': kospi200_kind
                        }
                        kospi200_stocks.append(stock_info)
                        kospi200_count += 1
                        
                        # KOSPI200 종목 발견 시 즉시 출력
                        print(f"   ✅ KOSPI200 [{kospi200_count:3d}] {code} ({name}) - Kind: {kospi200_kind}")
                    
                    # API 호출 제한을 위한 짧은 대기 (0.01초)
                    time.sleep(0.01)
                    
                except Exception as e:
                    print(f"   ⚠️  {code} 조회 실패: {e}")
                    continue
            
            print(f"\n🎯 최종 결과: KOSPI200 종목 {len(kospi200_stocks)}개 발견!")
            return kospi200_stocks
            
        except Exception as e:
            print(f"❌ KOSPI200 종목 조회 실패: {e}")
            return []
    
    def verify_history_data(self, stocks: list) -> list:
        """각 종목별 일봉 데이터 검증"""
        print(f"\n📊 {len(stocks)}개 KOSPI200 종목의 일봉 데이터 검증 중...")
        print("=" * 80)
        
        results = []
        
        try:
            with get_connection_context(self.db_path) as conn:
                for i, stock in enumerate(stocks, 1):
                    code = stock['code']
                    name = stock['name']
                    kospi200_kind = stock['kospi200_kind']
                    
                    # 일봉 데이터 조회
                    cursor = conn.execute(f"""
                        SELECT 
                            COUNT(*) as record_count,
                            MIN(date) as earliest_date,
                            MAX(date) as latest_date,
                            MIN(updated_at) as first_update,
                            MAX(updated_at) as last_update
                        FROM {HistoryTable.TABLE_NAME}
                        WHERE code = ? AND timeframe = 'D'
                    """, (code,))
                    
                    row = cursor.fetchone()
                    record_count = row[0] if row else 0
                    earliest_date = row[1] if row and row[1] else None
                    latest_date = row[2] if row and row[2] else None
                    first_update = row[3] if row and row[3] else None
                    last_update = row[4] if row and row[4] else None
                    
                    # 결과 저장
                    result = {
                        'rank': i,
                        'code': code,
                        'name': name,
                        'kospi200_kind': kospi200_kind,
                        'record_count': record_count,
                        'earliest_date': earliest_date,
                        'latest_date': latest_date,
                        'first_update': first_update,
                        'last_update': last_update,
                        'has_data': record_count > 0
                    }
                    
                    results.append(result)
                    
                    # 상태에 따른 아이콘 표시
                    if record_count > 0:
                        status_icon = "✅"
                        data_period = f"{earliest_date} ~ {latest_date}" if earliest_date and latest_date else "날짜 정보 없음"
                    else:
                        status_icon = "❌"
                        data_period = "데이터 없음"
                    
                    # 진행 상황 출력
                    print(f"{status_icon} [{i:3d}/{len(stocks)}] {code} ({name[:15]:<15}) "
                          f"| {record_count:>5,}개 | {data_period}")
                    
                    # 10개마다 진행률 표시
                    if i % 10 == 0:
                        progress = (i / len(stocks)) * 100
                        with_data = sum(1 for r in results if r['has_data'])
                        print(f"    📊 진행률: {progress:.1f}% | 데이터 보유: {with_data}개/{i}개 ({with_data/i*100:.1f}%)")
                        print()
        
        except Exception as e:
            print(f"❌ 데이터 검증 실패: {e}")
        
        return results
    
    def print_summary_statistics(self, results: list) -> None:
        """요약 통계 출력"""
        if not results:
            return
        
        print("\n" + "=" * 80)
        print("📋 KOSPI200 일봉 데이터 검증 요약")
        print("=" * 80)
        
        # 기본 통계
        total_stocks = len(results)
        with_data = [r for r in results if r['has_data']]
        without_data = [r for r in results if not r['has_data']]
        
        total_records = sum(r['record_count'] for r in results)
        avg_records = total_records / len(with_data) if with_data else 0
        
        print(f"📊 전체 현황:")
        print(f"   🎯 전체 KOSPI200 종목: {total_stocks:,}개")
        print(f"   ✅ 데이터 보유 종목: {len(with_data):,}개 ({len(with_data)/total_stocks*100:.1f}%)")
        print(f"   ❌ 데이터 없는 종목: {len(without_data):,}개 ({len(without_data)/total_stocks*100:.1f}%)")
        print(f"   📈 총 일봉 레코드: {total_records:,}개")
        print(f"   📊 평균 레코드/종목: {avg_records:.0f}개")
        
        # 데이터량별 분포
        if with_data:
            data_ranges = [
                ("5,000개 이상", lambda x: x >= 5000),
                ("1,000~4,999개", lambda x: 1000 <= x < 5000),
                ("500~999개", lambda x: 500 <= x < 1000),
                ("100~499개", lambda x: 100 <= x < 500),
                ("1~99개", lambda x: 1 <= x < 100)
            ]
            
            print(f"\n📊 데이터량별 분포:")
            for range_name, range_func in data_ranges:
                count = len([r for r in with_data if range_func(r['record_count'])])
                if count > 0:
                    print(f"   {range_name}: {count}개 종목")
        
        # 상위 10개 종목 (데이터량 기준)
        top_10 = sorted(with_data, key=lambda x: x['record_count'], reverse=True)[:10]
        if top_10:
            print(f"\n🏆 데이터 보유량 상위 10개 종목:")
            print(f"{'순위':<4} {'종목코드':<8} {'종목명':<15} {'레코드수':<8} {'데이터기간':<25}")
            print("-" * 70)
            for i, result in enumerate(top_10, 1):
                period = f"{result['earliest_date']} ~ {result['latest_date']}" \
                    if result['earliest_date'] and result['latest_date'] else "기간 정보 없음"
                print(f"{i:<4} {result['code']:<8} {result['name'][:14]:<15} "
                      f"{result['record_count']:>7,}개 {period:<25}")
        
        # 데이터 없는 종목들
        if without_data:
            print(f"\n❌ 데이터가 없는 {len(without_data)}개 종목:")
            print(f"{'종목코드':<8} {'종목명':<20} {'KOSPI200종류':<12}")
            print("-" * 45)
            for result in without_data[:20]:  # 최대 20개까지만 표시
                print(f"{result['code']:<8} {result['name'][:19]:<20} {result['kospi200_kind']:<12}")
            
            if len(without_data) > 20:
                print(f"   ... 외 {len(without_data) - 20}개 종목")
    
    def export_to_csv(self, results: list) -> str:
        """결과를 CSV 파일로 내보내기"""
        if not results:
            return ""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"kospi200_complete_verification_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = [
                    'rank', 'code', 'name', 'kospi200_kind', 'record_count',
                    'has_data', 'earliest_date', 'latest_date', 'first_update', 'last_update'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    writer.writerow({
                        'rank': result['rank'],
                        'code': result['code'],
                        'name': result['name'],
                        'kospi200_kind': result['kospi200_kind'],
                        'record_count': result['record_count'],
                        'has_data': '예' if result['has_data'] else '아니오',
                        'earliest_date': result['earliest_date'] or '',
                        'latest_date': result['latest_date'] or '',
                        'first_update': result['first_update'] or '',
                        'last_update': result['last_update'] or ''
                    })
            
            print(f"📄 검증 결과가 {filename} 파일로 저장되었습니다.")
            return filename
            
        except Exception as e:
            print(f"❌ CSV 파일 저장 실패: {e}")
            return ""
    
    def run_verification(self) -> dict:
        """전체 검증 프로세스 실행"""
        print("🔍 KOSPI200 전체 종목 일봉 데이터 완전 검증")
        print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        start_time = datetime.now()
        
        try:
            # 1. Cybos Plus 연결 확인
            if not self.check_cybos_connection():
                return {'error': 'Cybos Plus 연결 실패'}
            
            # 2. 실제 KOSPI200 종목 조회
            kospi200_stocks = self.get_all_kospi200_stocks()
            
            if not kospi200_stocks:
                print("❌ KOSPI200 종목을 찾을 수 없습니다.")
                return {'error': '종목 조회 실패'}
            
            self.kospi200_stocks = kospi200_stocks
            
            # 3. 각 종목별 일봉 데이터 검증
            verification_results = self.verify_history_data(kospi200_stocks)
            self.verification_results = verification_results
            
            # 4. 요약 통계 출력
            self.print_summary_statistics(verification_results)
            
            # 5. CSV 파일로 내보내기
            csv_filename = self.export_to_csv(verification_results)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print(f"\n🏁 검증 완료!")
            print(f"   소요 시간: {duration}")
            print(f"   처리 속도: {len(kospi200_stocks) / duration.total_seconds():.2f} 종목/초")
            
            return {
                'success': True,
                'total_stocks': len(kospi200_stocks),
                'verification_results': verification_results,
                'csv_filename': csv_filename,
                'duration': str(duration)
            }
            
        except KeyboardInterrupt:
            print("\n⚠️  사용자에 의해 중단되었습니다.")
            return {'error': '사용자 중단'}
            
        except Exception as e:
            print(f"\n❌ 검증 중 오류 발생: {e}")
            return {'error': str(e)}


def main():
    """메인 함수"""
    print("🎯 KOSPI200 전체 종목 일봉 데이터 완전 검증 도구")
    print("   실제 CpCodeMgr API로 KOSPI200 종목을 모두 찾아서 검증합니다.")
    print()
    
    # 확인 메시지
    response = input("KOSPI200 전체 종목 검증을 시작하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        print("사용자에 의해 취소되었습니다.")
        return
    
    # 검증 실행
    verifier = KOSPI200CompleteVerifier()
    result = verifier.run_verification()
    
    if result.get('success'):
        print(f"\n✅ 검증이 성공적으로 완료되었습니다!")
        if result.get('csv_filename'):
            print(f"📊 상세 결과는 {result['csv_filename']} 파일을 확인하세요.")
    else:
        print(f"\n❌ 검증 실패: {result.get('error', '알 수 없는 오류')}")


if __name__ == "__main__":
    main()

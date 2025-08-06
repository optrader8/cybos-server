"""
Check History Data Type - 히스토리 데이터 수정주가 여부 확인

기존 데이터베이스에 저장된 일봉 데이터가 수정주가인지 무수정주가인지 확인하고,
필요시 수정주가 데이터로 재수집하는 스크립트입니다.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import win32com.client
    from src.database.connection import get_connection_context
    from src.database.models.history import HistoryTable
    from src.database.models.stock import StockTable
    from src.cybos.history.fetcher import get_history_fetcher
except ImportError as e:
    print(f"Import error: {e}")
    print("Cybos Plus 환경에서 실행해주세요.")
    sys.exit(1)


class HistoryDataChecker:
    """히스토리 데이터 수정주가 여부 체크 클래스"""
    
    def __init__(self, db_path: str = "data/cybos.db"):
        self.db_path = db_path
    
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
    
    def analyze_sample_data(self, sample_size: int = 5):
        """샘플 종목으로 수정주가 여부 분석"""
        print(f"🔍 샘플 {sample_size}개 종목으로 수정주가 여부 분석 중...")
        print("=" * 60)
        
        try:
            with get_connection_context(self.db_path) as conn:
                # 데이터가 많은 종목들 샘플링
                cursor = conn.execute(f"""
                    SELECT h.code, s.name, COUNT(*) as record_count
                    FROM {HistoryTable.TABLE_NAME} h
                    JOIN {StockTable.TABLE_NAME} s ON h.code = s.code
                    WHERE h.timeframe = 'D' AND s.market_kind = 1
                    GROUP BY h.code, s.name
                    HAVING COUNT(*) > 100
                    ORDER BY COUNT(*) DESC
                    LIMIT ?
                """, (sample_size,))
                
                samples = cursor.fetchall()
                
                if not samples:
                    print("❌ 분석할 샘플 데이터가 없습니다.")
                    return
                
                print(f"📊 분석 대상 종목:")
                for i, (code, name, count) in enumerate(samples, 1):
                    print(f"   {i}. {code} ({name}): {count:,}개 레코드")
                
                print(f"\n🔄 각 종목별 수정주가 여부 확인...")
                
                analysis_results = []
                
                for code, name, record_count in samples:
                    result = self._analyze_single_stock(code, name)
                    analysis_results.append(result)
                
                # 전체 분석 결과
                self._print_analysis_summary(analysis_results)
                
                return analysis_results
        
        except Exception as e:
            print(f"❌ 샘플 데이터 분석 실패: {e}")
            return None
    
    def _analyze_single_stock(self, code: str, name: str) -> dict:
        """단일 종목 수정주가 여부 분석"""
        print(f"\n🔄 [{code}] {name} 분석 중...")
        
        result = {
            "code": code,
            "name": name,
            "db_data_available": False,
            "api_data_available": False,
            "is_adjusted": None,  # True: 수정주가, False: 무수정주가, None: 판단불가
            "confidence": 0.0,
            "analysis_details": []
        }
        
        try:
            # 1. DB에서 기존 데이터 조회 (최근 30일)
            db_data = self._get_db_recent_data(code, 30)
            result["db_data_available"] = len(db_data) > 0
            
            if not db_data:
                print(f"   ❌ DB에 최근 데이터 없음")
                return result
            
            print(f"   📊 DB 데이터: {len(db_data)}개 (최근 30일)")
            
            # 2. API에서 현재 데이터 조회
            api_data = self._get_api_recent_data(code, 30)
            result["api_data_available"] = len(api_data) > 0
            
            if not api_data:
                print(f"   ❌ API 데이터 조회 실패")
                return result
            
            print(f"   📊 API 데이터: {len(api_data)}개 (최근 30일, 수정주가)")
            
            # 3. 데이터 비교 분석
            comparison_result = self._compare_prices(db_data, api_data)
            result.update(comparison_result)
            
            return result
        
        except Exception as e:
            print(f"   ❌ 분석 실패: {e}")
            result["analysis_details"].append(f"Error: {e}")
            return result
    
    def _get_db_recent_data(self, code: str, days: int) -> list:
        """DB에서 최근 데이터 조회"""
        try:
            with get_connection_context(self.db_path) as conn:
                cursor = conn.execute(f"""
                    SELECT date, open_price, high_price, low_price, close_price, volume
                    FROM {HistoryTable.TABLE_NAME}
                    WHERE code = ? AND timeframe = 'D'
                    AND date >= date('now', '-{days} days')
                    ORDER BY date DESC
                """, (code,))
                
                return cursor.fetchall()
        
        except Exception as e:
            print(f"   ⚠️  DB 데이터 조회 실패: {e}")
            return []
    
    def _get_api_recent_data(self, code: str, days: int) -> list:
        """API에서 최근 데이터 조회 (수정주가)"""
        try:
            fetcher = get_history_fetcher(min_delay=1.0, max_delay=2.0)
            history_list = fetcher.fetch_daily_history(code, days)
            
            # HistoryInfo 객체를 튜플로 변환
            api_data = []
            for history in history_list:
                api_data.append((
                    history.date,
                    history.open_price,
                    history.high_price,
                    history.low_price,
                    history.close_price,
                    history.volume
                ))
            
            return api_data
        
        except Exception as e:
            print(f"   ⚠️  API 데이터 조회 실패: {e}")
            return []
    
    def _compare_prices(self, db_data: list, api_data: list) -> dict:
        """가격 데이터 비교 분석"""
        result = {
            "is_adjusted": None,
            "confidence": 0.0,
            "analysis_details": []
        }
        
        try:
            # 날짜별로 데이터 매핑
            db_dict = {row[0]: row[1:] for row in db_data}  # date: (open, high, low, close, volume)
            api_dict = {row[0]: row[1:] for row in api_data}
            
            # 공통 날짜 찾기
            common_dates = set(db_dict.keys()) & set(api_dict.keys())
            
            if len(common_dates) < 5:
                result["analysis_details"].append("공통 날짜가 5일 미만으로 비교 불가")
                print(f"   ⚠️  공통 날짜 부족: {len(common_dates)}일")
                return result
            
            # 가격 차이 분석
            price_differences = []
            volume_differences = []
            
            for date in sorted(common_dates, reverse=True)[:10]:  # 최근 10일만
                db_prices = db_dict[date]  # (open, high, low, close, volume)
                api_prices = api_dict[date]
                
                # 종가 비교
                db_close = float(db_prices[3])
                api_close = float(api_prices[3])
                
                if db_close > 0 and api_close > 0:
                    price_diff_ratio = abs(db_close - api_close) / db_close * 100
                    price_differences.append(price_diff_ratio)
                    
                    print(f"   📅 {date}: DB종가={db_close:,.0f}, API종가={api_close:,.0f}, 차이={price_diff_ratio:.2f}%")
                
                # 거래량 비교
                db_volume = int(db_prices[4]) if db_prices[4] else 0
                api_volume = int(api_prices[4]) if api_prices[4] else 0
                
                if db_volume > 0 and api_volume > 0:
                    volume_diff_ratio = abs(db_volume - api_volume) / db_volume * 100
                    volume_differences.append(volume_diff_ratio)
            
            # 결과 판단
            if price_differences:
                avg_price_diff = sum(price_differences) / len(price_differences)
                max_price_diff = max(price_differences)
                
                print(f"   📊 가격 차이: 평균 {avg_price_diff:.2f}%, 최대 {max_price_diff:.2f}%")
                
                if avg_price_diff < 1.0:  # 평균 1% 미만 차이
                    result["is_adjusted"] = True  # 이미 수정주가로 보임
                    result["confidence"] = min(95.0, 100 - avg_price_diff * 10)
                    result["analysis_details"].append(f"가격 차이 미미({avg_price_diff:.2f}%) - 수정주가로 판단")
                    print(f"   ✅ 수정주가로 판단 (신뢰도: {result['confidence']:.1f}%)")
                
                elif avg_price_diff > 5.0:  # 평균 5% 이상 차이
                    result["is_adjusted"] = False  # 무수정주가로 보임
                    result["confidence"] = min(95.0, avg_price_diff * 2)
                    result["analysis_details"].append(f"가격 차이 큼({avg_price_diff:.2f}%) - 무수정주가로 판단")
                    print(f"   ❌ 무수정주가로 판단 (신뢰도: {result['confidence']:.1f}%)")
                
                else:  # 애매한 경우
                    result["is_adjusted"] = None
                    result["confidence"] = 50.0
                    result["analysis_details"].append(f"가격 차이 애매({avg_price_diff:.2f}%) - 판단 어려움")
                    print(f"   ❓ 판단 어려움 (차이: {avg_price_diff:.2f}%)")
        
        except Exception as e:
            result["analysis_details"].append(f"비교 분석 오류: {e}")
            print(f"   ❌ 비교 분석 실패: {e}")
        
        return result
    
    def _print_analysis_summary(self, results: list):
        """분석 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("📋 수정주가 분석 결과 요약")
        print("=" * 60)
        
        total = len(results)
        adjusted_count = len([r for r in results if r["is_adjusted"] is True])
        unadjusted_count = len([r for r in results if r["is_adjusted"] is False])
        unknown_count = len([r for r in results if r["is_adjusted"] is None])
        
        print(f"📊 전체 분석 종목: {total}개")
        print(f"   ✅ 수정주가로 판단: {adjusted_count}개 ({adjusted_count/total*100:.1f}%)")
        print(f"   ❌ 무수정주가로 판단: {unadjusted_count}개 ({unadjusted_count/total*100:.1f}%)")
        print(f"   ❓ 판단 어려움: {unknown_count}개 ({unknown_count/total*100:.1f}%)")
        
        if unadjusted_count > 0:
            print(f"\n⚠️  무수정주가로 판단된 종목:")
            for result in results:
                if result["is_adjusted"] is False:
                    print(f"   - {result['code']} ({result['name']}) - 신뢰도: {result['confidence']:.1f}%")
            
            print(f"\n💡 권장사항:")
            print(f"   1. 히스토리 데이터를 삭제하고 수정주가로 재수집")
            print(f"   2. 명령: python check_history_data_type.py --reset-and-recollect")
        
        elif adjusted_count == total:
            print(f"\n✅ 결론: 모든 데이터가 수정주가로 저장되어 있습니다!")
        
        else:
            print(f"\n❓ 결론: 일부 데이터의 수정주가 여부가 불명확합니다.")
    
    def reset_and_recollect_data(self, target_codes: list = None):
        """히스토리 데이터 초기화 및 수정주가로 재수집"""
        if not self.check_cybos_connection():
            return
        
        print("🔄 히스토리 데이터 수정주가 재수집 시작")
        print("=" * 60)
        
        try:
            if target_codes is None:
                # 샘플 분석 결과에서 무수정주가 종목들 추출
                analysis_results = self.analyze_sample_data(10)
                if not analysis_results:
                    return
                
                target_codes = [r["code"] for r in analysis_results if r["is_adjusted"] is False]
            
            if not target_codes:
                print("✅ 재수집할 종목이 없습니다.")
                return
            
            print(f"🎯 재수집 대상: {len(target_codes)}개 종목")
            
            response = input(f"{len(target_codes)}개 종목의 일봉 데이터를 삭제하고 재수집하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("사용자에 의해 취소되었습니다.")
                return
            
            # 각 종목별로 재수집
            fetcher = get_history_fetcher(min_delay=2.0, max_delay=4.0)
            
            for i, code in enumerate(target_codes, 1):
                print(f"\n🔄 [{i}/{len(target_codes)}] {code} 재수집 중...")
                
                try:
                    # 1. 기존 데이터 삭제
                    with get_connection_context(self.db_path) as conn:
                        cursor = conn.execute(f"""
                            DELETE FROM {HistoryTable.TABLE_NAME}
                            WHERE code = ? AND timeframe = 'D'
                        """, (code,))
                        deleted_count = cursor.rowcount
                        conn.commit()
                        
                        print(f"   🗑️  기존 데이터 {deleted_count}개 삭제")
                    
                    # 2. 수정주가 데이터 재수집
                    history_list = fetcher.fetch_daily_history(code, 5000)
                    
                    if history_list:
                        # 3. 새 데이터 저장
                        with get_connection_context(self.db_path) as conn:
                            saved_count = 0
                            for history in history_list:
                                try:
                                    from src.database.models.history import HistoryTable
                                    HistoryTable.upsert_history(conn, history)
                                    saved_count += 1
                                except Exception as e:
                                    print(f"   ⚠️  저장 실패: {history.date} - {e}")
                            
                            conn.commit()
                        
                        print(f"   ✅ 수정주가 데이터 {saved_count}개 저장 완료")
                    else:
                        print(f"   ❌ 데이터 수집 실패")
                
                except Exception as e:
                    print(f"   ❌ 재수집 실패: {e}")
            
            print(f"\n✅ 수정주가 재수집 완료!")
        
        except Exception as e:
            print(f"❌ 재수집 실패: {e}")


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="히스토리 데이터 수정주가 여부 확인")
    parser.add_argument("--sample-size", type=int, default=5, help="분석할 샘플 종목 수")
    parser.add_argument("--reset-and-recollect", action="store_true", help="무수정주가 데이터 초기화 후 재수집")
    
    args = parser.parse_args()
    
    print("🔍 히스토리 데이터 수정주가 여부 확인 도구")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    checker = HistoryDataChecker()
    
    if not checker.check_cybos_connection():
        return
    
    if args.reset_and_recollect:
        checker.reset_and_recollect_data()
    else:
        checker.analyze_sample_data(args.sample_size)


if __name__ == "__main__":
    main()

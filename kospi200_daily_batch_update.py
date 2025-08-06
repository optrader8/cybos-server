"""
KOSPI200 Daily History Smart Batch Update - KOSPI200 종목 일봉 히스토리 스마트 배치 업데이트

기존 kospi200_daily_batch.py를 기반으로 하되:
- 5000개 일괄 요청이 아닌 누락된 날짜 수 + 10개만 효율적으로 요청
- 각 종목별로 데이터 공백을 정확히 계산하여 최적화된 요청
- 불필요한 API 호출을 최소화하여 빠르고 안전한 업데이트
"""

import sys
import time
import random
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import win32com.client
    from src.database.connection import get_connection_context, initialize_database
    from src.database.models.stock import StockTable, MarketKind
    from src.database.models.history import HistoryTable, HistoryTimeframe, HistoryInfo
    from src.cybos.history.fetcher import get_history_fetcher
except ImportError as e:
    print(f"Import error: {e}")
    print("Please make sure you're running in the correct environment")
    sys.exit(1)


class KOSPI200SmartBatch:
    """KOSPI200 일봉 히스토리 스마트 배치 업데이트 클래스"""
    
    def __init__(self, min_delay_minutes: float = 0.2, max_delay_minutes: float = 1.0):
        self.min_delay_minutes = min_delay_minutes
        self.max_delay_minutes = max_delay_minutes
        self.db_path = "data/cybos.db"
        self.buffer_days = 10  # 누락된 날짜 + 10개 버퍼
        
        # 통계 정보
        self.stats = {
            "start_time": None,
            "end_time": None,
            "total_stocks": 0,
            "processed_stocks": 0,
            "successful_stocks": 0,
            "failed_stocks": 0,
            "total_history_records": 0,
            "total_api_requests": 0,
            "total_missing_days": 0,
            "total_requested_days": 0,
            "efficiency_ratio": 0.0,
            "errors": []
        }
    
    def check_cybos_connection(self) -> bool:
        """Cybos Plus 연결 확인"""
        try:
            cybos = win32com.client.Dispatch("CpUtil.CpCybos")
            if cybos.IsConnect:
                print("✅ Cybos Plus 연결 상태: 정상")
                return True
            else:
                print("❌ Cybos Plus 연결되지 않음")
                print("   1. Cybos Plus를 실행하고 로그인하세요")
                print("   2. 모든 COM 등록이 완료되었는지 확인하세요")
                return False
        except Exception as e:
            print(f"❌ Cybos Plus 연결 확인 실패: {e}")
            return False
    
    def get_kospi200_stocks(self) -> list:
        """CpCodeMgr API를 사용하여 정확한 KOSPI200 종목 목록 조회"""
        print("🔍 KOSPI200 종목 목록 조회 중...")
        
        kospi200_stocks = []
        
        try:
            # CpCodeMgr COM 객체 생성
            code_mgr = win32com.client.Dispatch("CpUtil.CpCodeMgr")
            
            # KOSPI 전체 종목 리스트 조회
            kospi_codes = code_mgr.GetStockListByMarket(1)  # 1 = KOSPI
            
            print(f"   📊 KOSPI 전체 종목 수: {len(kospi_codes)}개")
            
            # 각 종목의 KOSPI200 여부 확인
            for i, code in enumerate(kospi_codes):
                try:
                    # 진행 상황 출력 (100개마다)
                    if (i + 1) % 100 == 0:
                        print(f"   🔄 진행률: {i + 1}/{len(kospi_codes)} ({(i + 1) / len(kospi_codes) * 100:.1f}%)")
                    
                    # KOSPI200 종목 여부 확인
                    kospi200_kind = code_mgr.GetStockKospi200Kind(code)
                    
                    # 0이 아니면 KOSPI200 종목
                    if kospi200_kind != 0:
                        name = code_mgr.CodeToName(code)
                        kospi200_stocks.append({
                            'code': code,
                            'name': name,
                            'kospi200_kind': kospi200_kind
                        })
                        
                        print(f"   ✅ KOSPI200 종목 발견: {code} ({name})")
                    
                    # API 호출 제한을 위한 짧은 대기
                    time.sleep(0.01)
                    
                except Exception as e:
                    print(f"   ⚠️  {code} 조회 실패: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ KOSPI200 종목 조회 실패: {e}")
            print("   백업 방법: 하드코딩된 대표 종목 사용")
            return self._get_fallback_kospi200_stocks()
        
        print(f"🎯 KOSPI200 종목 총 {len(kospi200_stocks)}개 발견")
        return kospi200_stocks
    
    def _get_fallback_kospi200_stocks(self) -> list:
        """백업용 KOSPI200 대표 종목들"""
        fallback_codes = [
            ('005930', '삼성전자'),
            ('000660', 'SK하이닉스'),
            ('207940', '삼성바이오로직스'),
            ('005380', '현대차'),
            ('006400', '삼성SDI'),
            ('051910', 'LG화학'),
            ('003550', 'LG'),
            ('000270', '기아'),
            ('068270', '셀트리온'),
            ('012330', '현대모비스'),
            ('066570', 'LG전자'),
            ('096770', 'SK이노베이션'),
            ('028260', '삼성물산'),
            ('323410', '카카오뱅크'),
            ('035420', 'NAVER'),
            ('035720', '카카오'),
            ('017670', 'SK텔레콤'),
            ('033780', 'KT&G'),
            ('003670', 'POSCO홀딩스'),
            ('316140', '우리금융지주')
        ]
        
        return [{'code': code, 'name': name, 'kospi200_kind': 1} for code, name in fallback_codes]
    
    def calculate_missing_days(self, code: str, max_days: int = 60) -> int:
        """종목별 누락된 날짜 수 계산 (주말 제외)"""
        try:
            with get_connection_context(self.db_path) as conn:
                # 최신 데이터 날짜 조회
                cursor = conn.execute(f"""
                    SELECT MAX(date) FROM {HistoryTable.TABLE_NAME}
                    WHERE code = ? AND timeframe = 'D'
                """, (code,))
                
                result = cursor.fetchone()
                latest_date = result[0] if result and result[0] else None
                
                if not latest_date:
                    # 데이터가 없으면 최대 요청 일수 반환
                    print(f"   📊 {code}: 기존 데이터 없음 (최대 {max_days}일 요청)")
                    return max_days
                
                # 최신 날짜부터 오늘까지 누락된 영업일 수 계산
                latest_datetime = datetime.strptime(latest_date, '%Y-%m-%d')
                current_datetime = datetime.now()
                
                missing_days = 0
                current_check = latest_datetime + timedelta(days=1)
                
                while current_check.date() <= current_datetime.date() and missing_days < max_days:
                    # 주말(토요일=5, 일요일=6) 제외
                    if current_check.weekday() < 5:  # 월~금요일만
                        # 해당 날짜 데이터 존재 여부 확인
                        check_date_str = current_check.strftime('%Y-%m-%d')
                        cursor = conn.execute(f"""
                            SELECT COUNT(*) FROM {HistoryTable.TABLE_NAME}
                            WHERE code = ? AND timeframe = 'D' AND date = ?
                        """, (code, check_date_str))
                        
                        count = cursor.fetchone()[0]
                        if count == 0:
                            missing_days += 1
                    
                    current_check += timedelta(days=1)
                
                print(f"   📊 {code}: 최신 데이터({latest_date}) 이후 누락 {missing_days}일")
                return missing_days
                
        except Exception as e:
            print(f"   ⚠️  {code} 누락 일수 계산 실패: {e}")
            return max_days  # 오류 시 안전하게 최대값 반환
    
    def wait_random_delay(self) -> None:
        """12초-60초 사이 불규칙한 대기"""
        wait_minutes = random.uniform(self.min_delay_minutes, self.max_delay_minutes)
        wait_seconds = wait_minutes * 60
        
        print(f"⏳ {wait_seconds:.0f}초 대기 중...")
        
        # 10초마다 진행 상황 출력 (60초 이상인 경우만)
        if wait_seconds > 60:
            start_time = time.time()
            while time.time() - start_time < wait_seconds:
                remaining = wait_seconds - (time.time() - start_time)
                if remaining > 10:
                    print(f"   ⏰ 남은 시간: {remaining:.0f}초")
                    time.sleep(10)
                else:
                    time.sleep(remaining)
                    break
        else:
            time.sleep(wait_seconds)
        
        print(f"✅ 대기 완료")
    
    def collect_single_stock_history_smart(self, stock: dict) -> int:
        """단일 종목 스마트 히스토리 데이터 수집"""
        code = stock['code']
        name = stock['name']
        
        try:
            # 1. 누락된 날짜 수 계산
            missing_days = self.calculate_missing_days(code)
            
            if missing_days == 0:
                print(f"   ✅ {code} ({name}): 누락 데이터 없음 - 스킵")
                return 0
            
            # 2. 요청할 데이터 수 = 누락 날짜 + 버퍼
            request_count = missing_days + self.buffer_days
            
            # 최대 5000개 제한
            request_count = min(request_count, 5000)
            
            print(f"   📊 {code} ({name}): 누락 {missing_days}일 + 버퍼 {self.buffer_days}일 = {request_count}개 요청")
            
            # 통계 업데이트
            self.stats["total_missing_days"] += missing_days
            self.stats["total_requested_days"] += request_count
            self.stats["total_api_requests"] += 1
            
            # 3. 히스토리 데이터 수집
            fetcher = get_history_fetcher(min_delay=2.0, max_delay=5.0)
            history_list = fetcher.fetch_daily_history(code, request_count)
            
            if history_list:
                # 데이터베이스에 저장
                with get_connection_context(self.db_path) as conn:
                    saved_count = 0
                    for history in history_list:
                        try:
                            HistoryTable.upsert_history(conn, history)
                            saved_count += 1
                        except Exception as e:
                            print(f"   ⚠️  데이터 저장 실패: {history.date} - {e}")
                    
                    conn.commit()
                
                efficiency = (missing_days / request_count * 100) if request_count > 0 else 0
                print(f"   ✅ {code} ({name}): {saved_count:,}개 레코드 저장 완료 (효율성: {efficiency:.1f}%)")
                return saved_count
            else:
                print(f"   ❌ {code} ({name}): 데이터 없음")
                return 0
        
        except Exception as e:
            error_msg = f"{code} ({name}) 수집 실패: {e}"
            self.stats["errors"].append(error_msg)
            print(f"   ❌ {error_msg}")
            return 0
    
    def run_smart_batch(self, dry_run: bool = False) -> dict:
        """KOSPI200 일봉 히스토리 스마트 배치 실행"""
        print("🚀 KOSPI200 일봉 히스토리 스마트 배치 시작")
        print("=" * 60)
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"대기 시간: {self.min_delay_minutes*60:.0f}~{self.max_delay_minutes*60:.0f}초")
        print(f"스마트 모드: 누락 날짜 + {self.buffer_days}일 버퍼")
        
        # 통계 초기화
        self.stats["start_time"] = datetime.now()
        self.stats["errors"] = []
        
        try:
            # Cybos Plus 연결 확인
            if not self.check_cybos_connection():
                return self.stats
            
            # 데이터베이스 초기화
            print("\n🗄️  데이터베이스 초기화 중...")
            initialize_database()
            
            # KOSPI200 종목 조회
            kospi200_stocks = self.get_kospi200_stocks()
            
            if not kospi200_stocks:
                print("❌ KOSPI200 종목을 찾을 수 없습니다.")
                return self.stats
            
            self.stats["total_stocks"] = len(kospi200_stocks)
            
            # 예상 효율성 분석 (첫 5개 종목으로 샘플링)
            print(f"\n🔬 스마트 분석 (샘플 5개 종목)...")
            sample_missing = 0
            sample_count = min(5, len(kospi200_stocks))
            
            for i in range(sample_count):
                sample_missing += self.calculate_missing_days(kospi200_stocks[i]['code'])
            
            avg_missing = sample_missing / sample_count
            estimated_efficiency = (avg_missing / (avg_missing + self.buffer_days)) * 100
            
            print(f"📊 스마트 배치 예상:")
            print(f"   평균 누락 일수: {avg_missing:.1f}일")
            print(f"   평균 요청 일수: {avg_missing + self.buffer_days:.1f}일")
            print(f"   예상 효율성: {estimated_efficiency:.1f}%")
            print(f"   기존 대비 API 요청 절약: {((5000 - (avg_missing + self.buffer_days)) / 5000 * 100):.1f}%")
            
            if dry_run:
                print("\n🔍 DRY RUN 모드 - 실제 데이터 수집은 하지 않습니다.")
                print("\n📋 대상 종목 목록 (처음 10개):")
                for i, stock in enumerate(kospi200_stocks[:10], 1):
                    missing = self.calculate_missing_days(stock['code'])
                    request_count = missing + self.buffer_days
                    print(f"   {i}. {stock['code']} ({stock['name']}): 누락 {missing}일 → {request_count}개 요청")
                if len(kospi200_stocks) > 10:
                    print(f"   ... 외 {len(kospi200_stocks) - 10}개")
                return self.stats
            
            # 확인 메시지
            response = input(f"\n{len(kospi200_stocks)}개 KOSPI200 종목의 스마트 업데이트를 시작하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("사용자에 의해 취소되었습니다.")
                return self.stats
            
            # 배치 작업 시작
            print(f"\n📈 KOSPI200 스마트 히스토리 데이터 수집 시작...")
            
            for i, stock in enumerate(kospi200_stocks, 1):
                print(f"\n🔄 [{i}/{len(kospi200_stocks)}] {stock['code']} ({stock['name']}) 처리 중...")
                
                # 데이터 수집
                start_time = time.time()
                records_count = self.collect_single_stock_history_smart(stock)
                processing_time = time.time() - start_time
                
                # 통계 업데이트
                self.stats["processed_stocks"] += 1
                if records_count > 0:
                    self.stats["successful_stocks"] += 1
                    self.stats["total_history_records"] += records_count
                else:
                    self.stats["failed_stocks"] += 1
                
                # 진행 상황 출력
                success_rate = (self.stats["successful_stocks"] / self.stats["processed_stocks"]) * 100
                progress = (i / len(kospi200_stocks)) * 100
                
                # 현재까지의 효율성 계산
                if self.stats["total_requested_days"] > 0:
                    current_efficiency = (self.stats["total_missing_days"] / self.stats["total_requested_days"]) * 100
                    self.stats["efficiency_ratio"] = current_efficiency
                
                print(f"   📊 진행률: {progress:.1f}% | 성공률: {success_rate:.1f}% | "
                      f"효율성: {self.stats['efficiency_ratio']:.1f}% | 처리시간: {processing_time:.1f}초")
                
                # 마지막 종목이 아니면 대기
                if i < len(kospi200_stocks):
                    print(f"   🎯 다음 종목: {kospi200_stocks[i]['code']} ({kospi200_stocks[i]['name']})")
                    self.wait_random_delay()
            
            self.stats["end_time"] = datetime.now()
            
            # 최종 결과 출력
            self._print_final_results()
            
            return self.stats
            
        except KeyboardInterrupt:
            print("\n⚠️  사용자에 의해 중단되었습니다.")
            self.stats["end_time"] = datetime.now()
            self._print_final_results()
            return self.stats
            
        except Exception as e:
            print(f"\n❌ 시스템 오류: {e}")
            self.stats["errors"].append(f"System error: {e}")
            self.stats["end_time"] = datetime.now()
            return self.stats
    
    def _print_final_results(self) -> None:
        """최종 결과 출력"""
        if not self.stats["start_time"] or not self.stats["end_time"]:
            return
        
        duration = self.stats["end_time"] - self.stats["start_time"]
        
        print("\n" + "=" * 60)
        print("🎉 KOSPI200 스마트 히스토리 배치 완료!")
        print(f"📊 최종 결과:")
        print(f"   전체 종목: {self.stats['total_stocks']:,}개")
        print(f"   처리 종목: {self.stats['processed_stocks']:,}개")
        print(f"   성공 종목: {self.stats['successful_stocks']:,}개")
        print(f"   실패 종목: {self.stats['failed_stocks']:,}개")
        
        if self.stats['processed_stocks'] > 0:
            success_rate = (self.stats['successful_stocks'] / self.stats['processed_stocks']) * 100
            print(f"   성공률: {success_rate:.1f}%")
        
        print(f"   총 히스토리 레코드: {self.stats['total_history_records']:,}개")
        print(f"   소요 시간: {duration}")
        
        # 스마트 배치 효율성 정보
        print(f"\n🎯 스마트 배치 효율성:")
        print(f"   총 누락 일수: {self.stats['total_missing_days']:,}일")
        print(f"   총 요청 일수: {self.stats['total_requested_days']:,}일")
        print(f"   효율성 비율: {self.stats['efficiency_ratio']:.1f}%")
        print(f"   API 요청 수: {self.stats['total_api_requests']:,}번")
        
        if self.stats['total_api_requests'] > 0:
            avg_requested = self.stats['total_requested_days'] / self.stats['total_api_requests']
            traditional_requests = self.stats['total_api_requests'] * 5000
            saved_requests = traditional_requests - self.stats['total_requested_days']
            savings_ratio = (saved_requests / traditional_requests) * 100
            
            print(f"   평균 요청량/종목: {avg_requested:.1f}개 (기존: 5,000개)")
            print(f"   절약된 API 요청: {saved_requests:,}개 ({savings_ratio:.1f}%)")
        
        if self.stats["errors"]:
            print(f"\n⚠️  오류 발생: {len(self.stats['errors'])}건")
            print("   최근 오류:")
            for error in self.stats["errors"][-5:]:  # 최근 5개만 표시
                print(f"     - {error}")
        
        # 시간당 종목 처리량
        if duration.total_seconds() > 0:
            stocks_per_hour = (self.stats['processed_stocks'] * 3600) / duration.total_seconds()
            print(f"   처리 속도: {stocks_per_hour:.1f}종목/시간")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="KOSPI200 일봉 히스토리 스마트 배치 작업")
    
    parser.add_argument("--dry-run", action="store_true", help="실제 실행 없이 계획만 출력")
    parser.add_argument("--min-delay", type=float, default=0.2, help="최소 대기 시간 (분, 기본: 0.2 = 12초)")
    parser.add_argument("--max-delay", type=float, default=1.0, help="최대 대기 시간 (분, 기본: 1.0 = 60초)")
    parser.add_argument("--buffer", type=int, default=10, help="누락 일수에 추가할 버퍼 (기본: 10일)")
    
    args = parser.parse_args()
    
    # 입력 검증
    if args.min_delay < 0.1 or args.max_delay < 0.1:
        print("❌ 대기 시간은 최소 0.1분 이상이어야 합니다.")
        return
    
    if args.min_delay >= args.max_delay:
        print("❌ 최소 대기 시간은 최대 대기 시간보다 작아야 합니다.")
        return
    
    if args.buffer < 1 or args.buffer > 100:
        print("❌ 버퍼는 1-100일 사이여야 합니다.")
        return
    
    print("🎯 KOSPI200 일봉 히스토리 스마트 배치 시스템")
    print("=" * 60)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 배치 작업 실행
    batch = KOSPI200SmartBatch(
        min_delay_minutes=args.min_delay,
        max_delay_minutes=args.max_delay
    )
    
    batch.buffer_days = args.buffer
    
    result = batch.run_smart_batch(dry_run=args.dry_run)
    
    print(f"\n🏁 스마트 배치 작업 종료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()

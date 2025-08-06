"""
KOSPI200 Daily History Batch - KOSPI200 종목 일봉 히스토리 배치 작업

CpCodeMgr API를 사용하여 정확한 KOSPI200 종목을 식별하고,
불규칙한 3-10분 지연시간으로 안전하게 히스토리 데이터를 수집합니다.
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


class KOSPI200HistoryBatch:
    """KOSPI200 일봉 히스토리 배치 작업 클래스"""
    
    def __init__(self, min_delay_minutes: float = 0.2, max_delay_minutes: float = 1.0):
        self.min_delay_minutes = min_delay_minutes
        self.max_delay_minutes = max_delay_minutes
        self.db_path = "data/cybos.db"
        
        # 통계 정보
        self.stats = {
            "start_time": None,
            "end_time": None,
            "total_stocks": 0,
            "processed_stocks": 0,
            "successful_stocks": 0,
            "failed_stocks": 0,
            "total_history_records": 0,
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
    
    def collect_single_stock_history(self, stock: dict, incremental: bool = True) -> int:
        """단일 종목 히스토리 데이터 수집"""
        code = stock['code']
        name = stock['name']
        
        try:
            fetcher = get_history_fetcher(min_delay=2.0, max_delay=5.0)
            
            # 기존 데이터 확인
            if incremental:
                with get_connection_context(self.db_path) as conn:
                    latest_date = HistoryTable.get_latest_date(conn, code, HistoryTimeframe.DAILY)
                
                if latest_date:
                    print(f"   📅 기존 데이터 있음 (최신: {latest_date}) - 증분 수집")
                    count = 100  # 최근 100개만
                else:
                    print(f"   🆕 신규 데이터 수집 - 전체 수집")
                    count = 5000  # 전체 데이터
            else:
                count = 5000  # 전체 업데이트
            
            # 히스토리 데이터 수집
            print(f"   📊 {code} ({name}) 일봉 데이터 수집 중... (최대 {count}개)")
            history_list = fetcher.fetch_daily_history(code, count)
            
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
                
                print(f"   ✅ {code} ({name}): {saved_count:,}개 레코드 저장 완료")
                return saved_count
            else:
                print(f"   ❌ {code} ({name}): 데이터 없음")
                return 0
        
        except Exception as e:
            error_msg = f"{code} ({name}) 수집 실패: {e}"
            self.stats["errors"].append(error_msg)
            print(f"   ❌ {error_msg}")
            return 0
    
    def run_batch(self, incremental: bool = True, dry_run: bool = False) -> dict:
        """KOSPI200 일봉 히스토리 배치 실행"""
        print("🚀 KOSPI200 일봉 히스토리 배치 시작")
        print("=" * 60)
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"대기 시간: {self.min_delay_minutes*60:.0f}~{self.max_delay_minutes*60:.0f}초")
        print(f"업데이트 모드: {'증분' if incremental else '전체'}")
        
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
            
            # 예상 소요 시간 계산
            avg_delay_minutes = (self.min_delay_minutes + self.max_delay_minutes) / 2
            estimated_hours = (len(kospi200_stocks) * avg_delay_minutes) / 60
            estimated_completion = datetime.now() + timedelta(hours=estimated_hours)
            
            print(f"\n📊 배치 계획:")
            print(f"   대상 종목: {len(kospi200_stocks)}개")
            print(f"   평균 대기 시간: {avg_delay_minutes*60:.0f}초")
            print(f"   예상 소요 시간: {estimated_hours:.1f}시간")
            print(f"   예상 완료 시간: {estimated_completion.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if dry_run:
                print("\n🔍 DRY RUN 모드 - 실제 데이터 수집은 하지 않습니다.")
                print("\n📋 대상 종목 목록:")
                for i, stock in enumerate(kospi200_stocks[:10], 1):  # 처음 10개만 표시
                    print(f"   {i}. {stock['code']} ({stock['name']})")
                if len(kospi200_stocks) > 10:
                    print(f"   ... 외 {len(kospi200_stocks) - 10}개")
                return self.stats
            
            # 확인 메시지
            response = input(f"\n{len(kospi200_stocks)}개 KOSPI200 종목의 히스토리 데이터를 수집하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("사용자에 의해 취소되었습니다.")
                return self.stats
            
            # 배치 작업 시작
            print(f"\n📈 KOSPI200 히스토리 데이터 수집 시작...")
            
            for i, stock in enumerate(kospi200_stocks, 1):
                print(f"\n🔄 [{i}/{len(kospi200_stocks)}] {stock['code']} ({stock['name']}) 처리 중...")
                
                # 데이터 수집
                start_time = time.time()
                records_count = self.collect_single_stock_history(stock, incremental)
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
                
                print(f"   📊 진행률: {progress:.1f}% | 성공률: {success_rate:.1f}% | 처리시간: {processing_time:.1f}초")
                
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
        print("🎉 KOSPI200 일봉 히스토리 배치 완료!")
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
    parser = argparse.ArgumentParser(description="KOSPI200 일봉 히스토리 배치 작업")
    
    parser.add_argument("--dry-run", action="store_true", help="실제 실행 없이 계획만 출력")
    parser.add_argument("--full", action="store_true", help="전체 업데이트 (기존 데이터 무시)")
    parser.add_argument("--min-delay", type=float, default=0.2, help="최소 대기 시간 (분, 기본: 0.2 = 12초)")
    parser.add_argument("--max-delay", type=float, default=1.0, help="최대 대기 시간 (분, 기본: 1.0 = 60초)")
    
    args = parser.parse_args()
    
    # 입력 검증
    if args.min_delay < 0.1 or args.max_delay < 0.1:
        print("❌ 대기 시간은 최소 0.1분 이상이어야 합니다.")
        return
    
    if args.min_delay >= args.max_delay:
        print("❌ 최소 대기 시간은 최대 대기 시간보다 작아야 합니다.")
        return
    
    print("🎯 KOSPI200 일봉 히스토리 배치 시스템")
    print("=" * 60)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 배치 작업 실행
    batch = KOSPI200HistoryBatch(
        min_delay_minutes=args.min_delay,
        max_delay_minutes=args.max_delay
    )
    
    result = batch.run_batch(
        incremental=not args.full,
        dry_run=args.dry_run
    )
    
    print(f"\n🏁 배치 작업 종료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()

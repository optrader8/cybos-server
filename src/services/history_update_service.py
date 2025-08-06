"""
History Update Service - 히스토리 데이터 업데이트 서비스

전체 종목에 대한 히스토리 데이터를 배치로 안전하게 수집하고 저장하는 서비스입니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..database.connection import get_connection_context
from ..database.models.stock import StockTable, MarketKind
from ..database.models.history import HistoryTable, HistoryInfo, HistoryTimeframe
from ..cybos.history.fetcher import get_history_fetcher


class HistoryUpdateService:
    """히스토리 데이터 업데이트 서비스 클래스"""
    
    def __init__(self, 
                 db_path: str = "data/cybos.db",
                 batch_size: int = 10,
                 min_delay: float = 3.0,
                 max_delay: float = 8.0,
                 max_requests_per_hour: int = 200):
        
        self.db_path = db_path
        self.batch_size = batch_size
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_requests_per_hour = max_requests_per_hour
        
        # 통계 정보
        self.stats = {
            "start_time": None,
            "end_time": None,
            "total_stocks": 0,
            "processed_stocks": 0,
            "successful_stocks": 0,
            "failed_stocks": 0,
            "total_requests": 0,
            "total_history_records": 0,
            "errors": []
        }
    
    def get_target_stocks(self, market_kinds: List[int] = None) -> List[Dict[str, Any]]:
        """히스토리 업데이트 대상 종목 목록 조회"""
        if market_kinds is None:
            market_kinds = [MarketKind.KOSPI, MarketKind.KOSDAQ]
        
        target_stocks = []
        
        with get_connection_context(self.db_path) as conn:
            for market_kind in market_kinds:
                stocks = StockTable.get_stocks_by_market(conn, market_kind)
                for stock in stocks:
                    target_stocks.append({
                        "code": stock.code,
                        "name": stock.name,
                        "market_kind": stock.market_kind
                    })
        
        # 랜덤하게 섞어서 서버 부하 분산
        random.shuffle(target_stocks)
        return target_stocks
    
    def calculate_safe_schedule(self, total_stocks: int) -> Dict[str, Any]:
        """안전한 스케줄 계산"""
        total_batches = (total_stocks + self.batch_size - 1) // self.batch_size
        
        # 시간당 최대 요청 수를 고려한 최소 간격 계산
        min_interval = 3600 / self.max_requests_per_hour
        safe_interval = max(min_interval, self.min_delay)
        
        # 예상 소요 시간 계산 (히스토리는 더 오래 걸림)
        estimated_time = total_batches * (safe_interval + self.max_delay + 2)  # 추가 처리 시간
        
        return {
            "total_stocks": total_stocks,
            "total_batches": total_batches,
            "safe_interval": safe_interval,
            "estimated_time_hours": estimated_time / 3600,
            "estimated_completion": datetime.now() + timedelta(seconds=estimated_time)
        }
    
    def check_existing_data(self, code: str, timeframe: HistoryTimeframe) -> Optional[str]:
        """기존 히스토리 데이터 확인 (가장 최신 날짜 반환)"""
        with get_connection_context(self.db_path) as conn:
            return HistoryTable.get_latest_date(conn, code, timeframe)
    
    def update_history_batch(self, stocks: List[Dict[str, Any]], 
                           timeframe: HistoryTimeframe = HistoryTimeframe.DAILY,
                           incremental: bool = True) -> int:
        """배치 단위로 히스토리 데이터 업데이트"""
        fetcher = get_history_fetcher(self.min_delay, self.max_delay)
        total_records = 0
        
        try:
            for stock in stocks:
                code = stock["code"]
                name = stock["name"]
                
                try:
                    # 증분 업데이트인 경우 기존 데이터 확인
                    if incremental:
                        latest_date = self.check_existing_data(code, timeframe)
                        if latest_date:
                            print(f"   📅 {code} ({name}): 기존 데이터 있음 (최신: {latest_date})")
                            # 최근 100개만 수집 (증분 업데이트)
                            count = 100
                        else:
                            print(f"   🆕 {code} ({name}): 신규 수집")
                            # 전체 데이터 수집
                            count = 5000
                    else:
                        # 전체 업데이트
                        count = 5000
                    
                    # 히스토리 데이터 수집
                    if timeframe == HistoryTimeframe.DAILY:
                        history_list = fetcher.fetch_daily_history(code, count)
                    elif timeframe == HistoryTimeframe.WEEKLY:
                        history_list = fetcher.fetch_weekly_history(code, count)
                    else:  # MONTHLY
                        history_list = fetcher.fetch_monthly_history(code, count)
                    
                    # 데이터베이스에 저장
                    if history_list:
                        with get_connection_context(self.db_path) as conn:
                            for history in history_list:
                                HistoryTable.upsert_history(conn, history)
                            conn.commit()
                        
                        total_records += len(history_list)
                        print(f"   ✅ {code} ({name}): {len(history_list)}개 저장")
                    else:
                        print(f"   ⚠️  {code} ({name}): 데이터 없음")
                    
                    self.stats["total_requests"] += 1
                    
                except Exception as e:
                    error_msg = f"History update failed for {code}: {e}"
                    self.stats["errors"].append(error_msg)
                    print(f"   ❌ {error_msg}")
                    continue
            
            return total_records
            
        except Exception as e:
            error_msg = f"Batch history update failed: {e}"
            self.stats["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            return total_records
    
    def run_full_history_update(self, 
                               market_kinds: List[int] = None,
                               timeframe: HistoryTimeframe = HistoryTimeframe.DAILY,
                               incremental: bool = True,
                               dry_run: bool = False) -> Dict[str, Any]:
        """전체 히스토리 데이터 업데이트 실행"""
        print(f"🚀 히스토리 데이터 업데이트 서비스 시작 ({timeframe.value}봉)")
        print("=" * 60)
        
        # 통계 초기화
        self.stats["start_time"] = datetime.now()
        self.stats["errors"] = []
        
        try:
            # 대상 종목 조회
            target_stocks = self.get_target_stocks(market_kinds)
            self.stats["total_stocks"] = len(target_stocks)
            
            if not target_stocks:
                print("❌ 업데이트할 종목이 없습니다.")
                return self.stats
            
            # 스케줄 계산
            schedule = self.calculate_safe_schedule(len(target_stocks))
            
            print(f"📊 업데이트 계획:")
            print(f"   대상 종목 수: {schedule['total_stocks']:,}")
            print(f"   배치 수: {schedule['total_batches']:,}")
            print(f"   배치 크기: {self.batch_size}")
            print(f"   예상 소요 시간: {schedule['estimated_time_hours']:.1f}시간")
            print(f"   예상 완료 시간: {schedule['estimated_completion'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   업데이트 모드: {'증분' if incremental else '전체'}")
            
            if dry_run:
                print("🔍 DRY RUN 모드 - 실제 업데이트는 수행하지 않습니다.")
                return self.stats
            
            # 확인 메시지
            response = input("\n계속하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("사용자에 의해 취소되었습니다.")
                return self.stats
            
            # 배치 단위로 처리
            print(f"\n📈 히스토리 데이터 업데이트 시작...")
            
            for i in range(0, len(target_stocks), self.batch_size):
                batch_stocks = target_stocks[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1
                total_batches = schedule["total_batches"]
                
                print(f"\n🔄 배치 {batch_num}/{total_batches} 처리 중... ({len(batch_stocks)}개 종목)")
                
                # 배치 처리
                batch_start = time.time()
                records_count = self.update_history_batch(batch_stocks, timeframe, incremental)
                batch_time = time.time() - batch_start
                
                # 통계 업데이트
                self.stats["processed_stocks"] += len(batch_stocks)
                self.stats["successful_stocks"] += sum(1 for stock in batch_stocks if records_count > 0)
                self.stats["failed_stocks"] += len(batch_stocks) - sum(1 for stock in batch_stocks if records_count > 0)
                self.stats["total_history_records"] += records_count
                
                # 진행 상황 출력
                print(f"   ✅ 저장된 레코드: {records_count:,}개")
                print(f"   ⏱️  소요 시간: {batch_time:.1f}초")
                
                # 전체 진행률 계산
                progress = (batch_num / total_batches) * 100
                print(f"   📊 전체 진행률: {progress:.1f}%")
                
                # 배치 간 대기 (히스토리는 더 긴 대기)
                if batch_num < total_batches:
                    wait_time = random.uniform(8.0, 15.0)
                    print(f"   ⏳ 다음 배치까지 {wait_time:.1f}초 대기...")
                    time.sleep(wait_time)
            
            self.stats["end_time"] = datetime.now()
            
            # 최종 결과 출력
            self._print_final_results()
            
            return self.stats
            
        except KeyboardInterrupt:
            print("\n⚠️  사용자에 의해 중단되었습니다.")
            self.stats["end_time"] = datetime.now()
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
        success_rate = (self.stats["successful_stocks"] / max(self.stats["processed_stocks"], 1)) * 100
        
        print("\n" + "=" * 60)
        print("🎉 히스토리 데이터 업데이트 완료!")
        print(f"📊 최종 결과:")
        print(f"   전체 종목: {self.stats['total_stocks']:,}")
        print(f"   처리 종목: {self.stats['processed_stocks']:,}")
        print(f"   성공 종목: {self.stats['successful_stocks']:,}")
        print(f"   실패 종목: {self.stats['failed_stocks']:,}")
        print(f"   성공률: {success_rate:.1f}%")
        print(f"   총 히스토리 레코드: {self.stats['total_history_records']:,}개")
        print(f"   총 요청 수: {self.stats['total_requests']:,}")
        print(f"   소요 시간: {duration}")
        
        if self.stats["errors"]:
            print(f"\n⚠️  오류 발생: {len(self.stats['errors'])}건")
            print("   최근 오류:")
            for error in self.stats["errors"][-5:]:
                print(f"     - {error}")


def run_history_update(market_kinds: List[int] = None,
                      timeframe: HistoryTimeframe = HistoryTimeframe.DAILY,
                      batch_size: int = 10,
                      incremental: bool = True,
                      dry_run: bool = False) -> Dict[str, Any]:
    """편의 함수: 히스토리 데이터 업데이트 실행"""
    service = HistoryUpdateService(batch_size=batch_size)
    return service.run_full_history_update(
        market_kinds=market_kinds,
        timeframe=timeframe,
        incremental=incremental,
        dry_run=dry_run
    )

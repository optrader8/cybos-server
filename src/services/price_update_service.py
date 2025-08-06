"""
Price Update Service - 시세 업데이트 배치 서비스

매일 정기적으로 실행되어 전체 종목의 시세를 안전하게 업데이트하는 서비스입니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..database.connection import get_connection_context
from ..database.models.stock import StockTable, MarketKind
from ..database.models.price import PriceTable, PriceInfo
from ..cybos.price.fetcher import get_price_fetcher


class PriceUpdateService:
    """시세 업데이트 서비스 클래스"""
    
    def __init__(self, 
                 db_path: str = "data/cybos.db",
                 batch_size: int = 30,
                 min_delay: float = 2.0,
                 max_delay: float = 5.0,
                 max_requests_per_hour: int = 500):
        
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
            "errors": []
        }
    
    def get_target_stocks(self, market_kinds: List[int] = None) -> List[Dict[str, Any]]:
        """업데이트 대상 종목 목록 조회"""
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
        # 배치 수 계산
        total_batches = (total_stocks + self.batch_size - 1) // self.batch_size
        
        # 시간당 최대 요청 수를 고려한 최소 간격 계산
        min_interval = 3600 / self.max_requests_per_hour  # 초 단위
        safe_interval = max(min_interval, self.min_delay)
        
        # 예상 소요 시간 계산
        estimated_time = total_batches * (safe_interval + self.max_delay)
        
        return {
            "total_stocks": total_stocks,
            "total_batches": total_batches,
            "safe_interval": safe_interval,
            "estimated_time_minutes": estimated_time / 60,
            "estimated_completion": datetime.now() + timedelta(seconds=estimated_time)
        }
    
    def update_prices_batch(self, stocks: List[Dict[str, Any]]) -> List[PriceInfo]:
        """배치 단위로 시세 업데이트"""
        fetcher = get_price_fetcher(self.min_delay, self.max_delay)
        
        # 종목 코드 리스트 생성
        codes = [stock["code"] for stock in stocks]
        
        try:
            # 시세 데이터 조회
            prices = fetcher.fetch_multiple_prices_batch(codes, len(codes))
            
            # 데이터베이스에 저장
            if prices:
                with get_connection_context(self.db_path) as conn:
                    for price in prices:
                        try:
                            PriceTable.insert_price(conn, price)
                        except Exception as e:
                            self.stats["errors"].append(f"DB insert error for {price.code}: {e}")
                    
                    conn.commit()
            
            self.stats["total_requests"] += 1
            return prices
            
        except Exception as e:
            error_msg = f"Batch update failed for codes {codes[:3]}...: {e}"
            self.stats["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            return []
    
    def run_full_update(self, market_kinds: List[int] = None, dry_run: bool = False) -> Dict[str, Any]:
        """전체 시세 업데이트 실행"""
        print("🚀 시세 업데이트 서비스 시작")
        print("=" * 50)
        
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
            print(f"   예상 소요 시간: {schedule['estimated_time_minutes']:.1f}분")
            print(f"   예상 완료 시간: {schedule['estimated_completion'].strftime('%H:%M:%S')}")
            
            if dry_run:
                print("🔍 DRY RUN 모드 - 실제 업데이트는 수행하지 않습니다.")
                return self.stats
            
            # 확인 메시지
            response = input("\n계속하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("사용자에 의해 취소되었습니다.")
                return self.stats
            
            # 배치 단위로 처리
            print(f"\n📈 시세 업데이트 시작...")
            
            for i in range(0, len(target_stocks), self.batch_size):
                batch_stocks = target_stocks[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1
                total_batches = schedule["total_batches"]
                
                print(f"\n🔄 배치 {batch_num}/{total_batches} 처리 중... ({len(batch_stocks)}개 종목)")
                
                # 배치 처리
                batch_start = time.time()
                updated_prices = self.update_prices_batch(batch_stocks)
                batch_time = time.time() - batch_start
                
                # 통계 업데이트
                self.stats["processed_stocks"] += len(batch_stocks)
                self.stats["successful_stocks"] += len(updated_prices)
                self.stats["failed_stocks"] += len(batch_stocks) - len(updated_prices)
                
                # 진행 상황 출력
                success_rate = len(updated_prices) / len(batch_stocks) * 100
                print(f"   ✅ 성공: {len(updated_prices)}/{len(batch_stocks)} ({success_rate:.1f}%)")
                print(f"   ⏱️  소요 시간: {batch_time:.1f}초")
                
                # 전체 진행률 계산
                progress = (batch_num / total_batches) * 100
                print(f"   📊 전체 진행률: {progress:.1f}%")
                
                # 불규칙한 대기 시간
                if batch_num < total_batches:
                    wait_time = random.uniform(3.0, 10.0)
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
        
        print("\n" + "=" * 50)
        print("🎉 시세 업데이트 완료!")
        print(f"📊 최종 결과:")
        print(f"   전체 종목: {self.stats['total_stocks']:,}")
        print(f"   처리 종목: {self.stats['processed_stocks']:,}")
        print(f"   성공 종목: {self.stats['successful_stocks']:,}")
        print(f"   실패 종목: {self.stats['failed_stocks']:,}")
        print(f"   성공률: {success_rate:.1f}%")
        print(f"   총 요청 수: {self.stats['total_requests']:,}")
        print(f"   소요 시간: {duration}")
        
        if self.stats["errors"]:
            print(f"\n⚠️  오류 발생: {len(self.stats['errors'])}건")
            print("   최근 오류:")
            for error in self.stats["errors"][-5:]:  # 최근 5개만 표시
                print(f"     - {error}")
    
    def update_prices_for_stocks(self, stock_codes: List[str], dry_run: bool = False) -> Dict[str, Any]:
        """특정 종목들의 시세 업데이트"""
        print("🚀 특정 종목 시세 업데이트 서비스 시작")
        print("=" * 50)
        
        # 통계 초기화
        self.stats["start_time"] = datetime.now()
        self.stats["errors"] = []
        
        try:
            # 종목 코드를 StockInfo 형태로 변환 (모든 코드는 이미 A 접두사 포함)
            target_stocks = []
            
            with get_connection_context(self.db_path) as conn:
                for code in stock_codes:
                    stock_info = StockTable.get_stock(conn, code)
                    if stock_info:
                        target_stocks.append({
                            'code': stock_info.code,
                            'name': stock_info.name,
                            'market_kind': stock_info.market_kind
                        })
                    else:
                        print(f"⚠️  종목을 찾을 수 없음: {code}")
            
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
            print(f"   예상 소요 시간: {schedule['estimated_time_minutes']:.1f}분")
            print(f"   예상 완료 시간: {schedule['estimated_completion'].strftime('%H:%M:%S')}")
            
            if dry_run:
                print("🔍 DRY RUN 모드 - 실제 업데이트는 수행하지 않습니다.")
                return self.stats
            
            # 확인 메시지
            response = input("\n계속하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("사용자에 의해 취소되었습니다.")
                return self.stats
            
            # 배치 단위로 처리
            print(f"\n📈 시세 업데이트 시작...")
            
            for i in range(0, len(target_stocks), self.batch_size):
                batch_stocks = target_stocks[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1
                total_batches = schedule["total_batches"]
                
                print(f"\n🔄 배치 {batch_num}/{total_batches} 처리 중... ({len(batch_stocks)}개 종목)")
                
                # 배치 처리
                batch_start = time.time()
                updated_prices = self.update_prices_batch(batch_stocks)
                batch_time = time.time() - batch_start
                
                # 통계 업데이트
                self.stats["processed_stocks"] += len(batch_stocks)
                self.stats["successful_stocks"] += len(updated_prices)
                self.stats["failed_stocks"] += len(batch_stocks) - len(updated_prices)
                
                # 진행 상황 출력
                success_rate = len(updated_prices) / len(batch_stocks) * 100
                print(f"   ✅ 성공: {len(updated_prices)}/{len(batch_stocks)} ({success_rate:.1f}%)")
                print(f"   ⏱️  소요 시간: {batch_time:.1f}초")
                
                # 전체 진행률 계산
                progress = (batch_num / total_batches) * 100
                print(f"   📊 전체 진행률: {progress:.1f}%")
                
                # 불규칙한 대기 시간
                if batch_num < total_batches:
                    wait_time = random.uniform(3.0, 10.0)
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

    def cleanup_old_prices(self, days: int = 30) -> int:
        """오래된 시세 데이터 정리"""
        with get_connection_context(self.db_path) as conn:
            deleted_count = PriceTable.cleanup_old_data(conn, days)
            
        print(f"🗑️  {days}일 이전 데이터 {deleted_count:,}건 삭제 완료")
        return deleted_count


def run_price_update(market_kinds: List[int] = None, 
                    batch_size: int = 30,
                    dry_run: bool = False) -> Dict[str, Any]:
    """편의 함수: 시세 업데이트 실행"""
    service = PriceUpdateService(batch_size=batch_size)
    return service.run_full_update(market_kinds, dry_run)

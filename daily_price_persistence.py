"""
Daily Price Persistence Service - 일간 시세 데이터 영속성 보장 서비스

실행 일자를 기준으로:
1. StockMst로 당일 시세 데이터를 수집하여 히스토리 DB에 저장
2. 데이터 공백(Gap) 탐지 및 분석 
3. 공백이 3일 이상이면 StockChart로 보완 데이터 수집
4. FastAPI REST API 호출 가능한 구조로 설계
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import argparse

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import win32com.client
    from src.database.connection import get_connection_context
    from src.database.models.history import HistoryTable, HistoryTimeframe, HistoryInfo
    from src.database.models.stock import StockTable
    from src.cybos.history.fetcher import get_history_fetcher
except ImportError as e:
    print(f"Import error: {e}")
    print("Cybos Plus 환경에서 실행해주세요.")
    sys.exit(1)


class DailyPricePersistenceService:
    """일간 시세 데이터 영속성 보장 서비스 클래스"""
    
    def __init__(self, db_path: str = "data/cybos.db"):
        self.db_path = db_path
        self.gap_threshold_days = 3  # 3일 이상 공백 시 보완
        self.backfill_days = 10      # 보완 시 10일치 데이터 요청
        
        # 통계 정보
        self.stats = {
            "processed_stocks": 0,
            "daily_updates": 0,
            "gaps_detected": 0,
            "gaps_filled": 0,
            "errors": []
        }
    
    def check_cybos_connection(self) -> bool:
        """Cybos Plus 연결 확인"""
        try:
            cybos = win32com.client.Dispatch("CpUtil.CpCybos")
            if cybos.IsConnect:
                return True
            else:
                print("❌ Cybos Plus 연결되지 않음")
                return False
        except Exception as e:
            print(f"❌ Cybos Plus 연결 확인 실패: {e}")
            return False
    
    def get_daily_price_from_stockmst(self, code: str) -> Optional[HistoryInfo]:
        """StockMst로 당일 시세 데이터 조회"""
        try:
            # StockMst COM 객체 생성
            stockmst = win32com.client.Dispatch("dscbo1.StockMst")
            
            # 종목 코드 설정
            stockmst.SetInputValue(0, code)
            
            # 요청 실행
            ret = stockmst.BlockRequest()
            if ret != 0:
                print(f"   ⚠️  StockMst 요청 실패 ({code}): {ret}")
                return None
            
            # 현재가 정보 조회
            current_price = stockmst.GetHeaderValue(11)    # 현재가
            open_price = stockmst.GetHeaderValue(13)       # 시가
            high_price = stockmst.GetHeaderValue(14)       # 고가  
            low_price = stockmst.GetHeaderValue(15)        # 저가
            volume = stockmst.GetHeaderValue(18)           # 거래량
            
            # 유효성 검사
            if current_price <= 0 or open_price <= 0:
                print(f"   ⚠️  유효하지 않은 가격 데이터 ({code})")
                return None
            
            # HistoryInfo 객체 생성
            today = datetime.now().strftime('%Y-%m-%d')
            
            history_info = HistoryInfo(
                code=code,
                timeframe=HistoryTimeframe.DAILY,
                date=today,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=current_price,  # 현재가를 종가로 사용
                volume=volume
            )
            
            print(f"   📊 StockMst 데이터: {code} - O:{open_price} H:{high_price} L:{low_price} C:{current_price} V:{volume:,}")
            return history_info
            
        except Exception as e:
            print(f"   ❌ StockMst 조회 실패 ({code}): {e}")
            return None
    
    def detect_data_gaps(self, code: str, target_date: str = None) -> List[Tuple[str, str]]:
        """데이터 공백 구간 탐지"""
        if target_date is None:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        gaps = []
        
        try:
            with get_connection_context(self.db_path) as conn:
                # 최근 30일간의 데이터 조회
                cursor = conn.execute(f"""
                    SELECT date FROM {HistoryTable.TABLE_NAME}
                    WHERE code = ? AND timeframe = 'D'
                    AND date >= date(?, '-30 days')
                    ORDER BY date DESC
                """, (code, target_date))
                
                existing_dates = [row[0] for row in cursor.fetchall()]
                
                if not existing_dates:
                    # 데이터가 전혀 없는 경우
                    start_date = (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
                    gaps.append((start_date, target_date))
                    return gaps
                
                # 날짜 순으로 정렬 (오래된 것부터)
                existing_dates.sort()
                
                # 공백 구간 찾기
                current_date = datetime.strptime(target_date, '%Y-%m-%d')
                gap_start = None
                gap_days = 0
                
                for i in range(30):  # 최근 30일 체크
                    check_date = (current_date - timedelta(days=i)).strftime('%Y-%m-%d')
                    
                    # 주말 제외 (토요일: 5, 일요일: 6)
                    weekday = (current_date - timedelta(days=i)).weekday()
                    if weekday >= 5:  # 주말은 스킵
                        continue
                    
                    if check_date not in existing_dates:
                        if gap_start is None:
                            gap_start = check_date
                        gap_days += 1
                    else:
                        if gap_start is not None and gap_days >= self.gap_threshold_days:
                            gaps.append((gap_start, check_date))
                        gap_start = None
                        gap_days = 0
                
                # 마지막 공백 처리
                if gap_start is not None and gap_days >= self.gap_threshold_days:
                    oldest_check = (current_date - timedelta(days=29)).strftime('%Y-%m-%d')
                    gaps.append((oldest_check, gap_start))
                
                return gaps
                
        except Exception as e:
            print(f"   ❌ 공백 탐지 실패 ({code}): {e}")
            return []
    
    def fill_data_gaps(self, code: str, gaps: List[Tuple[str, str]]) -> int:
        """StockChart로 데이터 공백 보완"""
        if not gaps:
            return 0
        
        filled_records = 0
        
        try:
            fetcher = get_history_fetcher(min_delay=1.0, max_delay=2.0)
            
            for gap_start, gap_end in gaps:
                print(f"   🔧 공백 보완: {gap_start} ~ {gap_end}")
                
                # 보완할 데이터 범위 계산
                gap_start_date = datetime.strptime(gap_start, '%Y-%m-%d')
                extra_days = self.backfill_days
                
                # StockChart로 히스토리 데이터 조회
                history_list = fetcher.fetch_daily_history(code, extra_days)
                
                if history_list:
                    # 공백 구간에 해당하는 데이터만 필터링
                    gap_end_date = datetime.strptime(gap_end, '%Y-%m-%d')
                    
                    filtered_history = []
                    for history in history_list:
                        history_date = datetime.strptime(history.date, '%Y-%m-%d')
                        if gap_start_date <= history_date <= gap_end_date:
                            filtered_history.append(history)
                    
                    # 데이터베이스에 저장
                    with get_connection_context(self.db_path) as conn:
                        for history in filtered_history:
                            try:
                                HistoryTable.upsert_history(conn, history)
                                filled_records += 1
                                print(f"   ✅ 보완: {history.date} - O:{history.open_price} C:{history.close_price}")
                            except Exception as e:
                                print(f"   ⚠️  저장 실패: {history.date} - {e}")
                        
                        conn.commit()
                    
                    print(f"   📊 공백 보완 완료: {len(filtered_history)}개 레코드 추가")
                else:
                    print(f"   ❌ StockChart 데이터 없음")
        
        except Exception as e:
            print(f"   ❌ 공백 보완 실패 ({code}): {e}")
        
        return filled_records
    
    def process_single_stock(self, code: str, name: str = None, 
                           update_daily: bool = True, 
                           fill_gaps: bool = True) -> Dict:
        """단일 종목 일간 데이터 영속성 처리"""
        result = {
            "code": code,
            "name": name or "Unknown",
            "daily_updated": False,
            "gaps_detected": 0,
            "gaps_filled": 0,
            "errors": []
        }
        
        print(f"\n🔄 [{code}] {name or 'Unknown'} 처리 중...")
        
        try:
            # 1. 당일 시세 데이터 업데이트
            if update_daily:
                daily_data = self.get_daily_price_from_stockmst(code)
                
                if daily_data:
                    with get_connection_context(self.db_path) as conn:
                        try:
                            HistoryTable.upsert_history(conn, daily_data)
                            conn.commit()
                            result["daily_updated"] = True
                            self.stats["daily_updates"] += 1
                            print(f"   ✅ 당일 데이터 저장 완료: {daily_data.date}")
                        except Exception as e:
                            error_msg = f"당일 데이터 저장 실패: {e}"
                            result["errors"].append(error_msg)
                            print(f"   ❌ {error_msg}")
                else:
                    error_msg = "당일 시세 데이터 조회 실패"
                    result["errors"].append(error_msg)
                    print(f"   ❌ {error_msg}")
                
                # API 호출 제한
                time.sleep(0.2)
            
            # 2. 데이터 공백 탐지 및 보완
            if fill_gaps:
                gaps = self.detect_data_gaps(code)
                result["gaps_detected"] = len(gaps)
                
                if gaps:
                    print(f"   📊 공백 구간 {len(gaps)}개 탐지")
                    self.stats["gaps_detected"] += len(gaps)
                    
                    filled_count = self.fill_data_gaps(code, gaps)
                    result["gaps_filled"] = filled_count
                    self.stats["gaps_filled"] += filled_count
                else:
                    print(f"   ✅ 공백 없음")
            
            self.stats["processed_stocks"] += 1
            
        except Exception as e:
            error_msg = f"처리 실패: {e}"
            result["errors"].append(error_msg)
            self.stats["errors"].append(f"{code}: {error_msg}")
            print(f"   ❌ {error_msg}")
        
        return result
    
    def process_kospi200_stocks(self, update_daily: bool = True, 
                               fill_gaps: bool = True,
                               max_stocks: int = None) -> List[Dict]:
        """KOSPI200 전체 종목 처리"""
        print("🎯 KOSPI200 종목 일간 데이터 영속성 처리")
        print("=" * 60)
        
        results = []
        
        try:
            # 검증 CSV에서 데이터가 있는 종목들 조회
            with get_connection_context(self.db_path) as conn:
                cursor = conn.execute(f"""
                    SELECT DISTINCT s.code, s.name 
                    FROM {StockTable.TABLE_NAME} s
                    WHERE s.market_kind = 1 AND s.kospi200_kind != 0
                    ORDER BY s.code
                """)
                
                stocks = cursor.fetchall()
            
            print(f"📊 대상 종목: {len(stocks)}개")
            
            if max_stocks:
                stocks = stocks[:max_stocks]
                print(f"   (제한: {max_stocks}개만 처리)")
            
            # 각 종목 처리
            for i, (code, name) in enumerate(stocks, 1):
                print(f"\n🔄 [{i}/{len(stocks)}] 진행률: {(i/len(stocks)*100):.1f}%")
                
                result = self.process_single_stock(
                    code=code, 
                    name=name,
                    update_daily=update_daily,
                    fill_gaps=fill_gaps
                )
                
                results.append(result)
                
                # 5개마다 진행상황 요약
                if i % 5 == 0:
                    success_rate = (self.stats["daily_updates"] / self.stats["processed_stocks"]) * 100
                    print(f"   📊 중간 현황: 성공률 {success_rate:.1f}%, 공백보완 {self.stats['gaps_filled']}개")
            
            return results
            
        except Exception as e:
            error_msg = f"전체 처리 실패: {e}"
            self.stats["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            return results
    
    def print_summary(self, results: List[Dict]) -> None:
        """처리 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("📋 일간 데이터 영속성 처리 완료!")
        print("=" * 60)
        
        # 기본 통계
        total_stocks = len(results)
        successful_daily = len([r for r in results if r["daily_updated"]])
        total_gaps_detected = sum(r["gaps_detected"] for r in results)
        total_gaps_filled = sum(r["gaps_filled"] for r in results)
        
        print(f"📊 처리 결과:")
        print(f"   전체 종목: {total_stocks:,}개")
        print(f"   당일 업데이트 성공: {successful_daily:,}개 ({successful_daily/max(total_stocks,1)*100:.1f}%)")
        print(f"   탐지된 공백: {total_gaps_detected:,}개")
        print(f"   보완된 공백: {total_gaps_filled:,}개")
        
        if self.stats["errors"]:
            print(f"\n⚠️  오류 발생: {len(self.stats['errors'])}건")
            for error in self.stats["errors"][-5:]:  # 최근 5개만
                print(f"     - {error}")
        
        # 공백이 많이 보완된 종목
        top_filled = sorted([r for r in results if r["gaps_filled"] > 0], 
                           key=lambda x: x["gaps_filled"], reverse=True)[:5]
        
        if top_filled:
            print(f"\n🔧 공백 보완이 많은 종목 (상위 5개):")
            for result in top_filled:
                print(f"   {result['code']} ({result['name']}): {result['gaps_filled']}개 보완")
    
    # FastAPI용 메서드들
    def process_stock_api(self, code: str, update_daily: bool = True, 
                         fill_gaps: bool = True) -> Dict:
        """단일 종목 처리 (API용)"""
        if not self.check_cybos_connection():
            return {"error": "Cybos Plus 연결 실패"}
        
        result = self.process_single_stock(code, update_daily=update_daily, fill_gaps=fill_gaps)
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_gaps_api(self, code: str, target_date: str = None) -> Dict:
        """공백 조회 (API용)"""
        try:
            gaps = self.detect_data_gaps(code, target_date)
            return {
                "success": True,
                "data": {
                    "code": code,
                    "target_date": target_date or datetime.now().strftime('%Y-%m-%d'),
                    "gaps_count": len(gaps),
                    "gaps": [{"start": start, "end": end} for start, end in gaps]
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def batch_process_api(self, codes: List[str], update_daily: bool = True, 
                         fill_gaps: bool = True) -> Dict:
        """배치 처리 (API용)"""
        if not self.check_cybos_connection():
            return {"error": "Cybos Plus 연결 실패"}
        
        results = []
        for code in codes:
            result = self.process_single_stock(code, update_daily=update_daily, fill_gaps=fill_gaps)
            results.append(result)
        
        return {
            "success": True,
            "data": {
                "processed_count": len(results),
                "results": results
            },
            "timestamp": datetime.now().isoformat()
        }


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="일간 시세 데이터 영속성 보장 서비스")
    
    parser.add_argument("--code", type=str, help="단일 종목 코드 (예: 005930)")
    parser.add_argument("--no-daily", action="store_true", help="당일 업데이트 건너뛰기")
    parser.add_argument("--no-gaps", action="store_true", help="공백 보완 건너뛰기")
    parser.add_argument("--max-stocks", type=int, help="최대 처리 종목 수 제한")
    parser.add_argument("--gaps-only", type=str, help="특정 종목의 공백만 조회")
    
    args = parser.parse_args()
    
    print("🎯 일간 시세 데이터 영속성 보장 서비스")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    service = DailyPricePersistenceService()
    
    # 연결 확인
    if not service.check_cybos_connection():
        return
    
    try:
        if args.gaps_only:
            # 공백만 조회
            print(f"🔍 {args.gaps_only} 종목의 공백 구간 조회")
            gaps = service.detect_data_gaps(args.gaps_only)
            print(f"📊 공백 구간: {len(gaps)}개")
            for i, (start, end) in enumerate(gaps, 1):
                print(f"   {i}. {start} ~ {end}")
            
        elif args.code:
            # 단일 종목 처리
            print(f"🎯 단일 종목 처리: {args.code}")
            result = service.process_single_stock(
                code=args.code,
                update_daily=not args.no_daily,
                fill_gaps=not args.no_gaps
            )
            print(f"\n✅ 처리 완료: {result}")
            
        else:
            # KOSPI200 전체 처리
            print("🎯 KOSPI200 전체 종목 처리")
            if not args.no_daily and not args.no_gaps:
                response = input("당일 업데이트 + 공백 보완을 실행하시겠습니까? (y/N): ")
                if response.lower() != 'y':
                    print("사용자에 의해 취소되었습니다.")
                    return
            
            results = service.process_kospi200_stocks(
                update_daily=not args.no_daily,
                fill_gaps=not args.no_gaps,
                max_stocks=args.max_stocks
            )
            
            service.print_summary(results)
    
    except KeyboardInterrupt:
        print("\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 실행 오류: {e}")


if __name__ == "__main__":
    main()

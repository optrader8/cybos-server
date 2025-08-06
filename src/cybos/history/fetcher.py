"""
History Data Fetcher - 히스토리 데이터 수집 클래스

StockChart API를 사용하여 일봉, 주봉, 월봉 히스토리 데이터를 안전하게 수집합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import time
import random
import win32com.client
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ...core.constants import LT_NONTRADE_REQUEST
from ...database.models.history import HistoryInfo, HistoryTimeframe


class SafeHistoryFetcher:
    """안전한 히스토리 데이터 수집 클래스"""
    
    def __init__(self, min_delay: float = 2.0, max_delay: float = 5.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self._cybos = None
        self._stock_chart = None
        self._initialize_com_objects()
    
    def _initialize_com_objects(self) -> None:
        """COM 객체 초기화"""
        try:
            self._cybos = win32com.client.Dispatch("CpUtil.CpCybos")
            self._stock_chart = win32com.client.Dispatch("CpSysDib.StockChart")
            print("✅ StockChart COM 객체 초기화 완료")
        except Exception as e:
            print(f"❌ COM 객체 초기화 실패: {e}")
            raise
    
    def check_connection(self) -> bool:
        """연결 상태 확인"""
        try:
            return self._cybos.IsConnect == 1
        except Exception:
            return False
    
    def get_request_limit_info(self) -> Dict[str, Any]:
        """요청 제한 정보 조회"""
        try:
            remain_count = self._cybos.GetLimitRemainCount(LT_NONTRADE_REQUEST)
            remain_time = self._cybos.LimitRequestRemainTime
            
            return {
                "remain_count": remain_count,
                "remain_time_ms": remain_time,
                "remain_time_sec": remain_time / 1000.0,
                "is_safe": remain_count > 10
            }
        except Exception as e:
            print(f"Warning: Could not get limit info: {e}")
            return {
                "remain_count": 0,
                "remain_time_ms": 0,
                "remain_time_sec": 0,
                "is_safe": False
            }
    
    def wait_if_needed(self) -> None:
        """필요시 대기"""
        limit_info = self.get_request_limit_info()
        
        # 요청 가능 횟수가 부족한 경우 대기
        if not limit_info["is_safe"]:
            wait_time = max(limit_info["remain_time_sec"] + 1, 5)
            print(f"⏳ Request limit reached. Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
        
        # 기본 지연 시간 (불규칙)
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
    
    def fetch_daily_history(self, code: str, count: int = 5000) -> List[HistoryInfo]:
        """일봉 히스토리 데이터 수집"""
        return self._fetch_history_internal(code, HistoryTimeframe.DAILY, count)
    
    def fetch_weekly_history(self, code: str, count: int = 1000) -> List[HistoryInfo]:
        """주봉 히스토리 데이터 수집"""
        return self._fetch_history_internal(code, HistoryTimeframe.WEEKLY, count)
    
    def fetch_monthly_history(self, code: str, count: int = 500) -> List[HistoryInfo]:
        """월봉 히스토리 데이터 수집"""
        return self._fetch_history_internal(code, HistoryTimeframe.MONTHLY, count)
    
    def _fetch_history_internal(self, code: str, timeframe: HistoryTimeframe, count: int) -> List[HistoryInfo]:
        """히스토리 데이터 내부 수집 함수"""
        try:
            if not self.check_connection():
                raise ConnectionError("Cybos Plus not connected")
            
            # 안전 대기
            self.wait_if_needed()
            
            # A 접두사 처리
            query_code = code if code.startswith("A") else f"A{code}"
            
            # 입력 설정
            self._stock_chart.SetInputValue(0, query_code)          # 종목코드
            self._stock_chart.SetInputValue(1, ord('2'))            # 개수로 요청
            self._stock_chart.SetInputValue(4, count)               # 요청개수
            self._stock_chart.SetInputValue(5, [0, 2, 3, 4, 5, 8, 9])  # 필드: 날짜,시가,고가,저가,종가,거래량,거래대금
            self._stock_chart.SetInputValue(6, ord(timeframe.value)) # 차트구분
            self._stock_chart.SetInputValue(9, ord('1'))            # 수정주가 적용
            
            # 데이터 요청
            result = self._stock_chart.BlockRequest()
            if result != 0:
                print(f"History request failed for {query_code}: error code {result}")
                return []
            
            # 데이터 추출
            return self._extract_history_data(code, timeframe)
            
        except Exception as e:
            print(f"Error fetching history for {code}: {e}")
            return []
    
    def _extract_history_data(self, code: str, timeframe: HistoryTimeframe) -> List[HistoryInfo]:
        """히스토리 데이터 추출"""
        try:
            count = self._stock_chart.GetHeaderValue(3)  # 수신개수
            if count <= 0:
                return []
            
            history_list = []
            
            for i in range(count):
                # 필드 데이터 추출 (요청 순서대로: 0,2,3,4,5,8,9)
                date_val = self._stock_chart.GetDataValue(0, i)      # 날짜
                open_price = self._stock_chart.GetDataValue(1, i)    # 시가
                high_price = self._stock_chart.GetDataValue(2, i)    # 고가
                low_price = self._stock_chart.GetDataValue(3, i)     # 저가
                close_price = self._stock_chart.GetDataValue(4, i)   # 종가
                volume = self._stock_chart.GetDataValue(5, i)        # 거래량
                amount = self._stock_chart.GetDataValue(6, i)        # 거래대금
                
                # 날짜 포맷 변환 (YYYYMMDD -> YYYY-MM-DD)
                if isinstance(date_val, (int, float)):
                    date_str = str(int(date_val))
                    if len(date_str) == 8:
                        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    else:
                        continue  # 잘못된 날짜 형식은 건너뛰기
                else:
                    continue
                
                # HistoryInfo 객체 생성
                history = HistoryInfo(
                    code=code,  # 원본 코드 (A 접두사 제거)
                    timeframe=timeframe,
                    date=formatted_date,
                    open_price=int(open_price) if open_price else 0,
                    high_price=int(high_price) if high_price else 0,
                    low_price=int(low_price) if low_price else 0,
                    close_price=int(close_price) if close_price else 0,
                    volume=int(volume) if volume else 0,
                    amount=int(amount) if amount else 0
                )
                
                history_list.append(history)
            
            # 날짜 오름차순 정렬 (과거 -> 현재)
            history_list.sort(key=lambda x: x.date)
            
            print(f"✅ {code} {timeframe.value}봉 히스토리 {len(history_list)}개 수집 완료")
            return history_list
            
        except Exception as e:
            print(f"Error extracting history data: {e}")
            return []


def get_history_fetcher(min_delay: float = 2.0, max_delay: float = 5.0) -> SafeHistoryFetcher:
    """히스토리 수집기 팩토리 함수"""
    return SafeHistoryFetcher(min_delay=min_delay, max_delay=max_delay)

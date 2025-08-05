"""
Safe Price Fetcher - 안전한 시세 데이터 수집기

Cybos Plus API 요청 제한을 고려한 안전하고 효율적인 시세 수집 시스템입니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import win32com.client
import time
import random
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...database.models.price import PriceInfo
from ...core.constants import LT_NONTRADE_REQUEST


class SafePriceFetcher:
    """안전한 시세 데이터 수집 클래스"""
    
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self._cybos = None
        self._stock_mst = None
        self._stock_mst2 = None
        self._stock_mst_m = None
        self._initialize_com_objects()
    
    def _initialize_com_objects(self) -> None:
        """COM 객체 초기화"""
        try:
            self._cybos = win32com.client.Dispatch("CpUtil.CpCybos")
            self._stock_mst = win32com.client.Dispatch("dscbo1.StockMst")
            self._stock_mst2 = win32com.client.Dispatch("dscbo1.StockMst2")
            self._stock_mst_m = win32com.client.Dispatch("dscbo1.StockMstM")
        except Exception as e:
            raise ConnectionError(f"Failed to initialize COM objects: {e}")
    
    def check_connection(self) -> bool:
        """연결 상태 확인"""
        try:
            return self._cybos.IsConnect == 1
        except:
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
                "is_safe": remain_count > 10  # 안전 기준: 10개 이상 남음
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
            wait_time = max(limit_info["remain_time_sec"] + 1, 5)  # 최소 5초
            print(f"⏳ Request limit reached. Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
        
        # 기본 지연 시간 (불규칙)
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
    
    def fetch_single_price(self, code: str) -> Optional[PriceInfo]:
        """단일 종목 시세 조회 (StockMst 사용)"""
        try:
            if not self.check_connection():
                raise ConnectionError("Cybos Plus not connected")
            
            # A 접두사가 없으면 추가 (test_2.py와 동일하게)
            query_code = code if code.startswith("A") else f"A{code}"
            
            # 기본 지연 시간만 적용 (불필요한 대기 제거)
            delay = random.uniform(0.5, 1.5)
            time.sleep(delay)
            
            # 종목 코드 설정
            self._stock_mst.SetInputValue(0, query_code)
            
            # 데이터 요청
            result = self._stock_mst.BlockRequest()
            if result != 0:
                print(f"Request failed for {query_code}: error code {result}")
                return None
            
            # 데이터 추출
            price_info = self._extract_single_price_data(code)  # 원본 코드 사용
            return price_info
            
        except Exception as e:
            print(f"Error fetching price for {code}: {e}")
            return None
    
    def _extract_single_price_data(self, code: str) -> PriceInfo:
        """StockMst 응답에서 시세 데이터 추출"""
        try:
            # 기본 정보
            name = self._stock_mst.GetHeaderValue(1)
            time_val = self._stock_mst.GetHeaderValue(4)
            
            # 가격 정보
            current_price = self._stock_mst.GetHeaderValue(11)
            change = self._stock_mst.GetHeaderValue(12)
            open_price = self._stock_mst.GetHeaderValue(13)
            high_price = self._stock_mst.GetHeaderValue(14)
            low_price = self._stock_mst.GetHeaderValue(15)
            ask_price = self._stock_mst.GetHeaderValue(16)
            bid_price = self._stock_mst.GetHeaderValue(17)
            volume = self._stock_mst.GetHeaderValue(18)
            prev_close = self._stock_mst.GetHeaderValue(10)
            
            # 상태 구분 계산
            status = 3  # 기본값: 보합
            if change > 0:
                status = 2  # 상승
            elif change < 0:
                status = 5  # 하락
            
            return PriceInfo(
                code=code,
                name=name,
                time=str(time_val).zfill(4),
                current_price=current_price,
                change=change,
                status=status,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                prev_close=prev_close,
                ask_price=ask_price,
                bid_price=bid_price,
                volume=volume
            )
            
        except Exception as e:
            raise ValueError(f"Failed to extract price data for {code}: {e}")
    
    def fetch_multiple_prices_batch(self, codes: List[str], batch_size: int = 50) -> List[PriceInfo]:
        """여러 종목 시세 일괄 조회 (StockMst2 사용)"""
        try:
            if not self.check_connection():
                raise ConnectionError("Cybos Plus not connected")
            
            # 배치 크기로 나누어 처리
            all_results = []
            
            for i in range(0, len(codes), batch_size):
                batch_codes = codes[i:i + batch_size]
                batch_results = self._fetch_batch_internal(batch_codes)
                all_results.extend(batch_results)
                
                # 배치 간 대기
                if i + batch_size < len(codes):
                    print(f"Processed batch {i//batch_size + 1}, waiting before next batch...")
                    self.wait_if_needed()
            
            return all_results
            
        except Exception as e:
            print(f"Error in batch fetch: {e}")
            return []
    
    def _fetch_batch_internal(self, codes: List[str]) -> List[PriceInfo]:
        """내부 배치 처리 함수"""
        try:
            # 기본 지연 시간만 적용
            delay = random.uniform(0.5, 1.5)
            time.sleep(delay)
            
            # A 접두사 추가 (단일 조회와 동일하게)
            query_codes = [code if code.startswith("A") else f"A{code}" for code in codes]
            code_string = ",".join(query_codes)
            
            # 입력값 설정
            self._stock_mst2.SetInputValue(0, code_string)
            
            # 데이터 요청
            result = self._stock_mst2.BlockRequest()
            if result != 0:
                print(f"Batch request failed: error code {result}")
                return []
            
            # 데이터 추출
            count = self._stock_mst2.GetHeaderValue(0)
            prices = []
            
            for i in range(count):
                try:
                    price_info = self._extract_batch_price_data(i, codes[i] if i < len(codes) else None)
                    if price_info:
                        prices.append(price_info)
                except Exception as e:
                    print(f"Error extracting data for index {i}: {e}")
                    continue
            
            return prices
            
        except Exception as e:
            print(f"Error in internal batch fetch: {e}")
            return []
    
    def _extract_batch_price_data(self, index: int, original_code: str = None) -> Optional[PriceInfo]:
        """StockMst2 응답에서 시세 데이터 추출"""
        try:
            # 기본 정보
            code = self._stock_mst2.GetDataValue(0, index)
            name = self._stock_mst2.GetDataValue(1, index)
            time_val = self._stock_mst2.GetDataValue(2, index)
            
            # A 접두사 제거해서 원본 코드 사용
            if original_code:
                code = original_code
            elif code.startswith("A"):
                code = code[1:]
            
            # 가격 정보
            current_price = self._stock_mst2.GetDataValue(3, index)
            change = self._stock_mst2.GetDataValue(4, index)
            
            # 상태 정보 (문자열이면 ord() 사용, 정수면 그대로 사용)
            status_raw = self._stock_mst2.GetDataValue(5, index)
            if isinstance(status_raw, str):
                status = ord(status_raw)
            else:
                status = int(status_raw) if status_raw is not None else 3
            
            # OHLC
            open_price = self._stock_mst2.GetDataValue(6, index)
            high_price = self._stock_mst2.GetDataValue(7, index)
            low_price = self._stock_mst2.GetDataValue(8, index)
            
            # 호가
            ask_price = self._stock_mst2.GetDataValue(9, index)
            bid_price = self._stock_mst2.GetDataValue(10, index)
            
            # 거래량
            volume = self._stock_mst2.GetDataValue(11, index)
            amount = self._stock_mst2.GetDataValue(12, index)
            
            # 전일종가
            prev_close = self._stock_mst2.GetDataValue(19, index)
            
            return PriceInfo(
                code=code,
                name=name,
                time=str(time_val).zfill(4),
                current_price=current_price,
                change=change,
                status=status,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                prev_close=prev_close,
                ask_price=ask_price,
                bid_price=bid_price,
                volume=volume,
                amount=amount
            )
            
        except Exception as e:
            print(f"Error extracting batch data at index {index}: {e}")
            return None


# 전역 인스턴스
_price_fetcher: Optional[SafePriceFetcher] = None


def get_price_fetcher(min_delay: float = 1.0, max_delay: float = 3.0) -> SafePriceFetcher:
    """전역 price fetcher 인스턴스 반환"""
    global _price_fetcher
    if _price_fetcher is None:
        _price_fetcher = SafePriceFetcher(min_delay, max_delay)
    return _price_fetcher


def fetch_single_price(code: str) -> Optional[PriceInfo]:
    """편의 함수: 단일 종목 시세 조회"""
    return get_price_fetcher().fetch_single_price(code)


def fetch_multiple_prices(codes: List[str], batch_size: int = 50) -> List[PriceInfo]:
    """편의 함수: 여러 종목 시세 일괄 조회"""
    return get_price_fetcher().fetch_multiple_prices_batch(codes, batch_size)

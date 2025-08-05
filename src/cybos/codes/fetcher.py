"""
Stock Code Fetcher - Cybos Plus 종목 정보 수집기

Cybos Plus API를 통해 종목 정보를 수집하고 StockInfo 객체로 변환합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import win32com.client
from typing import List, Optional, Dict, Any

from ...database.models.stock import StockInfo, MarketKind


class StockCodeFetcher:
    """Cybos Plus 종목 정보 수집 클래스"""
    
    def __init__(self):
        self._code_mgr = None
        self._stock_code = None
        self._initialize_com_objects()
    
    def _initialize_com_objects(self) -> None:
        """COM 객체 초기화"""
        try:
            self._code_mgr = win32com.client.Dispatch("CpUtil.CpCodeMgr")
            self._stock_code = win32com.client.Dispatch("CpUtil.CpStockCode")
        except Exception as e:
            raise ConnectionError(f"Failed to initialize COM objects: {e}")
    
    def get_market_stock_codes(self, market_kind: int) -> List[str]:
        """시장별 종목 코드 목록 조회"""
        try:
            codes = self._code_mgr.GetStockListByMarket(market_kind)
            return list(codes) if codes else []
        except Exception as e:
            print(f"Error getting stock codes for market {market_kind}: {e}")
            return []
    
    def get_all_stock_codes(self) -> Dict[str, List[str]]:
        """전체 시장 종목 코드 조회"""
        return {
            "kospi": self.get_market_stock_codes(MarketKind.KOSPI),
            "kosdaq": self.get_market_stock_codes(MarketKind.KOSDAQ),
            "freeboard": self.get_market_stock_codes(MarketKind.FREEBOARD),
            "krx": self.get_market_stock_codes(MarketKind.KRX)
        }
    
    def get_basic_stock_info(self, code: str) -> Optional[StockInfo]:
        """기본 종목 정보 조회"""
        try:
            # 기본 정보
            name = self._code_mgr.CodeToName(code)
            if not name:
                return None
            
            market_kind = self._code_mgr.GetStockMarketKind(code)
            section_kind = self._code_mgr.GetStockSectionKind(code)
            
            # StockInfo 객체 생성
            stock_info = StockInfo(
                code=code,
                name=name,
                market_kind=market_kind,
                section_kind=section_kind
            )
            
            return stock_info
            
        except Exception as e:
            print(f"Error getting basic info for {code}: {e}")
            return None
    
    def get_detailed_stock_info(self, code: str) -> Optional[StockInfo]:
        """상세 종목 정보 조회 (모든 필드 포함)"""
        try:
            # 기본 정보부터 가져오기
            stock_info = self.get_basic_stock_info(code)
            if not stock_info:
                return None
            
            # 상세 정보 추가
            self._add_control_info(stock_info, code)
            self._add_price_info(stock_info, code)
            self._add_company_info(stock_info, code)
            self._add_trading_info(stock_info, code)
            
            return stock_info
            
        except Exception as e:
            print(f"Error getting detailed info for {code}: {e}")
            return None
    
    def _add_control_info(self, stock_info: StockInfo, code: str) -> None:
        """관리/감리 정보 추가"""
        try:
            stock_info.control_kind = self._code_mgr.GetStockControlKind(code)
            stock_info.supervision_kind = self._code_mgr.GetStockSupervisionKind(code)
            stock_info.stock_status_kind = self._code_mgr.GetStockStatusKind(code)
            stock_info.lac_kind = self._code_mgr.GetStockLacKind(code)
        except Exception as e:
            print(f"Error getting control info for {code}: {e}")
    
    def _add_price_info(self, stock_info: StockInfo, code: str) -> None:
        """가격 정보 추가"""
        try:
            stock_info.std_price = self._code_mgr.GetStockStdPrice(code)
            stock_info.max_price = self._code_mgr.GetStockMaxPrice(code)
            stock_info.min_price = self._code_mgr.GetStockMinPrice(code)
            stock_info.par_price = self._code_mgr.GetStockParPrice(code)
            stock_info.yd_open_price = self._code_mgr.GetStockYdOpenPrice(code)
        except Exception as e:
            print(f"Error getting price info for {code}: {e}")
    
    def _add_company_info(self, stock_info: StockInfo, code: str) -> None:
        """기업 정보 추가"""
        try:
            stock_info.capital_size = self._code_mgr.GetStockCapital(code)
            stock_info.fiscal_month = self._code_mgr.GetStockFiscalMonth(code)
            stock_info.group_code = str(self._code_mgr.GetStockGroupCode(code))
            stock_info.industry_code = str(self._code_mgr.GetStockIndustryCode(code))
            stock_info.kospi200_kind = self._code_mgr.GetStockKospi200Kind(code)
            stock_info.listed_date = self._code_mgr.GetStockListedDate(code)
        except Exception as e:
            print(f"Error getting company info for {code}: {e}")
    
    def _add_trading_info(self, stock_info: StockInfo, code: str) -> None:
        """거래 정보 추가"""
        try:
            stock_info.margin_rate = self._code_mgr.GetStockMarginRate(code)
            stock_info.meme_min = self._code_mgr.GetStockMemeMin(code)
        except Exception as e:
            print(f"Error getting trading info for {code}: {e}")
    
    def fetch_all_stocks(self, detailed: bool = False) -> List[StockInfo]:
        """전체 종목 정보 수집"""
        all_stocks = []
        
        # 모든 시장의 종목 코드 가져오기
        market_codes = self.get_all_stock_codes()
        
        for market_name, codes in market_codes.items():
            print(f"Fetching {market_name} stocks: {len(codes)} codes")
            
            for i, code in enumerate(codes):
                if detailed:
                    stock_info = self.get_detailed_stock_info(code)
                else:
                    stock_info = self.get_basic_stock_info(code)
                
                if stock_info:
                    all_stocks.append(stock_info)
                
                # 진행상황 출력 (100개마다)
                if (i + 1) % 100 == 0:
                    print(f"  Processed {i + 1}/{len(codes)} {market_name} stocks")
        
        print(f"Total fetched stocks: {len(all_stocks)}")
        return all_stocks
    
    def fetch_market_stocks(self, market_kind: int, detailed: bool = False) -> List[StockInfo]:
        """특정 시장 종목 정보 수집"""
        codes = self.get_market_stock_codes(market_kind)
        stocks = []
        
        print(f"Fetching market {market_kind} stocks: {len(codes)} codes")
        
        for i, code in enumerate(codes):
            if detailed:
                stock_info = self.get_detailed_stock_info(code)
            else:
                stock_info = self.get_basic_stock_info(code)
            
            if stock_info:
                stocks.append(stock_info)
            
            # 진행상황 출력
            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{len(codes)} stocks")
        
        return stocks


# 전역 인스턴스
_fetcher: Optional[StockCodeFetcher] = None


def get_fetcher() -> StockCodeFetcher:
    """전역 fetcher 인스턴스 반환"""
    global _fetcher
    if _fetcher is None:
        _fetcher = StockCodeFetcher()
    return _fetcher


def fetch_all_stocks(detailed: bool = False) -> List[StockInfo]:
    """편의 함수: 전체 종목 정보 수집"""
    return get_fetcher().fetch_all_stocks(detailed)


def fetch_market_stocks(market_kind: int, detailed: bool = False) -> List[StockInfo]:
    """편의 함수: 특정 시장 종목 정보 수집"""
    return get_fetcher().fetch_market_stocks(market_kind, detailed)


def get_stock_counts() -> Dict[str, int]:
    """편의 함수: 시장별 종목 수 조회"""
    fetcher = get_fetcher()
    market_codes = fetcher.get_all_stock_codes()
    
    return {
        "kospi": len(market_codes["kospi"]),
        "kosdaq": len(market_codes["kosdaq"]),
        "freeboard": len(market_codes["freeboard"]),
        "krx": len(market_codes["krx"]),
        "total": sum(len(codes) for codes in market_codes.values())
    }

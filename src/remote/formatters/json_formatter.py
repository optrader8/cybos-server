"""
JSON Formatter - JSON 데이터 포맷터

데이터를 JSON 형식으로 변환합니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import json
from typing import Dict, Any, List
from datetime import datetime
from ...database.models.price import PriceInfo
from ...database.models.stock import StockInfo


class JSONFormatter:
    """JSON 데이터 포맷터"""

    @staticmethod
    def format_price(price: PriceInfo) -> Dict[str, Any]:
        """
        PriceInfo를 JSON 형식으로 변환

        Args:
            price: 시세 정보

        Returns:
            JSON 직렬화 가능한 딕셔너리
        """
        return {
            "code": price.code,
            "name": price.name,
            "time": price.time,
            "current_price": price.current_price,
            "change": price.change,
            "status": price.status,
            "open_price": price.open_price,
            "high_price": price.high_price,
            "low_price": price.low_price,
            "prev_close": price.prev_close,
            "ask_price": price.ask_price,
            "bid_price": price.bid_price,
            "volume": price.volume,
            "amount": price.amount,
            "created_at": price.created_at,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def format_prices(prices: List[PriceInfo]) -> List[Dict[str, Any]]:
        """
        여러 PriceInfo를 JSON 형식으로 변환

        Args:
            prices: 시세 정보 리스트

        Returns:
            JSON 직렬화 가능한 딕셔너리 리스트
        """
        return [JSONFormatter.format_price(price) for price in prices]

    @staticmethod
    def format_stock(stock: StockInfo) -> Dict[str, Any]:
        """
        StockInfo를 JSON 형식으로 변환

        Args:
            stock: 주식 정보

        Returns:
            JSON 직렬화 가능한 딕셔너리
        """
        return {
            "code": stock.code,
            "name": stock.name,
            "market_kind": stock.market_kind,
            "control_kind": stock.control_kind,
            "supervise_kind": stock.supervise_kind,
            "stock_kind": stock.stock_kind,
            "listing_date": stock.listing_date,
            "capital": stock.capital,
            "credit_able": stock.credit_able,
            "created_at": stock.created_at,
            "updated_at": stock.updated_at,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def format_stocks(stocks: List[StockInfo]) -> List[Dict[str, Any]]:
        """
        여러 StockInfo를 JSON 형식으로 변환

        Args:
            stocks: 주식 정보 리스트

        Returns:
            JSON 직렬화 가능한 딕셔너리 리스트
        """
        return [JSONFormatter.format_stock(stock) for stock in stocks]

    @staticmethod
    def to_json_string(data: Any, indent: int = None) -> str:
        """
        데이터를 JSON 문자열로 변환

        Args:
            data: 변환할 데이터
            indent: 들여쓰기 수준

        Returns:
            JSON 문자열
        """
        return json.dumps(data, ensure_ascii=False, indent=indent)

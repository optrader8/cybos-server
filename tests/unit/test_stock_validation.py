"""
Stock Database Validation Tests - 종목 정보 DB 검증 테스트

저장된 종목 정보의 무결성과 정확성을 검증하는 테스트입니다.
"""

import pytest
import sqlite3
from pathlib import Path
import sys

# 프로젝트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_connection_context, get_db_info
from src.database.models.stock import StockTable, StockInfo, MarketKind


class TestStockDatabase:
    """종목 데이터베이스 검증 테스트 클래스"""
    
    @pytest.fixture
    def db_path(self):
        """테스트용 DB 경로"""
        return "data/cybos.db"
    
    def test_database_exists(self, db_path):
        """데이터베이스 파일 존재 확인"""
        db_file = Path(db_path)
        assert db_file.exists(), f"Database file not found: {db_path}"
        assert db_file.stat().st_size > 0, "Database file is empty"
    
    def test_stock_table_exists(self, db_path):
        """stocks 테이블 존재 확인"""
        with get_connection_context(db_path) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='stocks'
            """)
            result = cursor.fetchone()
            assert result is not None, "stocks table does not exist"
    
    def test_stock_table_structure(self, db_path):
        """stocks 테이블 구조 확인"""
        with get_connection_context(db_path) as conn:
            cursor = conn.execute("PRAGMA table_info(stocks)")
            columns = cursor.fetchall()
            
            expected_columns = {
                'code', 'name', 'market_kind', 'section_kind',
                'control_kind', 'supervision_kind', 'stock_status_kind',
                'std_price', 'max_price', 'min_price', 'par_price', 'yd_open_price',
                'capital_size', 'fiscal_month', 'group_code', 'industry_code',
                'kospi200_kind', 'margin_rate', 'meme_min', 'lac_kind',
                'listed_date', 'created_at', 'updated_at'
            }
            
            actual_columns = {col[1] for col in columns}
            
            missing_columns = expected_columns - actual_columns
            assert not missing_columns, f"Missing columns: {missing_columns}"
            
            extra_columns = actual_columns - expected_columns
            assert not extra_columns, f"Unexpected columns: {extra_columns}"
    
    def test_stock_data_exists(self, db_path):
        """종목 데이터 존재 확인"""
        with get_connection_context(db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM stocks")
            count = cursor.fetchone()[0]
            assert count > 0, "No stock data found in database"
            print(f"Total stocks in database: {count}")
    
    def test_market_distribution(self, db_path):
        """시장별 종목 분포 확인"""
        with get_connection_context(db_path) as conn:
            count_info = StockTable.count_stocks(conn)
            
            assert count_info["total"] > 0, "No stocks found"
            
            # KOSPI 종목이 있는지 확인
            if "kospi" in count_info:
                assert count_info["kospi"] > 0, "No KOSPI stocks found"
                print(f"KOSPI stocks: {count_info['kospi']}")
            
            # KOSDAQ 종목이 있는지 확인 (있다면)
            if "kosdaq" in count_info:
                print(f"KOSDAQ stocks: {count_info['kosdaq']}")
            
            print(f"Total stocks: {count_info['total']}")
    
    def test_stock_code_format(self, db_path):
        """종목 코드 형식 검증"""
        with get_connection_context(db_path) as conn:
            cursor = conn.execute("SELECT code FROM stocks LIMIT 100")
            codes = [row[0] for row in cursor.fetchall()]
            
            for code in codes:
                # 종목 코드 기본 검증
                assert isinstance(code, str), f"Code should be string: {code}"
                assert len(code) >= 6, f"Code too short: {code}"
                assert len(code) <= 10, f"Code too long: {code}"  # 유연하게 설정
                assert code.strip() == code, f"Code has leading/trailing spaces: '{code}'"
                assert code != "", f"Empty code found"
                
                # 샘플 출력 (처음 5개만)
                if codes.index(code) < 5:
                    print(f"    Sample code: {code}")
    
    def test_stock_name_not_empty(self, db_path):
        """종목명이 비어있지 않은지 확인"""
        with get_connection_context(db_path) as conn:
            cursor = conn.execute("SELECT code, name FROM stocks WHERE name IS NULL OR name = ''")
            empty_names = cursor.fetchall()
            
            assert not empty_names, f"Found stocks with empty names: {empty_names}"
    
    def test_market_kind_valid(self, db_path):
        """시장 구분 값이 유효한지 확인"""
        valid_markets = {kind.value for kind in MarketKind}
        
        with get_connection_context(db_path) as conn:
            cursor = conn.execute("SELECT DISTINCT market_kind FROM stocks")
            market_kinds = [row[0] for row in cursor.fetchall()]
            
            for market_kind in market_kinds:
                assert market_kind in valid_markets, f"Invalid market_kind: {market_kind}"
    
    def test_price_data_consistency(self, db_path):
        """가격 데이터 일관성 확인"""
        with get_connection_context(db_path) as conn:
            cursor = conn.execute("""
                SELECT code, name, std_price, max_price, min_price 
                FROM stocks 
                WHERE std_price > 0 AND max_price > 0 AND min_price > 0
                LIMIT 10
            """)
            
            price_data = cursor.fetchall()
            
            for code, name, std_price, max_price, min_price in price_data:
                # 상한가 >= 기준가 >= 하한가
                assert max_price >= std_price >= min_price, \
                    f"Price inconsistency for {code}({name}): max={max_price}, std={std_price}, min={min_price}"
    
    def test_timestamp_fields(self, db_path):
        """타임스탬프 필드 확인"""
        with get_connection_context(db_path) as conn:
            cursor = conn.execute("""
                SELECT code, created_at, updated_at 
                FROM stocks 
                WHERE created_at IS NOT NULL AND updated_at IS NOT NULL
                LIMIT 5
            """)
            
            timestamp_data = cursor.fetchall()
            
            assert len(timestamp_data) > 0, "No records with timestamps found"
            
            for code, created_at, updated_at in timestamp_data:
                assert created_at is not None, f"created_at is null for {code}"
                assert updated_at is not None, f"updated_at is null for {code}"
                # ISO 형식인지 간단히 확인
                assert "T" in created_at, f"Invalid created_at format for {code}: {created_at}"
                assert "T" in updated_at, f"Invalid updated_at format for {code}: {updated_at}"
    
    def test_sample_major_stocks(self, db_path):
        """주요 종목들이 제대로 저장되었는지 확인"""
        major_stocks = {
            "005930": "삼성전자",
            "000660": "SK하이닉스", 
            "035420": "NAVER",
            "051910": "LG화학",
            "005380": "현대차"
        }
        
        with get_connection_context(db_path) as conn:
            for code, expected_name in major_stocks.items():
                stock = StockTable.get_stock(conn, code)
                if stock:  # 종목이 있다면 검증
                    assert stock.name == expected_name, \
                        f"Name mismatch for {code}: expected={expected_name}, actual={stock.name}"
                    assert stock.market_kind == MarketKind.KOSPI, \
                        f"Market mismatch for {code}: expected=KOSPI, actual={stock.market_kind}"
                    print(f"✅ {code}: {stock.name} verified")
                else:
                    print(f"⚠️  {code}: {expected_name} not found in database")
    
    def test_database_integrity(self, db_path):
        """데이터베이스 무결성 검사"""
        with get_connection_context(db_path) as conn:
            # SQLite 무결성 체크
            cursor = conn.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            assert result == "ok", f"Database integrity check failed: {result}"
            
            # 중복 키 확인
            cursor = conn.execute("""
                SELECT code, COUNT(*) as cnt 
                FROM stocks 
                GROUP BY code 
                HAVING cnt > 1
            """)
            duplicates = cursor.fetchall()
            assert not duplicates, f"Found duplicate codes: {duplicates}"
    
    def test_index_exists(self, db_path):
        """인덱스 존재 확인"""
        expected_indexes = [
            "idx_stocks_market",
            "idx_stocks_section", 
            "idx_stocks_name",
            "idx_stocks_status"
        ]
        
        with get_connection_context(db_path) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            
            for expected_index in expected_indexes:
                assert expected_index in indexes, f"Index not found: {expected_index}"


class TestStockInfoModel:
    """StockInfo 모델 테스트"""
    
    def test_stock_info_creation(self):
        """StockInfo 객체 생성 테스트"""
        stock = StockInfo(
            code="005930",
            name="삼성전자", 
            market_kind=MarketKind.KOSPI,
            section_kind=1
        )
        
        assert stock.code == "005930"
        assert stock.name == "삼성전자"
        assert stock.market_kind == MarketKind.KOSPI
        assert stock.section_kind == 1
    
    def test_stock_info_to_dict(self):
        """StockInfo to_dict 메서드 테스트"""
        stock = StockInfo(
            code="005930",
            name="삼성전자",
            market_kind=MarketKind.KOSPI,
            section_kind=1,
            std_price=70000
        )
        
        stock_dict = stock.to_dict()
        
        assert isinstance(stock_dict, dict)
        assert stock_dict["code"] == "005930"
        assert stock_dict["name"] == "삼성전자"
        assert stock_dict["std_price"] == 70000
    
    def test_stock_info_from_dict(self):
        """StockInfo from_dict 메서드 테스트"""
        data = {
            "code": "005930",
            "name": "삼성전자",
            "market_kind": 1,
            "section_kind": 1,
            "std_price": 70000
        }
        
        stock = StockInfo.from_dict(data)
        
        assert stock.code == "005930"
        assert stock.name == "삼성전자"
        assert stock.market_kind == 1
        assert stock.std_price == 70000


if __name__ == "__main__":
    # 직접 실행 시 간단한 테스트 실행
    import unittest
    
    # 기본 검증만 실행
    db_path = "data/cybos.db"
    
    print("🔍 종목 데이터베이스 검증 시작...")
    
    # 데이터베이스 존재 확인
    db_file = Path(db_path)
    if not db_file.exists():
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        sys.exit(1)
    
    print(f"✅ 데이터베이스 파일 존재: {db_path}")
    
    # 기본 정보 출력
    db_info = get_db_info(db_path)
    print(f"📊 데이터베이스 정보:")
    for key, value in db_info.items():
        print(f"  {key}: {value}")
    
    # 간단한 검증
    with get_connection_context(db_path) as conn:
        # 종목 수 확인
        count_info = StockTable.count_stocks(conn)
        print(f"\n📈 시장별 종목 수:")
        for market, count in count_info.items():
            print(f"  {market}: {count:,}")
        
        # 샘플 종목 확인
        cursor = conn.execute("SELECT code, name, market_kind FROM stocks LIMIT 5")
        print(f"\n📋 샘플 종목:")
        for code, name, market_kind in cursor.fetchall():
            market_name = "KOSPI" if market_kind == 1 else "KOSDAQ" if market_kind == 2 else f"Market_{market_kind}"
            print(f"  {code}: {name} ({market_name})")
    
    print("\n✅ 기본 검증 완료!")
    print("\n전체 테스트 실행 방법:")
    print("  pytest tests/unit/test_stock_validation.py -v")

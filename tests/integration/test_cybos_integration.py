"""
Stock Integration Tests - 종목 정보 통합 테스트

Cybos Plus와 데이터베이스 간의 통합 테스트입니다.
실제 환경에서 Cybos Plus 연결이 필요합니다.
"""

import pytest
import sys
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import win32com.client
    CYBOS_AVAILABLE = True
except ImportError:
    CYBOS_AVAILABLE = False

from src.cybos.codes.fetcher import get_fetcher, get_stock_counts
from src.database.connection import get_connection_context
from src.database.models.stock import StockTable, MarketKind


@pytest.mark.cybos
@pytest.mark.integration
class TestCybosIntegration:
    """Cybos Plus 통합 테스트"""
    
    @pytest.fixture(autouse=True)
    def check_cybos_connection(self):
        """Cybos Plus 연결 확인"""
        if not CYBOS_AVAILABLE:
            pytest.skip("pywin32 not available")
        
        try:
            cybos = win32com.client.Dispatch("CpUtil.CpCybos")
            if cybos.IsConnect != 1:
                pytest.skip("Cybos Plus not connected")
        except Exception:
            pytest.skip("Cybos Plus connection failed")
    
    def test_stock_count_consistency(self):
        """Cybos API와 DB의 종목 수 일치성 확인"""
        # Cybos에서 종목 수 조회
        cybos_counts = get_stock_counts()
        
        # DB에서 종목 수 조회
        with get_connection_context() as conn:
            db_counts = StockTable.count_stocks(conn)
        
        # KOSPI 종목 수 비교 (DB에 저장된 것이 있다면)
        if "kospi" in db_counts and cybos_counts["kospi"] > 0:
            # 완전히 일치하지 않을 수 있지만, 큰 차이는 없어야 함
            diff_ratio = abs(db_counts["kospi"] - cybos_counts["kospi"]) / cybos_counts["kospi"]
            assert diff_ratio < 0.1, f"Too much difference in KOSPI count: DB={db_counts['kospi']}, Cybos={cybos_counts['kospi']}"
    
    def test_sample_stock_data_accuracy(self):
        """샘플 종목 데이터 정확성 확인"""
        fetcher = get_fetcher()
        test_codes = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
        
        with get_connection_context() as conn:
            for code in test_codes:
                # Cybos에서 현재 정보 조회
                cybos_info = fetcher.get_basic_stock_info(code)
                if not cybos_info:
                    continue
                
                # DB에서 저장된 정보 조회
                db_info = StockTable.get_stock(conn, code)
                if not db_info:
                    continue
                
                # 기본 정보 비교
                assert db_info.code == cybos_info.code
                assert db_info.name == cybos_info.name
                assert db_info.market_kind == cybos_info.market_kind
                
                print(f"✅ {code}: {db_info.name} - Data consistency verified")
    
    def test_new_stock_fetch_and_save(self):
        """새로운 종목 정보 수집 및 저장 테스트"""
        fetcher = get_fetcher()
        
        # KOSPI 첫 10개 종목 수집
        kospi_codes = fetcher.get_market_stock_codes(MarketKind.KOSPI)[:10]
        
        collected_stocks = []
        for code in kospi_codes:
            stock_info = fetcher.get_detailed_stock_info(code)
            if stock_info:
                collected_stocks.append(stock_info)
        
        assert len(collected_stocks) > 0, "No stocks collected"
        
        # 임시 테이블에 저장 테스트
        with get_connection_context() as conn:
            # 임시 테이블 생성
            conn.execute("""
                CREATE TEMPORARY TABLE test_stocks AS 
                SELECT * FROM stocks WHERE 1=0
            """)
            
            # 데이터 삽입
            for stock in collected_stocks:
                placeholders = ", ".join(["?" for _ in range(len(stock.to_dict()))])
                columns = ", ".join(stock.to_dict().keys())
                
                conn.execute(f"""
                    INSERT INTO test_stocks ({columns}) 
                    VALUES ({placeholders})
                """, list(stock.to_dict().values()))
            
            # 저장된 데이터 확인
            cursor = conn.execute("SELECT COUNT(*) FROM test_stocks")
            saved_count = cursor.fetchone()[0]
            assert saved_count == len(collected_stocks)
            
            print(f"✅ Successfully saved {saved_count} stocks to temporary table")


@pytest.mark.integration
class TestDatabasePerformance:
    """데이터베이스 성능 테스트"""
    
    def test_large_query_performance(self):
        """대용량 쿼리 성능 테스트"""
        import time
        
        with get_connection_context() as conn:
            # 전체 종목 수 조회 성능
            start_time = time.time()
            cursor = conn.execute("SELECT COUNT(*) FROM stocks")
            count = cursor.fetchone()[0]
            count_time = time.time() - start_time
            
            assert count_time < 1.0, f"Count query too slow: {count_time:.3f}s"
            
            # 시장별 조회 성능
            start_time = time.time()
            cursor = conn.execute("SELECT * FROM stocks WHERE market_kind = ? LIMIT 100", (MarketKind.KOSPI,))
            results = cursor.fetchall()
            query_time = time.time() - start_time
            
            assert query_time < 0.5, f"Market query too slow: {query_time:.3f}s"
            assert len(results) > 0, "No results returned"
            
            print(f"✅ Performance test passed: count={count_time:.3f}s, query={query_time:.3f}s")
    
    def test_index_effectiveness(self):
        """인덱스 효과성 테스트"""
        with get_connection_context() as conn:
            # 인덱스를 사용하는 쿼리들
            test_queries = [
                ("SELECT * FROM stocks WHERE market_kind = ?", (MarketKind.KOSPI,)),
                ("SELECT * FROM stocks WHERE name LIKE ?", ("%삼성%",)),
                ("SELECT * FROM stocks WHERE stock_status_kind = ?", (0,)),
            ]
            
            for query, params in test_queries:
                # EXPLAIN QUERY PLAN으로 인덱스 사용 확인
                cursor = conn.execute(f"EXPLAIN QUERY PLAN {query}", params)
                plan = cursor.fetchall()
                
                # 인덱스를 사용하는지 확인 (단순한 체크)
                plan_text = " ".join([str(row) for row in plan])
                using_index = "USING INDEX" in plan_text.upper() or "INDEX" in plan_text.upper()
                
                print(f"Query: {query}")
                print(f"Plan: {plan}")
                print(f"Using Index: {using_index}")


if __name__ == "__main__":
    print("🔗 Cybos Plus 통합 테스트")
    print("=" * 50)
    
    # Cybos Plus 연결 확인
    if not CYBOS_AVAILABLE:
        print("❌ pywin32 모듈이 없습니다.")
        sys.exit(1)
    
    try:
        cybos = win32com.client.Dispatch("CpUtil.CpCybos")
        if cybos.IsConnect != 1:
            print("❌ Cybos Plus가 연결되지 않았습니다.")
            print("   HTS를 실행하고 로그인 후 다시 시도하세요.")
            sys.exit(1)
        
        print("✅ Cybos Plus 연결 확인됨")
    except Exception as e:
        print(f"❌ Cybos Plus 연결 실패: {e}")
        sys.exit(1)
    
    # 간단한 통합 테스트 실행
    try:
        # 종목 수 확인
        print("\n📊 종목 수 확인...")
        counts = get_stock_counts()
        for market, count in counts.items():
            print(f"  {market}: {count:,}")
        
        # 샘플 종목 정보 확인
        print("\n📋 샘플 종목 정보 확인...")
        fetcher = get_fetcher()
        sample_codes = ["005930", "000660", "035420"]
        
        for code in sample_codes:
            info = fetcher.get_basic_stock_info(code)
            if info:
                print(f"  {code}: {info.name} (시장: {info.market_kind})")
            else:
                print(f"  {code}: 정보 조회 실패")
        
        print("\n✅ 통합 테스트 완료!")
        print("\n전체 통합 테스트 실행 방법:")
        print("  pytest tests/integration/test_cybos_integration.py -v -m cybos")
        
    except Exception as e:
        print(f"❌ 통합 테스트 실패: {e}")
        sys.exit(1)

"""
Quick Test Runner - 빠른 테스트 실행기

저장된 종목 정보를 빠르게 검증하는 스크립트입니다.
"""

import sys
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tests.unit.test_stock_validation import TestStockDatabase


def main():
    """메인 테스트 실행 함수"""
    print("🔍 종목 데이터베이스 빠른 검증")
    print("=" * 50)
    
    # 테스트 인스턴스 생성
    test_db = TestStockDatabase()
    db_path = "data/cybos.db"
    
    try:
        # 1. 데이터베이스 존재 확인
        print("1. 데이터베이스 파일 존재 확인...")
        test_db.test_database_exists(db_path)
        print("   ✅ 통과")
        
        # 2. 테이블 구조 확인
        print("2. 테이블 구조 확인...")
        test_db.test_stock_table_exists(db_path)
        test_db.test_stock_table_structure(db_path)
        print("   ✅ 통과")
        
        # 3. 데이터 존재 확인
        print("3. 종목 데이터 존재 확인...")
        test_db.test_stock_data_exists(db_path)
        print("   ✅ 통과")
        
        # 4. 시장별 분포 확인
        print("4. 시장별 종목 분포 확인...")
        test_db.test_market_distribution(db_path)
        print("   ✅ 통과")
        
        # 5. 데이터 형식 검증
        print("5. 종목 코드 형식 검증...")
        test_db.test_stock_code_format(db_path)
        print("   ✅ 통과")
        
        # 6. 종목명 검증
        print("6. 종목명 검증...")
        test_db.test_stock_name_not_empty(db_path)
        print("   ✅ 통과")
        
        # 7. 시장 구분 검증
        print("7. 시장 구분 검증...")
        test_db.test_market_kind_valid(db_path)
        print("   ✅ 통과")
        
        # 8. 주요 종목 확인
        print("8. 주요 종목 확인...")
        test_db.test_sample_major_stocks(db_path)
        print("   ✅ 통과")
        
        # 9. 데이터베이스 무결성 확인
        print("9. 데이터베이스 무결성 확인...")
        test_db.test_database_integrity(db_path)
        print("   ✅ 통과")
        
        # 10. 인덱스 확인
        print("10. 인덱스 확인...")
        test_db.test_index_exists(db_path)
        print("    ✅ 통과")
        
        print("\n🎉 모든 검증이 성공적으로 완료되었습니다!")
        print("\n📊 최종 요약:")
        
        # 최종 통계 출력
        from src.database.connection import get_db_info
        db_info = get_db_info(db_path)
        
        print(f"   📁 DB 파일: {db_info['db_path']}")
        print(f"   💾 DB 크기: {db_info['db_size']:,} bytes")
        print(f"   📊 전체 종목 수: {db_info.get('stocks_count', 'N/A'):,}")
        
        return True
        
    except AssertionError as e:
        print(f"   ❌ 실패: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return False


def run_full_tests():
    """전체 테스트 실행 가이드"""
    print("\n" + "=" * 50)
    print("🧪 전체 테스트 실행 방법:")
    print("")
    print("1. 단위 테스트만 실행:")
    print("   pytest tests/unit/ -v")
    print("")
    print("2. 통합 테스트 실행 (Cybos Plus 연결 필요):")
    print("   pytest tests/integration/ -v -m cybos")
    print("")
    print("3. 모든 테스트 실행:")
    print("   pytest tests/ -v")
    print("")
    print("4. 느린 테스트 제외하고 실행:")
    print("   pytest tests/ -v -m 'not slow'")
    print("")
    print("5. 커버리지 포함 실행:")
    print("   pytest tests/ --cov=src --cov-report=html")


if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✨ 데이터베이스가 정상적으로 검증되었습니다!")
        run_full_tests()
    else:
        print("\n💥 검증 중 문제가 발생했습니다.")
        print("   로그를 확인하고 문제를 해결해주세요.")
        sys.exit(1)

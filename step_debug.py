"""
Step by Step Debug - 단계별 디버깅

우리 코드와 간단한 테스트 코드의 차이점을 찾아봅시다.
"""

import sys
from pathlib import Path
import win32com.client

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_simple_direct():
    """가장 간단한 직접 호출"""
    print("=== 1. 간단한 직접 호출 ===")
    try:
        inStockMst = win32com.client.Dispatch("dscbo1.StockMst")
        inStockMst.SetInputValue(0, "A000660")
        inStockMst.BlockRequest()
        current = inStockMst.GetHeaderValue(11)
        name = inStockMst.GetHeaderValue(1)
        print(f"✅ A000660 ({name}): {current:,}원")
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False


def test_without_a_prefix():
    """A 접두사 없이 테스트"""
    print("\n=== 2. A 접두사 없이 테스트 ===")
    try:
        inStockMst = win32com.client.Dispatch("dscbo1.StockMst")
        inStockMst.SetInputValue(0, "000660")  # A 제거
        inStockMst.BlockRequest()
        current = inStockMst.GetHeaderValue(11)
        name = inStockMst.GetHeaderValue(1)
        print(f"✅ 000660 ({name}): {current:,}원")
        return True
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False


def test_our_fetcher():
    """우리 fetcher 테스트"""
    print("\n=== 3. 우리 SafePriceFetcher 테스트 ===")
    try:
        from src.cybos.price.fetcher import get_price_fetcher
        
        fetcher = get_price_fetcher()
        
        if not fetcher.check_connection():
            print("❌ 연결 실패")
            return False
        
        print("✅ 연결 확인됨")
        
        # 단일 조회 테스트
        price_info = fetcher.fetch_single_price("000660")
        
        if price_info:
            print(f"✅ 000660 ({price_info.name}): {price_info.current_price:,}원")
            print(f"   전일대비: {price_info.change:+,}원")
            print(f"   거래량: {price_info.volume:,}주")
            return True
        else:
            print("❌ 데이터 조회 실패")
            return False
            
    except Exception as e:
        print(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_detailed_extraction():
    """상세한 데이터 추출 테스트"""
    print("\n=== 4. 상세한 데이터 추출 테스트 ===")
    try:
        inStockMst = win32com.client.Dispatch("dscbo1.StockMst")
        inStockMst.SetInputValue(0, "000660")
        result = inStockMst.BlockRequest()
        
        print(f"BlockRequest 결과: {result}")
        
        if result != 0:
            print(f"❌ 요청 실패 (코드: {result})")
            return False
        
        # 모든 필드 확인
        fields = {
            0: "종목코드",
            1: "종목명", 
            4: "시간",
            10: "전일종가",
            11: "현재가",
            12: "전일대비",
            13: "시가",
            14: "고가", 
            15: "저가",
            16: "매도호가",
            17: "매수호가",
            18: "누적거래량"
        }
        
        data = {}
        for field_id, field_name in fields.items():
            try:
                value = inStockMst.GetHeaderValue(field_id)
                data[field_id] = value
                print(f"   {field_name} ({field_id}): {value}")
            except Exception as e:
                print(f"   {field_name} ({field_id}): 오류 - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 실패: {e}")
        return False


def main():
    """메인 테스트"""
    print("🔍 단계별 디버깅 테스트")
    print("=" * 50)
    
    # 1단계: 가장 간단한 테스트
    if not test_simple_direct():
        print("❌ 1단계 실패 - 기본 COM 객체 문제")
        return
    
    # 2단계: A 접두사 없이
    test_without_a_prefix()
    
    # 3단계: 우리 fetcher
    test_our_fetcher()
    
    # 4단계: 상세 분석
    test_detailed_extraction()
    
    print("\n✅ 모든 테스트 완료!")


if __name__ == "__main__":
    main()

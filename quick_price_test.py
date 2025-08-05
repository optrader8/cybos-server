"""
Quick Price Test - 수정된 fetcher 테스트
"""

import sys
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cybos.price.fetcher import get_price_fetcher

def test_fetcher():
    """수정된 fetcher 테스트"""
    print("🧪 수정된 Price Fetcher 테스트")
    print("=" * 40)
    
    fetcher = get_price_fetcher()
    test_codes = ["000660", "005930", "035420"]  # A 접두사 없이
    
    for code in test_codes:
        print(f"\n📊 {code} 조회 중...")
        try:
            price_info = fetcher.fetch_single_price(code)
            if price_info:
                print(f"✅ {code} ({price_info.name})")
                print(f"   현재가: {price_info.current_price:,}원")
                print(f"   전일대비: {price_info.change:+,}원")
                print(f"   상태: {price_info.get_status_name()}")
                print(f"   거래량: {price_info.volume:,}주")
            else:
                print(f"❌ {code}: 데이터 없음")
        except Exception as e:
            print(f"❌ {code}: 오류 - {e}")

if __name__ == "__main__":
    test_fetcher()

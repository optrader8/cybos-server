"""
Debug Price Test - 상세한 가격 조회 디버깅

StockMst API를 직접 사용하여 가격 조회 문제를 분석합니다.
"""

import sys
from pathlib import Path
import win32com.client
from datetime import datetime

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_cybos_status():
    """Cybos Plus 상태 상세 확인"""
    print("=== Cybos Plus 상태 확인 ===")
    
    try:
        cybos = win32com.client.Dispatch("CpUtil.CpCybos")
        
        print(f"연결 상태: {cybos.IsConnect}")
        print(f"서버 유형: {cybos.ServerType}")
        
        # GetLoginInfo는 안전하게 호출
        try:
            user_id = cybos.GetLoginInfo(0)
            user_name = cybos.GetLoginInfo(1)
            account_count = cybos.GetLoginInfo(7)
            print(f"사용자 ID: {user_id}")
            print(f"사용자 이름: {user_name}")
            print(f"계좌 개수: {account_count}")
        except Exception as login_error:
            print(f"로그인 정보 조회 실패: {login_error}")
        
        # 요청 제한 정보
        try:
            remain_count = cybos.GetLimitRemainCount(1)  # 1: 비실시간 요청
            remain_time = cybos.LimitRequestRemainTime
            print(f"남은 요청 수: {remain_count}")
            print(f"재설정까지 시간: {remain_time/1000:.1f}초")
        except Exception as limit_error:
            print(f"요청 제한 정보 조회 실패: {limit_error}")
        
        return cybos.IsConnect == 1
        
    except Exception as e:
        print(f"전체 오류: {e}")
        return False


def test_direct_stockmst(code):
    """StockMst를 직접 사용하여 데이터 조회"""
    print(f"\n=== {code} 직접 조회 테스트 ===")
    
    try:
        # StockMst 객체 생성
        stock_mst = win32com.client.Dispatch("dscbo1.StockMst")
        
        # 종목 코드 설정 (A 접두사 제거)
        clean_code = code.replace("A", "") if code.startswith("A") else code
        print(f"조회 종목 코드: {clean_code}")
        
        stock_mst.SetInputValue(0, clean_code)
        
        # 데이터 요청
        print("데이터 요청 중...")
        result = stock_mst.BlockRequest()
        print(f"요청 결과: {result}")
        
        if result != 0:
            print(f"❌ 요청 실패 (코드: {result})")
            return None
        
        # 모든 주요 데이터 출력
        data = {}
        field_names = {
            0: "종목코드",
            1: "종목명", 
            4: "시간",
            10: "전일종가",
            11: "현재가",
            12: "전일대비",
            13: "시가",
            14: "고가", 
            15: "저가",
            18: "누적거래량",
            19: "누적거래대금",
            44: "거래상태",
            45: "소속구분",
            59: "장구분"
        }
        
        print("\n📊 조회된 데이터:")
        for field_id, field_name in field_names.items():
            try:
                value = stock_mst.GetHeaderValue(field_id)
                data[field_id] = value
                print(f"   {field_name} ({field_id}): {value}")
            except Exception as e:
                print(f"   {field_name} ({field_id}): 조회실패 - {e}")
        
        return data
        
    except Exception as e:
        print(f"❌ 직접 조회 실패: {e}")
        return None


def test_market_time():
    """현재 시간과 장 운영 시간 확인"""
    print("\n=== 시간 정보 확인 ===")
    
    now = datetime.now()
    print(f"현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"요일: {['월','화','수','목','금','토','일'][now.weekday()]}")
    
    # 장 운영 시간 확인
    weekday = now.weekday()  # 0=월요일, 6=일요일
    current_time = now.time()
    
    if weekday >= 5:  # 토요일(5) 또는 일요일(6)
        print("📅 주말 - 장 운영하지 않음")
        return False
    
    from datetime import time
    market_open = time(9, 0)  # 09:00
    market_close = time(15, 30)  # 15:30
    
    if market_open <= current_time <= market_close:
        print("🕐 장 중 시간")
        return True
    else:
        print("🕐 장 외 시간 (전일 종가 또는 예상 체결가)")
        return False


def main():
    """메인 테스트 함수"""
    print("🔍 가격 조회 문제 디버깅")
    print("=" * 50)
    
    # 1. Cybos 상태 확인
    if not check_cybos_status():
        print("❌ Cybos Plus 연결 문제")
        return
    
    # 2. 시간 정보 확인
    is_market_time = test_market_time()
    
    # 3. 직접 API 테스트
    test_codes = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
    
    for code in test_codes:
        data = test_direct_stockmst(code)
        if data:
            current_price = data.get(11, 0)
            prev_close = data.get(10, 0) 
            name = data.get(1, "")
            
            if current_price == 0 and prev_close > 0:
                print(f"💡 {code} ({name}): 현재가는 0이지만 전일종가 {prev_close:,}원 존재")
                if not is_market_time:
                    print("   → 장 외 시간이므로 전일종가 사용 가능")
            elif current_price > 0:
                print(f"✅ {code} ({name}): 정상 가격 {current_price:,}원")
            else:
                print(f"❓ {code} ({name}): 가격 정보 없음")
    
    print("\n💡 해결 방안:")
    if not is_market_time:
        print("1. 장 외 시간에는 전일종가(field 10) 사용")
        print("2. 예상체결가(field 55) 확인")
    print("3. 종목 코드에서 'A' 접두사 제거 확인")
    print("4. 데이터베이스 모델의 매개변수 오류 수정 필요")


if __name__ == "__main__":
    main()

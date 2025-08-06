"""
StockMst 53번 필드(KOSPI200 채용 여부) 직접 조회
데이터베이스의 kospi200_kind가 정확하지 않을 수 있으므로 
실시간으로 Cybos Plus API에서 직접 조회해서 확인
"""

import win32com.client
import time
import random

def check_kospi200_via_api():
    """StockMst API로 직접 KOSPI200 정보 확인"""
    
    print("🔍 StockMst API로 KOSPI200 정보 직접 조회")
    print("=" * 60)
    
    try:
        # COM 객체 생성
        stockMst = win32com.client.Dispatch("DsCbo1.StockMst")
        print("✅ StockMst COM 객체 생성 성공")
        
        # 테스트할 주요 종목들
        test_stocks = [
            ('005930', '삼성전자'),
            ('000660', 'SK하이닉스'),
            ('035420', 'NAVER'),
            ('207940', '삼성바이오로직스'),
            ('005380', '현대차'),
            ('006400', '삼성SDI'),
            ('051910', 'LG화학'),
            ('003550', 'LG'),
            ('000270', '기아'),
            ('068270', '셀트리온'),
            ('012330', '현대모비스'),
            ('066570', 'LG전자'),
            ('096770', 'SK이노베이션'),
            ('028260', '삼성물산'),
            ('323410', '카카오뱅크'),
            ('000100', '유한양행'),  # 일반 종목 (KOSPI200 아닐 것)
            ('000050', '경방'),     # 일반 종목 (KOSPI200 아닐 것)
        ]
        
        print(f"\n📊 주요 종목들의 KOSPI200 채용 여부 (필드 53번):")
        
        kospi200_stocks = []
        non_kospi200_stocks = []
        
        for code, name in test_stocks:
            try:
                # A 접두사 추가
                full_code = f"A{code}"
                
                # 데이터 요청 설정
                stockMst.SetInputValue(0, full_code)
                
                # 데이터 요청
                result = stockMst.BlockRequest()
                
                if result == 0:  # 성공
                    # 53번 필드: KOSPI200 채용 여부
                    kospi200_info = stockMst.GetHeaderValue(53)
                    
                    print(f"   {code} | {name:<12} | KOSPI200: '{kospi200_info}'")
                    
                    if kospi200_info and kospi200_info.strip() and kospi200_info.strip() != "미채용":
                        kospi200_stocks.append((code, name, kospi200_info))
                    else:
                        non_kospi200_stocks.append((code, name, kospi200_info))
                        
                else:
                    print(f"   {code} | {name:<12} | ❌ 조회 실패 (result: {result})")
                
                # 요청 제한 준수
                time.sleep(random.uniform(0.2, 0.5))
                
            except Exception as e:
                print(f"   {code} | {name:<12} | ❌ 에러: {str(e)}")
        
        # 결과 요약
        print(f"\n📈 결과 요약:")
        print(f"   KOSPI200 편입 종목: {len(kospi200_stocks)}개")
        for code, name, info in kospi200_stocks:
            print(f"      {code} | {name} → '{info}'")
        
        print(f"\n   KOSPI200 미편입 종목: {len(non_kospi200_stocks)}개")
        for code, name, info in non_kospi200_stocks:
            print(f"      {code} | {name} → '{info}'")
        
        # KOSPI200 섹터 분포
        if kospi200_stocks:
            print(f"\n🏭 KOSPI200 섹터 분포:")
            sector_count = {}
            for code, name, info in kospi200_stocks:
                sector = info.strip() if info else "미분류"
                sector_count[sector] = sector_count.get(sector, 0) + 1
            
            for sector, count in sector_count.items():
                print(f"   {sector}: {count}개")
        
    except Exception as e:
        print(f"❌ COM 객체 생성 실패: {str(e)}")
        print("   Cybos Plus가 실행되지 않았거나 관리자 권한이 필요할 수 있습니다.")

if __name__ == "__main__":
    check_kospi200_via_api()

"""
History Data Analysis - 히스토리 데이터 분석 도구

수집된 히스토리 데이터를 이용한 기본적인 시계열 분석 기능을 제공합니다.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.history_integration_service import HistoryIntegrationService, IntegratedCandle


class HistoryAnalyzer:
    """히스토리 데이터 분석 클래스"""
    
    def __init__(self, db_path: str = "data/cybos.db"):
        self.integration_service = HistoryIntegrationService(db_path)
    
    def calculate_moving_average(self, data: List[IntegratedCandle], period: int) -> List[float]:
        """이동평균 계산"""
        if len(data) < period:
            return []
        
        ma_values = []
        for i in range(period - 1, len(data)):
            sum_close = sum(candle.close_price for candle in data[i - period + 1:i + 1])
            ma_values.append(sum_close / period)
        
        return ma_values
    
    def calculate_volatility(self, data: List[IntegratedCandle], period: int = 20) -> List[float]:
        """변동성 계산 (표준편차)"""
        if len(data) < period:
            return []
        
        import math
        
        volatility_values = []
        for i in range(period - 1, len(data)):
            prices = [candle.close_price for candle in data[i - period + 1:i + 1]]
            mean_price = sum(prices) / len(prices)
            variance = sum((price - mean_price) ** 2 for price in prices) / len(prices)
            volatility = math.sqrt(variance)
            volatility_values.append(volatility)
        
        return volatility_values
    
    def find_support_resistance(self, data: List[IntegratedCandle], lookback: int = 10) -> Dict[str, List[int]]:
        """지지/저항선 찾기 (단순 로컬 최고/최저점)"""
        if len(data) < lookback * 2 + 1:
            return {"support": [], "resistance": []}
        
        support_levels = []
        resistance_levels = []
        
        for i in range(lookback, len(data) - lookback):
            current_high = data[i].high_price
            current_low = data[i].low_price
            
            # 저항선: 주변보다 높은 고점
            is_resistance = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and data[j].high_price >= current_high:
                    is_resistance = False
                    break
            
            if is_resistance:
                resistance_levels.append(current_high)
            
            # 지지선: 주변보다 낮은 저점
            is_support = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and data[j].low_price <= current_low:
                    is_support = False
                    break
            
            if is_support:
                support_levels.append(current_low)
        
        return {"support": support_levels, "resistance": resistance_levels}
    
    def generate_stock_report(self, code: str, days: int = 60) -> Dict[str, Any]:
        """종목 분석 보고서 생성"""
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # 데이터 조회
        data = self.integration_service.get_complete_daily_data(code, start_date, end_date)
        
        if not data:
            return {"error": "데이터 없음"}
        
        # 기본 통계
        latest = data[-1]
        oldest = data[0]
        
        high_prices = [candle.high_price for candle in data]
        low_prices = [candle.low_price for candle in data]
        close_prices = [candle.close_price for candle in data]
        volumes = [candle.volume for candle in data]
        
        # 수익률 계산
        total_return = ((latest.close_price - oldest.close_price) / oldest.close_price) * 100
        
        # 이동평균
        ma5 = self.calculate_moving_average(data, 5)
        ma20 = self.calculate_moving_average(data, 20)
        ma60 = self.calculate_moving_average(data, 60)
        
        # 변동성
        volatility = self.calculate_volatility(data, 20)
        
        # 지지/저항선
        support_resistance = self.find_support_resistance(data)
        
        # 거래량 분석
        avg_volume = sum(volumes) / len(volumes)
        recent_volume_trend = "증가" if len(volumes) > 5 and volumes[-5:] > volumes[-10:-5] else "감소"
        
        return {
            "code": code,
            "analysis_period": f"{start_date} ~ {end_date}",
            "data_points": len(data),
            "price_info": {
                "current_price": latest.close_price,
                "period_high": max(high_prices),
                "period_low": min(low_prices),
                "total_return_pct": round(total_return, 2)
            },
            "moving_averages": {
                "ma5": round(ma5[-1], 2) if ma5 else None,
                "ma20": round(ma20[-1], 2) if ma20 else None,
                "ma60": round(ma60[-1], 2) if ma60 else None
            },
            "volatility": {
                "current": round(volatility[-1], 2) if volatility else None,
                "average": round(sum(volatility) / len(volatility), 2) if volatility else None
            },
            "support_resistance": {
                "support_levels": support_resistance["support"][-3:],  # 최근 3개
                "resistance_levels": support_resistance["resistance"][-3:]  # 최근 3개
            },
            "volume_info": {
                "average_volume": int(avg_volume),
                "recent_trend": recent_volume_trend,
                "latest_volume": latest.volume
            },
            "data_quality": {
                "history_data_points": sum(1 for d in data if not d.is_realtime),
                "realtime_data_points": sum(1 for d in data if d.is_realtime),
                "completeness_pct": (len(data) / days) * 100
            }
        }


def analyze_stock(code: str, days: int = 60):
    """종목 분석 실행"""
    print(f"📊 {code} 종목 분석 (최근 {days}일)")
    print("=" * 60)
    
    analyzer = HistoryAnalyzer()
    report = analyzer.generate_stock_report(code, days)
    
    if "error" in report:
        print(f"❌ 분석 실패: {report['error']}")
        return
    
    # 보고서 출력
    print(f"📈 종목 정보:")
    print(f"   종목코드: {report['code']}")
    print(f"   분석기간: {report['analysis_period']}")
    print(f"   데이터 포인트: {report['data_points']}개")
    
    price_info = report['price_info']
    print(f"\n💰 가격 정보:")
    print(f"   현재가: {price_info['current_price']:,}원")
    print(f"   기간 고점: {price_info['period_high']:,}원")
    print(f"   기간 저점: {price_info['period_low']:,}원")
    print(f"   총 수익률: {price_info['total_return_pct']:+.2f}%")
    
    ma_info = report['moving_averages']
    print(f"\n📉 이동평균:")
    if ma_info['ma5']:
        print(f"   MA5: {ma_info['ma5']:,.2f}원")
    if ma_info['ma20']:
        print(f"   MA20: {ma_info['ma20']:,.2f}원")
    if ma_info['ma60']:
        print(f"   MA60: {ma_info['ma60']:,.2f}원")
    
    vol_info = report['volatility']
    print(f"\n🌪️  변동성:")
    if vol_info['current']:
        print(f"   현재 변동성: {vol_info['current']:,.2f}원")
        print(f"   평균 변동성: {vol_info['average']:,.2f}원")
    
    sr_info = report['support_resistance']
    print(f"\n🎯 지지/저항선:")
    if sr_info['support_levels']:
        print(f"   지지선: {[f'{p:,}원' for p in sr_info['support_levels']]}")
    if sr_info['resistance_levels']:
        print(f"   저항선: {[f'{p:,}원' for p in sr_info['resistance_levels']]}")
    
    volume_info = report['volume_info']
    print(f"\n📊 거래량 정보:")
    print(f"   평균 거래량: {volume_info['average_volume']:,}주")
    print(f"   최근 거래량: {volume_info['latest_volume']:,}주")
    print(f"   거래량 추세: {volume_info['recent_trend']}")
    
    quality_info = report['data_quality']
    print(f"\n🔍 데이터 품질:")
    print(f"   히스토리 데이터: {quality_info['history_data_points']}개")
    print(f"   실시간 데이터: {quality_info['realtime_data_points']}개")
    print(f"   데이터 완전성: {quality_info['completeness_pct']:.1f}%")


def compare_stocks(codes: List[str], days: int = 30):
    """여러 종목 비교 분석"""
    print(f"🔍 종목 비교 분석 (최근 {days}일)")
    print("=" * 60)
    
    analyzer = HistoryAnalyzer()
    
    comparison_data = []
    for code in codes:
        report = analyzer.generate_stock_report(code, days)
        if "error" not in report:
            comparison_data.append(report)
        else:
            print(f"⚠️  {code}: 데이터 없음")
    
    if not comparison_data:
        print("❌ 비교할 데이터가 없습니다.")
        return
    
    # 비교표 출력
    print(f"\n📊 종목 비교표:")
    print(f"{'종목코드':<10} {'현재가':<12} {'수익률':<10} {'변동성':<12} {'데이터완전성':<12}")
    print("-" * 70)
    
    for report in comparison_data:
        code = report['code']
        price = report['price_info']['current_price']
        return_pct = report['price_info']['total_return_pct']
        volatility = report['volatility']['average'] or 0
        completeness = report['data_quality']['completeness_pct']
        
        print(f"{code:<10} {price:>10,}원 {return_pct:>+8.2f}% {volatility:>10,.0f}원 {completeness:>10.1f}%")
    
    # 최고 성과 종목
    best_performer = max(comparison_data, key=lambda x: x['price_info']['total_return_pct'])
    worst_performer = min(comparison_data, key=lambda x: x['price_info']['total_return_pct'])
    
    print(f"\n🏆 분석 결과:")
    print(f"   최고 수익률: {best_performer['code']} ({best_performer['price_info']['total_return_pct']:+.2f}%)")
    print(f"   최저 수익률: {worst_performer['code']} ({worst_performer['price_info']['total_return_pct']:+.2f}%)")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="히스토리 데이터 분석")
    
    subparsers = parser.add_subparsers(dest="command", help="분석 명령어")
    
    # 단일 종목 분석
    analyze_parser = subparsers.add_parser("analyze", help="종목 분석")
    analyze_parser.add_argument("code", help="종목코드")
    analyze_parser.add_argument("--days", type=int, default=60, help="분석 기간 (일)")
    
    # 종목 비교
    compare_parser = subparsers.add_parser("compare", help="종목 비교")
    compare_parser.add_argument("codes", nargs="+", help="종목코드들")
    compare_parser.add_argument("--days", type=int, default=30, help="비교 기간 (일)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "analyze":
        analyze_stock(args.code, args.days)
    elif args.command == "compare":
        compare_stocks(args.codes, args.days)
    else:
        print(f"❌ 알 수 없는 명령어: {args.command}")

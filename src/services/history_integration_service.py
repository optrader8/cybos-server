"""
History Integration Service - 히스토리와 실시간 데이터 통합 서비스

히스토리 데이터와 실시간 시세 데이터를 통합하여 완전한 시계열 분석을 제공합니다.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..database.connection import get_connection_context
from ..database.models.history import HistoryTable, HistoryInfo, HistoryTimeframe
from ..database.models.price import PriceTable, PriceInfo


@dataclass
class IntegratedCandle:
    """통합된 캔들 데이터"""
    code: str
    date: str
    timeframe: str
    open_price: int
    high_price: int
    low_price: int
    close_price: int
    volume: int
    amount: int
    is_realtime: bool  # True: 실시간 데이터, False: 히스토리 데이터


class HistoryIntegrationService:
    """히스토리-실시간 데이터 통합 서비스"""
    
    def __init__(self, db_path: str = "data/cybos.db"):
        self.db_path = db_path
    
    def get_complete_daily_data(self, 
                               code: str, 
                               start_date: str, 
                               end_date: str) -> List[IntegratedCandle]:
        """완전한 일봉 데이터 조회 (히스토리 + 실시간)"""
        
        with get_connection_context(self.db_path) as conn:
            # 히스토리 데이터 조회
            history_data = HistoryTable.get_history(
                conn, code, HistoryTimeframe.DAILY, start_date, end_date
            )
            
            # 오늘 날짜의 실시간 데이터 조회
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 통합 데이터 생성
            integrated_data = []
            
            # 히스토리 데이터 추가
            for history in history_data:
                if history.date != today:  # 오늘이 아닌 데이터만
                    integrated_data.append(IntegratedCandle(
                        code=history.code,
                        date=history.date,
                        timeframe='D',
                        open_price=history.open_price,
                        high_price=history.high_price,
                        low_price=history.low_price,
                        close_price=history.close_price,
                        volume=history.volume,
                        amount=history.amount,
                        is_realtime=False
                    ))
            
            # 오늘 데이터는 실시간 시세에서 생성
            if start_date <= today <= end_date:
                today_candle = self._create_today_candle_from_realtime(conn, code, today)
                if today_candle:
                    integrated_data.append(today_candle)
            
            # 날짜순 정렬
            integrated_data.sort(key=lambda x: x.date)
            
            return integrated_data
    
    def _create_today_candle_from_realtime(self, 
                                          conn, 
                                          code: str, 
                                          date: str) -> Optional[IntegratedCandle]:
        """실시간 시세 데이터로부터 오늘의 캔들 생성"""
        
        # 오늘 하루의 모든 실시간 데이터 조회
        cursor = conn.execute(f"""
            SELECT 
                open_price, high_price, low_price, current_price as close_price,
                volume, amount
            FROM {PriceTable.TABLE_NAME}
            WHERE code = ? 
              AND date(created_at) = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (code, date))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        # 오늘의 OHLC 계산을 위해 모든 틱 데이터 조회
        cursor = conn.execute(f"""
            SELECT 
                MIN(open_price) as min_open,
                MAX(high_price) as max_high,
                MIN(low_price) as min_low,
                current_price as close,
                SUM(volume) as total_volume,
                SUM(amount) as total_amount
            FROM {PriceTable.TABLE_NAME}
            WHERE code = ? 
              AND date(created_at) = ?
        """, (code, date))
        
        ohlc_row = cursor.fetchone()
        if not ohlc_row:
            return None
        
        # 시가는 첫 번째 데이터의 현재가
        cursor = conn.execute(f"""
            SELECT current_price
            FROM {PriceTable.TABLE_NAME}
            WHERE code = ? 
              AND date(created_at) = ?
            ORDER BY created_at ASC
            LIMIT 1
        """, (code, date))
        
        first_row = cursor.fetchone()
        open_price = first_row[0] if first_row else ohlc_row[3]
        
        return IntegratedCandle(
            code=code,
            date=date,
            timeframe='D',
            open_price=open_price,
            high_price=ohlc_row[1] or 0,
            low_price=ohlc_row[2] or 0,
            close_price=ohlc_row[3] or 0,
            volume=ohlc_row[4] or 0,
            amount=ohlc_row[5] or 0,
            is_realtime=True
        )
    
    def check_data_completeness(self, code: str, days: int = 30) -> Dict[str, Any]:
        """데이터 완전성 검사"""
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        with get_connection_context(self.db_path) as conn:
            # 히스토리 데이터 개수
            history_cursor = conn.execute(f"""
                SELECT COUNT(*) FROM {HistoryTable.TABLE_NAME}
                WHERE code = ? 
                  AND timeframe = 'D'
                  AND date BETWEEN ? AND ?
            """, (code, start_date, end_date))
            
            history_count = history_cursor.fetchone()[0]
            
            # 실시간 데이터 개수 (오늘)
            today = datetime.now().strftime('%Y-%m-%d')
            realtime_cursor = conn.execute(f"""
                SELECT COUNT(*) FROM {PriceTable.TABLE_NAME}
                WHERE code = ?
                  AND date(created_at) = ?
            """, (code, today))
            
            realtime_count = realtime_cursor.fetchone()[0]
            
            # 최신 히스토리 데이터 날짜
            latest_cursor = conn.execute(f"""
                SELECT MAX(date) FROM {HistoryTable.TABLE_NAME}
                WHERE code = ? AND timeframe = 'D'
            """, (code,))
            
            latest_history_date = latest_cursor.fetchone()[0]
            
            return {
                "code": code,
                "period_days": days,
                "start_date": start_date,
                "end_date": end_date,
                "history_records": history_count,
                "realtime_records_today": realtime_count,
                "latest_history_date": latest_history_date,
                "has_today_realtime": realtime_count > 0,
                "data_gap_days": self._calculate_data_gap(latest_history_date, today)
            }
    
    def _calculate_data_gap(self, latest_history_date: str, today: str) -> int:
        """데이터 공백 일수 계산"""
        if not latest_history_date:
            return 999  # 히스토리 데이터 없음
        
        try:
            latest_dt = datetime.strptime(latest_history_date, '%Y-%m-%d')
            today_dt = datetime.strptime(today, '%Y-%m-%d')
            return (today_dt - latest_dt).days
        except:
            return 0
    
    def sync_today_data(self, code: str) -> bool:
        """오늘의 실시간 데이터를 히스토리로 동기화"""
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        with get_connection_context(self.db_path) as conn:
            # 오늘의 캔들 데이터 생성
            today_candle = self._create_today_candle_from_realtime(conn, code, today)
            
            if today_candle:
                # 히스토리 테이블에 저장
                history_info = HistoryInfo(
                    code=code,
                    timeframe=HistoryTimeframe.DAILY,
                    date=today,
                    open_price=today_candle.open_price,
                    high_price=today_candle.high_price,
                    low_price=today_candle.low_price,
                    close_price=today_candle.close_price,
                    volume=today_candle.volume,
                    amount=today_candle.amount
                )
                
                HistoryTable.upsert_history(conn, history_info)
                conn.commit()
                
                print(f"✅ {code} 오늘 데이터 동기화 완료")
                return True
            else:
                print(f"⚠️  {code} 오늘 실시간 데이터 없음")
                return False

"""
종목 코드 동기화 스크립트

Cybos Plus에서 종목 정보를 가져와 데이터베이스에 저장합니다.
Usage: python scripts/sync_stock_codes.py [--market MARKET] [--detailed] [--db-path PATH]
"""

import sys
import os
from pathlib import Path
import argparse

# src 디렉토리를 모듈 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.cybos.codes.fetcher import StockCodeFetcher, get_stock_counts
from src.database.models.stock import StockTable, MarketKind
from src.database.connection import get_connection_context


def sync_stocks(db_path: str, market: str = "all", detailed: bool = False) -> None:
    """
    종목 정보를 동기화합니다.

    Args:
        db_path: 데이터베이스 파일 경로
        market: 동기화할 시장 (all, kospi, kosdaq, freeboard, krx)
        detailed: True면 상세 정보까지 수집 (느림)
    """
    print(f"🚀 종목 코드 동기화 시작")
    print(f"   - 데이터베이스: {db_path}")
    print(f"   - 시장: {market}")
    print(f"   - 상세 정보: {'예' if detailed else '아니오'}")
    print()

    try:
        # CYBOS Plus 연결 확인
        print("🔌 Cybos Plus 연결 확인...")
        fetcher = StockCodeFetcher()
        counts = get_stock_counts()
        print(f"   ✅ 연결 성공")
        print(f"   📊 시장별 종목 수:")
        for market_name, count in counts.items():
            print(f"      - {market_name}: {count}")
        print()

        # 종목 정보 수집
        print("📥 종목 정보 수집 중...")

        if market == "all":
            stocks = fetcher.fetch_all_stocks(detailed=detailed)
        elif market == "kospi":
            stocks = fetcher.fetch_market_stocks(MarketKind.KOSPI, detailed=detailed)
        elif market == "kosdaq":
            stocks = fetcher.fetch_market_stocks(MarketKind.KOSDAQ, detailed=detailed)
        elif market == "freeboard":
            stocks = fetcher.fetch_market_stocks(MarketKind.FREEBOARD, detailed=detailed)
        elif market == "krx":
            stocks = fetcher.fetch_market_stocks(MarketKind.KRX, detailed=detailed)
        else:
            raise ValueError(f"Unknown market: {market}")

        print(f"   ✅ {len(stocks)}개 종목 수집 완료")
        print()

        # 데이터베이스에 저장
        print("💾 데이터베이스 저장 중...")
        with get_connection_context(db_path) as conn:
            for i, stock in enumerate(stocks):
                StockTable.insert_stock(conn, stock)

                # 진행상황 출력 (100개마다)
                if (i + 1) % 100 == 0:
                    print(f"   - {i + 1}/{len(stocks)} 저장 완료")

            conn.commit()

        print(f"   ✅ {len(stocks)}개 종목 저장 완료")
        print()

        # 결과 요약
        print_sync_summary(db_path)

    except Exception as e:
        print(f"\n❌ 동기화 실패: {str(e)}")
        raise


def print_sync_summary(db_path: str) -> None:
    """동기화 결과 요약 출력"""
    print("📊 동기화 결과 요약:")

    with get_connection_context(db_path) as conn:
        counts = StockTable.count_stocks(conn)

        for key, value in counts.items():
            if key == "total":
                print(f"   - 전체: {value}")
            else:
                print(f"   - {key}: {value}")

    print()
    print("✅ 종목 코드 동기화 완료!")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="종목 코드 동기화 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 전체 시장 동기화 (기본 정보만)
  python scripts/sync_stock_codes.py

  # KOSPI만 동기화
  python scripts/sync_stock_codes.py --market kospi

  # 전체 시장 동기화 (상세 정보 포함, 느림)
  python scripts/sync_stock_codes.py --detailed

  # 특정 데이터베이스에 동기화
  python scripts/sync_stock_codes.py --db-path data/my_db.db

  # KOSDAQ 상세 정보 동기화
  python scripts/sync_stock_codes.py --market kosdaq --detailed
        """
    )

    parser.add_argument(
        '--market',
        type=str,
        choices=['all', 'kospi', 'kosdaq', 'freeboard', 'krx'],
        default='all',
        help='동기화할 시장 (기본값: all)'
    )

    parser.add_argument(
        '--detailed',
        action='store_true',
        help='상세 정보까지 수집 (느림)'
    )

    parser.add_argument(
        '--db-path',
        type=str,
        default=None,
        help='데이터베이스 파일 경로 (기본값: 환경변수 DATABASE_PATH 또는 data/cybos.db)'
    )

    args = parser.parse_args()

    # 데이터베이스 경로 결정
    db_path = args.db_path
    if db_path is None:
        db_path = os.getenv('DATABASE_PATH', 'data/cybos.db')

    # 동기화 실행
    try:
        sync_stocks(db_path, args.market, args.detailed)
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()

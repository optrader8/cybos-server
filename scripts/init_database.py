"""
데이터베이스 초기화 스크립트

모든 테이블을 생성하고 인덱스를 설정합니다.
Usage: python scripts/init_database.py [--db-path PATH] [--force]
"""

import sys
import os
from pathlib import Path
import argparse
import sqlite3

# src 디렉토리를 모듈 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.models.stock import StockTable
from src.database.models.price import PriceTable
from src.database.models.history import HistoryTable
from src.database.models.pair import PairTable
from src.database.models.signal import SignalTable
from src.database.models.cointegration import CointegrationTable
from src.database.connection import get_connection_context


def init_database(db_path: str, force: bool = False) -> None:
    """
    데이터베이스를 초기화합니다.

    Args:
        db_path: 데이터베이스 파일 경로
        force: True면 기존 데이터베이스 파일을 삭제하고 재생성
    """
    # force 옵션이면 기존 파일 삭제
    if force and os.path.exists(db_path):
        print(f"🗑️  기존 데이터베이스 삭제: {db_path}")
        os.remove(db_path)

    # 데이터베이스 디렉토리 생성
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"📁 디렉토리 생성: {db_dir}")

    print(f"🚀 데이터베이스 초기화 시작: {db_path}")

    try:
        with get_connection_context(db_path) as conn:
            # 테이블 생성 순서 (외래키 의존성 고려)
            tables = [
                ("주식 정보", StockTable),
                ("시세 데이터", PriceTable),
                ("과거 데이터", HistoryTable),
                ("페어 정보", PairTable),
                ("공적분 결과", CointegrationTable),
                ("트레이딩 신호", SignalTable),
            ]

            # 테이블 생성
            print("\n📋 테이블 생성 중...")
            for table_name, table_class in tables:
                print(f"   - {table_name} ({table_class.TABLE_NAME})")
                table_class.create_table(conn)

            # 인덱스 생성
            print("\n🔍 인덱스 생성 중...")
            for table_name, table_class in tables:
                if hasattr(table_class, 'create_indexes'):
                    print(f"   - {table_name} 인덱스")
                    table_class.create_indexes(conn)

            conn.commit()

        print("\n✅ 데이터베이스 초기화 완료!")

        # 테이블 정보 출력
        print_table_info(db_path)

    except Exception as e:
        print(f"\n❌ 데이터베이스 초기화 실패: {str(e)}")
        raise


def print_table_info(db_path: str) -> None:
    """데이터베이스 테이블 정보 출력"""
    print("\n📊 테이블 정보:")

    with get_connection_context(db_path) as conn:
        cursor = conn.cursor()

        # 모든 테이블 조회
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)

        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            # 테이블 행 수 조회
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]

            print(f"   - {table}: {count} rows")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="데이터베이스 초기화 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 기본 경로로 초기화
  python scripts/init_database.py

  # 특정 경로로 초기화
  python scripts/init_database.py --db-path data/my_db.db

  # 기존 데이터베이스 삭제 후 재생성
  python scripts/init_database.py --force
        """
    )

    parser.add_argument(
        '--db-path',
        type=str,
        default=None,
        help='데이터베이스 파일 경로 (기본값: 환경변수 DATABASE_PATH 또는 data/cybos.db)'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='기존 데이터베이스를 삭제하고 재생성'
    )

    args = parser.parse_args()

    # 데이터베이스 경로 결정
    db_path = args.db_path
    if db_path is None:
        db_path = os.getenv('DATABASE_PATH', 'data/cybos.db')

    # 초기화 실행
    try:
        init_database(db_path, args.force)
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()

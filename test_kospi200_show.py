import sqlite3

def print_kospi200_stocks(db_path="data/cybos.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # 예시: kospi200_kind 또는 is_kospi200 컬럼이 1 또는 True인 경우
    # 실제 컬럼명에 맞게 수정 필요
    try:
        cur.execute("""
            SELECT code, name
            FROM stock
            WHERE kospi200_kind=1 OR is_kospi200=1
        """)
    except sqlite3.OperationalError:
        # 컬럼명이 다를 경우 fallback (예: sector, field53 등)
        print("❗ KOSPI200 판별 컬럼명을 확인하세요.")
        conn.close()
        return

    rows = cur.fetchall()
    print(f"KOSPI200 종목 수: {len(rows)}")
    for code, name in rows:
        print(f"{code}\t{name}")
    conn.close()

if __name__ == "__main__":
    print_kospi200_stocks()
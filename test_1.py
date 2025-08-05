import win32com.client

def is_connected():
    cybos = win32com.client.Dispatch("CpUtil.CpCybos")
    return cybos.IsConnect == 1

def print_stock_info():
    code_mgr = win32com.client.Dispatch("CpUtil.CpCodeMgr")

    kospi_codes = code_mgr.GetStockListByMarket(1)
    kosdaq_codes = code_mgr.GetStockListByMarket(2)

    print(f"[KOSPI 종목 수] {len(kospi_codes)}")
    print(f"[KOSDAQ 종목 수] {len(kosdaq_codes)}")

    print("=== KOSPI 주요 종목 정보 샘플 ===")
    for code in list(kospi_codes):
        name = code_mgr.CodeToName(code)
        section = code_mgr.GetStockSectionKind(code)
        print(f"종목코드: {code}, 이름: {name}, 섹션: {section}")

if __name__ == "__main__":
    if not is_connected():
        print("Cybos Plus 연결 실패. HTS 실행 및 로그인 상태를 확인하세요.")
        exit(1)
    print_stock_info()

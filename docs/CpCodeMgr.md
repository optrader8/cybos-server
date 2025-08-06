네, 알겠습니다. 제공해주신 `CpCodeMgr` API 명세서를 이전과 동일한 형식으로 명확하게 재구성하여 보여드리겠습니다.

---

# API 명세서: CpCodeMgr

## 1. 개요

`CpCodeMgr`은 주식, 선물/옵션, 업종 등 다양한 종목의 코드와 관련된 상세 정보를 조회하거나, 조건에 맞는 코드 리스트를 얻기 위한 COM 객체입니다.

-   **주요 기능**: 코드-이름 변환, 종목 상세 정보 조회, 시장/업종별 종목 리스트 검색
-   **모듈 위치**: `CpUtil.dll`

## 2. Methods

메서드는 기능에 따라 다음과 같이 분류됩니다.

### 2.1. 공통 코드 변환

| 메서드 | 설명 |
| :--- | :--- |
| `object.CodeToName(code)` | `code`에 해당하는 주식/선물/옵션 종목명을 반환합니다. |

---

### 2.2. 개별 주식 코드 정보 조회

각 메서드는 입력 파라미터로 `code`(주식코드)를 받습니다.

| 메서드 | 설명 | 반환값 |
| :--- | :--- | :--- |
| `object.GetStockMarginRate(code)` | 매수 증거금율을 반환합니다. | `float` |
| `object.GetStockMemeMin(code)` | 매매 거래단위 주식 수를 반환합니다. | `long` |
| `object.GetStockIndustryCode(code)` | 증권전산 업종코드를 반환합니다. | `string` |
| `object.GetStockMarketKind(code)` | 소속부(시장) 구분을 반환합니다. (상세 코드는 아래 참고) | `enum` |
| `object.GetStockControlKind(code)` | 감리 구분을 반환합니다. (상세 코드는 아래 참고) | `enum` |
| `object.GetStockSupervisionKind(code)`| 관리 구분을 반환합니다. (상세 코드는 아래 참고) | `enum` |
| `object.GetStockStatusKind(code)` | 주식 상태를 반환합니다. (상세 코드는 아래 참고) | `enum` |
| `object.GetStockCapital(code)` | 자본금 규모 구분을 반환합니다. (상세 코드는 아래 참고) | `enum` |
| `object.GetStockFiscalMonth(code)` | 결산월을 반환합니다. | `long` |
| `object.GetStockGroupCode(code)` | 그룹(계열사) 코드를 반환합니다. | `string` |
| `object.GetStockKospi200Kind(code)` | KOSPI200 종목 여부 및 소속 산업을 반환합니다. (상세 코드는 아래 참고) | `enum` |
| `object.GetStockSectionKind(code)` | 부(Section) 구분 코드를 반환합니다. (상세 코드는 아래 참고) | `enum` |
| `object.GetStockLacKind(code)` | 락(Lac) 구분 코드를 반환합니다. (상세 코드는 아래 참고) | `enum` |
| `object.GetStockListedDate(code)` | 상장일을 반환합니다. | `long` |
| `object.GetStockMaxPrice(code)` | 상한가를 반환합니다. | `long` |
| `object.GetStockMinPrice(code)` | 하한가를 반환합니다. | `long` |
| `object.GetStockParPrice(code)` | 액면가를 반환합니다. | `long` |
| `object.GetStockStdPrice(code)` | 기준가(권리락 등)를 반환합니다. | `long` |
| `object.GetStockYdOpenPrice(code)` | 전일 시가를 반환합니다. | `long` |
| `object.GetStockYdHighPrice(code)` | 전일 고가를 반환합니다. | `long` |
| `object.GetStockYdLowPrice(code)` | 전일 저가를 반환합니다. | `long` |
| `object.GetStockYdClosePrice(code)` | 전일 종가를 반환합니다. | `long` |
| `object.IsStockCreditEnable(code)` | 신용 가능 종목 여부를 반환합니다. | `bool` |
| `object.GetStockParPriceChageType(code)`| 액면가 변경 정보 코드를 반환합니다. (상세 코드는 아래 참고) | `enum` |

---

### 2.3. ELW 바스켓 정보 조회

**※** 아래 두 함수는 `CpElwCode` 객체에도 동일하게 존재합니다.

| 메서드 | 설명 |
| :--- | :--- |
| `object.GetStockElwBasketCodeList(code)` | ELW의 기초자산(바스켓) 코드 리스트를 배열로 반환합니다. |
| `object.GetStockElwBasketCompList(code)` | ELW의 기초자산(바스켓) 비율 리스트를 배열로 반환합니다. |

---

### 2.4. 각종 코드 리스트 조회

| 메서드 | 설명 |
| :--- | :--- |
| `object.GetStockListByMarket(market_code)` | `market_code`에 해당하는 시장의 모든 종목 코드를 배열로 반환합니다. (market_code는 `GetStockMarketKind` 참고) |
| `object.GetGroupCodeList(group_code)` | 관심종목 그룹(700~799) 또는 업종 코드에 해당하는 종목 코드를 배열로 반환합니다. |
| `object.GetGroupName(group_code)` | 관심종목 그룹 또는 업종 코드에 해당하는 명칭을 반환합니다. |
| `object.GetIndustryList()` | 전체 증권전산 업종 코드 리스트를 배열로 반환합니다. |
| `object.GetIndustryName(industry_code)` | 증권전산 업종 코드에 해당하는 업종명을 반환합니다. |
| `object.GetMemberList()` | 전체 거래원(회원사) 코드 리스트를 배열로 반환합니다. |
| `object.GetMemberName(member_code)` | 거래원 코드에 해당하는 거래원명을 반환합니다. |
| `object.GetKosdaqIndustry1List()` | 코스닥 산업별 코드 리스트를 배열로 반환합니다. |
| `object.GetKosdaqIndustry2List()` | 코스닥 지수 업종 코드 리스트를 배열로 반환합니다. |

---

### 2.5. 기타 정보 조회

| 메서드 | 설명 | 반환값 |
| :--- | :--- | :--- |
| `object.GetMarketStartTime()` | 장 시작 시각을 반환합니다. (예: 9시 -> 9) | `long` |
| `object.GetMarketEndTime()` | 장 마감 시각을 반환합니다. (예: 15시 -> 15) | `long` |

---

## 3. 상세 코드 정보 (Enums)

### `GetStockMarketKind` (소속부)
| 값 | 내용 |
| :--- | :--- |
| 0 | 구분없음 |
| 1 | 거래소(KOSPI) |
| 2 | 코스닥(KOSDAQ) |
| 3 | 프리보드 |
| 4 | KRX |

### `GetStockControlKind` (감리 구분)
| 값 | 내용 |
| :--- | :--- |
| 0 | 정상 |
| 1 | 주의 |
| 2 | 경고 |
| 3 | 위험예고 |
| 4 | 위험 |

### `GetStockSupervisionKind` (관리 구분)
| 값 | 내용 |
| :--- | :--- |
| 0 | 일반종목 |
| 1 | 관리 |

### `GetStockStatusKind` (주식 상태)
| 값 | 내용 |
| :--- | :--- |
| 0 | 정상 |
| 1 | 거래정지 |
| 2 | 거래중단 |

### `GetStockCapital` (자본금 규모)
| 값 | 내용 |
| :--- | :--- |
| 0 | 제외 |
| 1 | 대 |
| 2 | 중 |
| 3 | 소 |

### `GetStockKospi200Kind` (KOSPI200 구분)
**~ 2011/03/31**
| 값 | 내용 |
| :--- | :--- |
| 0 | 미채용 |
| 1 | 제조업 |
| 2 | 전기통신업 |
| 3 | 건설업 |
| 4 | 유통업 |
| 5 | 금융업 |

**2011/04/01 ~**
| 값 | 내용 |
| :--- | :--- |
| 0 | 미채용 |
| 1 | 건설기계 |
| 2 | 조선운송 |
| 3 | 철강소재 |
| 4 | 에너지화학 |
| 5 | 정보통신 |
| 6 | 금융 |
| 7 | 필수소비재 |
| 8 | 자유소비재 |

### `GetStockSectionKind` (부 구분)
| 값 | 내용 |
| :--- | :--- |
| 0 | 구분없음 |
| 1 | 주권 |
| 2 | 투자회사 |
| 3 | 부동산투자회사 |
| 4 | 선박투자회사 |
| 5 | 사회간접자본투융자회사 |
| 6 | 주식예탁증서 |
| 7 | 신수인수권증권 |
| 8 | 신주인수권증서 |
| 9 | 주식워런트증권 |
| 10 | 상장지수펀드(ETF) |
| 11 | 수익증권 |
| 12 | 해외ETF |
| 13 | 외국주권 |
| 14 | 선물 |
| 15 | 옵션 |

### `GetStockLacKind` (락 구분)
| 값 | 내용 |
| :--- | :--- |
| 0 | 구분없음 |
| 1 | 권리락 |
| 2 | 배당락 |
| 3 | 분배락 |
| 4 | 권배락 |
| 5 | 중간배당락 |
| 6 | 권리중간배당락 |
| 99 | 기타 |

### `GetStockParPriceChageType` (액면가 변경)
| 값 | 내용 |
| :--- | :--- |
| 0 | 해당없음 |
| 1 | 액면분할 |
| 2 | 액면병합 |
| 99 | 기타 |
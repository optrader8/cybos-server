CpCodeMgr

설명: 각종 코드정보 및 코드 리스트를 얻을 수 있습니다.

모듈위치: CpUtil.dll

Method

[주식/선물/옵션]

value = object.CodeToName( code )

code 에 해당하는 주식/선물/옵션 종목명 을 반환한다.

code : 주식/선물/옵션 코드

반환값 : 주식/선물/옵션 종목명

 

[주식 코드 정보]

value = object.GetStockMarginRate( code )

code 에 해당하는 주식 매수 증거금율을 반환한다.

code : 주식코드
반환값 : 주식 매수 증거금율 

 

value = object.GetStockMemeMin( code )

code 에 해당하는 주식 매매 거래단위주식수를 반환한다.

code : 주식코드
반환값 : 주식 매매 거래단위 주식수

 

value = object. GetStockIndustryCode ( code )

code 에 해당하는 증권전산업종코드를 반환한다.

code : 주식코드
반환값 : 증권전산업종코드

 

value = object. GetStockMarketKind ( code )

code 에 해당하는 소속부를 반환한다.

code : 주식코드
반환값 : 소속부
typedef enum {
[helpstring("구분없음")] CPC_MARKET_NULL  = 0,
[helpstring("거래소")]    CPC_MARKET_KOSPI  = 1,
[helpstring("코스닥")]    CPC_MARKET_KOSDAQ = 2,
[helpstring("프리보드")] CPC_MARKET_FREEBOARD = 3,
[helpstring("KRX")]    CPC_MARKET_KRX  = 4,
}CPE_MARKET_KIND;
 

value = object. GetStockControlKind ( code )

code 에 해당하는 감리구분 반환한다.

code : 주식코드
반환값 : 감리구분
typedef enum {
[helpstring("정상")]    CPC_CONTROL_NONE     = 0,
[helpstring("주의")]    CPC_CONTROL_ATTENTION  = 1,
[helpstring("경고")]    CPC_CONTROL_WARNING  = 2,
[helpstring("위험예고")] CPC_CONTROL_DANGER_NOTICE= 3,
[helpstring("위험")]    CPC_CONTROL_DANGER = 4,
}CPE_CONTROL_KIND;

 

value = object. GetStockSupervisionKind ( code )

code 에 해당하는 관리구분 반환한다.

code : 주식코드
반환값 : 관리구분
typedef enum    {
[helpstring("일반종목")] CPC_SUPERVISION_NONE = 0,
[helpstring("관리")]    CPC_SUPERVISION_NORMAL = 1,
}CPE_SUPERVISION_KIND;

 

value = object. GetStockStatusKind ( code )

code 에 해당하는 주식상태를 반환한다

code : 주식코드
반환값 : 관리구분
typedef enum    {
[helpstring("정상")]    CPC_STOCK_STATUS_NORMAL = 0,
[helpstring("거래정지")] CPC_STOCK_STATUS_STOP = 1,
[helpstring("거래중단")] CPC_STOCK_STATUS_BREAK = 2,
}CPE_SUPERVISION_KIND;

 

value = object. GetStockCapital ( code )

code 에 해당하는 자본금규모구분 반환한다.

code : 주식코드
반환값 : 자본금규모구분
typedef enum {
[helpstring("제외")]   CPC_CAPITAL_NULL  = 0,
[helpstring("대")]   CPC_CAPITAL_LARGE  = 1,
[helpstring("중")]   CPC_CAPITAL_MIDDLE  = 2,
[helpstring("소")]   CPC_CAPITAL_SMALL  = 3
}CPE_CAPITAL_SIZE;

 

value = object. GetStockFiscalMonth ( code )

code 에 해당하는 결산기 반환한다.

code : 주식코드
반환값 : 결산기

 

value = object. GetStockGroupCode ( code )

code 에 해당하는 그룹(계열사)코드 반환한다.

code : 주식코드
반환값 : 그룹(계열사)코드

 

value = object. GetStockKospi200Kind ( code )

code 에 해당하는KOSPI200 종목여부 반환한다.

code : 주식코드
반환값 : KOSPI200 종목여부
typedef enum {
[helpstring("미채용")]      CPC_KOSPI200_NONE  = 0,
[helpstring("제조업")]      CPC_KOSPI200_MANUFACTURE = 1,
[helpstring("전기통신업")]   CPC_KOSPI200_TELECOMMUNICATION= 2,
[helpstring("건설업")]      CPC_KOSPI200_CONSTRUCT = 3,
[helpstring("유통업")]      CPC_KOSPI200_CURRENCY = 4,
[helpstring("금융업")]      CPC_KOSPI200_FINANCE = 5,
}CPE_KOSPI200_KIND;

2011년 4월 1일부터 아래 값으로 변경

typedef enum {
[helpstring("미채용")]    CPC_KOSPI200_NONE        = 0,
[helpstring("건설기계")] CPC_KOSPI200_CONSTRUCTIONS_MACHINERY = 1,
[helpstring("조선운송")] CPC_KOSPI200_SHIPBUILDING_TRANSPORTATION   = 2,
[helpstring("철강소재")] CPC_KOSPI200_STEELS_METERIALS         = 3,
[helpstring("에너지화학")] CPC_KOSPI200_ENERGY_CHEMICALS         = 4,
[helpstring("정보통신")] CPC_KOSPI200_IT     = 5,
[helpstring("금융")]    CPC_KOSPI200_FINANCE      = 6,
[helpstring("필수소비재")] CPC_KOSPI200_CUSTOMER_STAPLES         = 7,
[helpstring("자유소비재")] CPC_KOSPI200_CUSTOMER_DISCRETIONARY      = 8,
}CPE_KOSPI200_KIND;

 

value = object. GetStockSectionKind ( code )

code 에 해당하는 부 구분 코드를 반환한다

 code : 주식코드

 반환값 : 부 구분 코드

 typedef enum

 {

  [helpstring("구분없음")]   CPC_KSE_SECTION_KIND_NULL= 0,

    [helpstring("주권")]   CPC_KSE_SECTION_KIND_ST   = 1,

    [helpstring("투자회사")]   CPC_KSE_SECTION_KIND_MF    = 2,

  [helpstring("부동산투자회사"]   CPC_KSE_SECTION_KIND_RT    = 3,

  [helpstring("선박투자회사")]   CPC_KSE_SECTION_KIND_SC    = 4,

  [helpstring("사회간접자본투융자회사")] CPC_KSE_SECTION_KIND_IF = 5,

  [helpstring("주식예탁증서")]   CPC_KSE_SECTION_KIND_DR    = 6,

  [helpstring("신수인수권증권")]   CPC_KSE_SECTION_KIND_SW    = 7,

  [helpstring("신주인수권증서")]   CPC_KSE_SECTION_KIND_SR    = 8,

  [helpstring("주식워런트증권")]   CPC_KSE_SECTION_KIND_ELW = 9,

  [helpstring("상장지수펀드(ETF)")] CPC_KSE_SECTION_KIND_ETF = 10,

  [helpstring("수익증권")]    CPC_KSE_SECTION_KIND_BC    = 11,

  [helpstring("해외ETF")]      CPC_KSE_SECTION_KIND_FETF   = 12,

  [helpstring("외국주권")]    CPC_KSE_SECTION_KIND_FOREIGN = 13,

  [helpstring("선물")]      CPC_KSE_SECTION_KIND_FU    = 14,

  [helpstring("옵션")]      CPC_KSE_SECTION_KIND_OP    = 15,    

 } CPE_KSE_SECTION_KIND;

 

value = object. GetStockLacKind ( code )

code 에 해당하는 락구분 코드를 반환한다

 code : 주식코드

 반환값 : 락 구분 코드

 typedef enum

 {

  [helpstring("구분없음")] CPC_LAC_NORMAL = 0,

  [helpstring("권리락")] CPC_LAC_EX_RIGHTS   = 1,

  [helpstring("배당락")]   CPC_LAC_EX_DIVIDEND = 2,

  [helpstring("분배락")]   CPC_LAC_EX_DISTRI_DIVIDEND   = 3,

  [helpstring("권배락")]   CPC_LAC_EX_RIGHTS_DIVIDEND   = 4,

  [helpstring("중간배당락")] CPC_LAC_INTERIM_DIVIDEND   = 5,

  [helpstring("권리중간배당락")] CPC_LAC_EX_RIGHTS_INTERIM_DIVIDEND= 6,

  [helpstring("기타")]   CPC_LAC_ETC   = 99,

 } CPE_LAC_KIND;

 

value = object. GetStockListedDate ( code )

code 에 해당하는 상장일을 반환한다

code : 주식코드
반환값 : 상장일 (LONG)

 

value = object. GetStockMaxPrice ( code )

code 에 해당하는 상한가를 반환한다

code : 주식코드
반환값 : 상한가(LONG)

 

value = object. GetStockMinPrice ( code )

code 에 해당하는 하한가를 반환한다

code : 주식코드
반환값 : 하한가(LONG)

 

value = object. GetStockParPrice ( code )

code 에 해당하는 액면가를 반환한다

code : 주식코드
반환값 : 액면가(LONG)

 

value = object. GetStockStdPrice ( code )

code 에 해당하는 권리락 등으로 인한 기준가를 반환한다

code : 주식코드
반환값 : 기준가(LONG)

 

value = object. GetStockYdOpenPrice ( code )

code 에 해당하는 전일 시가를 반환한다

code : 주식코드
반환값 : 전일 시가(LONG)

 

value = object. GetStockYdHighPrice ( code )

code 에 해당하는 전일 고가를 반환한다

code : 주식코드
반환값 : 전일고가(LONG)

 

value = object. GetStockYdLowPrice ( code )

code 에 해당하는 전일 저가를 반환한다

code : 주식코드
반환값 : 전일저가(LONG)

 

value = object. GetStockYdClosePrice ( code )

code 에 해당하는 전일종가를 반환한다

code : 주식코드
반환값 : 전일종가(LONG)

 

value = object. IsStockCreditEnable ( code )

code 에 해당하는 신용가능종목 여부를 반환한다

code : 주식코드
반환값 : 신용여부 (BOOL)

 

value = object. GetStockParPriceChageType ( code )

code 에 해당하는 액면정보 코드를 반환한다

 code : 주식코드

 반환값 : 액면정보 코드

 typedef enum

   {

   [helpstring("해당없음")]   CPC_PARPRICE_CHANGE_NONE   = 0,

 [helpstring("액면분할")]   CPC_PARPRICE_CHANGE_DIVIDE   = 1,   

 [helpstring("액면병합")]   CPC_PARPRICE_CHANGE_MERGE   = 2,   

 [helpstring("기타")]   CPC_PARPRICE_CHANGE_ETC = 99,

 }CPE_ECT_PARPRICE_CHANGE;

 

[Basket 정보]
아래 두 함수는 CpElwCode에도 동일한 함수명으로 존재합니다.

기존 사용 고객님을 위해서CpElwCode/CpCodeMgr 2군데서 제공합니다.

value = object.GetStockElwBasketCodeList( code )

Elw 기초자산 코드 리스트 얻기 (바스켓)

반환값 : 입력한 코드에 해당하는 바스켓코드리스트(배열)

 

value = object.GetStockElwBasketCompList( code )

Elw 기초자산 비율 리스트 얻기 (바스켓)

반환값 : 입력한 코드에 해당하는 바스켓비율리스트(배열)

 

[각종 코드리스트]

value = object.GetStockListByMarket(CPE_MARKET_KIND code )

시장구분에 따른 주식종목배열을 반환하다

반환값: 입력한 시장구분(CPE_MARKET_KIND)에 해당하는 종목리스트(배열)

 VB ex)

 Dim WorkKey As New CpTdUtil

 Dim codes As Variant

   codes = CodeMgr. GetStockListByMarket (CPC_MARKET_KOSPI) ' 거래소

 For i = LBound(codes) To UBound(codes)

  Debug.Print codes(i)

  Debug.Print CodeMgr. CodeToName(codes(i))

 Next

 VC++ ex)

 ICpCodeMgrPtr codeMgr;

 codeMgr.CreateInstance(_uuidof(CpCodeMgr));

 

 variant_t vArray, vItem;

 CComSafeArray<VARIANT> sa; 

 vArray = codeMgr->GetIndustryList();

 sa.Attach(vArray.Detach().parray);

 for (LONG nlb = sa.GetLowerBound(), nub = sa.GetUpperBound(); nlb <= nub; nlb++)

 {
  vItem = sa.GetAt(nlb);
  _tprintf(_T("%s\n"), (LPCTSTR)(bstr_t)vItem);

 }

 

value = object.GetGroupCodeList( code )

관심종목(700 ~799 ) 및 업종코드(GetIndustryList 참고)에 해당하는 종목배열을 반환한다

반환값 : 입력한 그룹에 해당하는 종목리스트(배열)

 VB ex)

 Dim CodeMgr As New CpCodeMgr

 Dim codes As Variant

   codes = CodeMgr. GetGroupCodeList (24) ' 24 증권업

 For i = LBound(codes) To UBound(codes)

  Debug.Print codes(i)

 Next

value = object. GetGroupName ( code )

관심종목(700 ~799 ) 및 업종코드에 해당하는 명칭을 반환한다

반환값 : 관심종목명 및 업종코드명

 

object. GetIndustryList ()

증권전산업종 코드 리스트를 반환한다.

반환값 : 증권전산업종코드(배열)

 VB ex)

 Dim CodeMgr As New CpCodeMgr

 Dim codes As Variant

   codes = CodeMgr.GetIndustryList ()

   For i = LBound(codes) To UBound(codes)

  Debug.Print codes(i)

 Next

value = object. GetIndustryName ( code )

증권전산업종코드에 해당하는 증권전산업종명을 반환한다

반환값 : 증권전산업종명

 

object. GetMemberList ( )

거래원코드(회원사)의 코드리스트를 반환한다.

반환값 : 거래원코드코드(배열)

value = object. GetMemberName ( code )

거래원코드(회원사)코드에 해당하는 거래원코드명을 반환한다

반환값 : 거래원코드명

 

object. GetKosdaqIndustry1List ()

코스닥산업별 코드리스트를 반환한다.

반환값 : 코스닥산업별코드(배열)

object. GetKosdaqIndustry2List ()

코스닥지수업종 코드리스트를 반환한다.

반환값 : 코스닥지수별코드(배열)

 VB ex)

 Dim CodeMgr As New CpCodeMgr

 Dim codes As Variant

   codes = CodeMgr. GetKosdaqIndustry2List ()

   For i = LBound(codes) To UBound(codes)

  Debug.Print codes(i)

 Next

 

[기타 정보]

value = object. GetMarketStartTime ()

장 시작 시각 얻기 (ex 9시일경우 리턴값 9)

반환값 :장시작 시각 

value = object. GetMarketEndTime ()

장 마감 시각 얻기 (ex오후 3시일경우 리턴값 15)

반환값 : 장마감 시각 

 
StockMst2

설명

주식 복수 종목에 대해 일괄 조회를 요청하고 수신한다

통신종류

Request/Reply

연속여부

X

관련 SB/PB

StockCur

관련CYBOS

[7059 관심종목조회]

모듈 위치

cpdib.dll

Method
object.SetInputValue(type,value)

type에 해당하는 입력 데이터를 value 값으로 지정합니다

type: 입력 데이터 종류

0 - (string) 다수의 종목코드(구분자:',' , MAX: 110종목) 예) A003540,A000060,A000010

value: 새로 지정할 값

value = object.GetHeaderValue(type)

type에 해당하는 헤더 데이터를 반환합니다

type: 데이터 종류

0 - (short) count

반환값: 데이터 종류에 해당하는 값

value = object.GetDataValue(Type,Index)

type에 해당하는 데이터를 반환합니다

type: 데이터 종류

0 - (string) 종목 코드

1 - (string) 종목명

2 - (long) 시간(HHMM)

3 - (long) 현재가

4 - (long) 전일대비

5 - (char) 상태구분

코드

내용

'1'

상한

'2'

상승

'3'

보합

'4'

하한

'5'

하락

'6'

기세상한

'7'

기세상승

'8'

기세하한

'9'

기세하락

6 - (long) 시가

7 - (long) 고가

8 - (long) 저가

9 - (long) 매도호가

10 - (long) 매수호가

11 - (unsigned long) 거래량 [주의] 단위 1주

12 - (long) 거래대금 [주의] 단위 천원

13 - (long) 총매도잔량

14 - (long) 총매수잔량

15 - (long) 매도잔량

16 - (long) 매수잔량

17 - (unsigned long) 상장주식수

18 - (long) 외국인보유비율(%)

19 - (long) 전일종가

20 - (unsigned long) 전일거래량

21 - (long) 체결강도

22 - (unsigned long) 순간체결량

23 - (char) 체결가비교 Flag

코드

내용

'O'

매도

'B'

매수

24 - (char) 호가비교 Flag

코드

내용

'O'

매도

'B'

매수

25- (char) 동시호가구분

코드

내용

'1'

동시호가

'2'

장중

26 - (long) 예상체결가

27 - (long) 예상체결가 전일대비

28 - (long) 예상체결가 상태구분

코드

내용

'1'

상한

'2'

상승

'3'

보합

'4'

하한

'5'

하락

'6'

기세상한

'7'

기세상승

'8'

기세하한

'9'

기세하락

29- (unsigned long) 예상체결가 거래량

index: data index

반환값: 데이터 종류의 index번째 data

object.Subscribe()

사용하지 않음

object.Unsubscribe()

사용하지 않음

object.Request()

다수의 종목 코드에 해당하는 데이터를 요청한다

object.BlockRequest()

데이터 요청.Blocking Mode

Event
Object.Received

다수의 종목코드 데이터를 수신할 때 발생하는 이벤트


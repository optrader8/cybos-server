StockMstM

설명

주식 복수 종목에 대해 간단한 내용을 일괄 조회 요청하고 수신한다

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

0 - (string) 다수의 종목코드
ex) A003540A000060A000010 (MAX:110개)

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

2 - (long) 대비

3 - (shot) 대비 구분 코드

코드

내용

1

상한

2

상승

3

보합

4

하한

5

하락

6

기세상한

7

기세상승

8

기세하한

9

기세하락

4 - (long) 현재가

5 - (long) 매도호가

6 - (long) 매수호가

7 - (unsigned long) 거래량

8 - (char) 장 구분 플래그

코드

내용

'0'

동시호가와 장중이외의 시간

'1'

동시호가시간(예상체결가 들어오는 시간)

'2'

장중

9 - (long) 예상 체결가

10 - (long) 예상 체결가 전일 대비

11 - (unsigned long) 예상 체결 수량

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


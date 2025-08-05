CpCybos

설명: CYBOS의 각종 상태를 확인할 수 있음.

모듈위치: CpUtil.dll

Property

value = object.IsConnect

(읽기전용) CYBOS의 통신 연결상태를 반환 합니다

반환값: 0- 연결 끊김, 1- 연결 정상


Python ex)
>>> import win32com.client
>>> inCpCybos = win32com.client.Dispatch("CpUtil.CpCybos")
>>> if inCpCybos.IsConnect == 1:
           print("연결 정상")
       else:
           print("연결 끊김") 

value = object.ServerType

(읽기전용) 연결된 서버 종류를 반환합니다

반환값: 0- 연결 끊김, 1- cybosplus 서버, 2- HTS 보통서버(cybosplus 서버 제외)

value = object.LimitRequestRemainTime

(읽기전용) 요청 개수를 재계산하기까지 남은 시간을 반환합니다. 즉 리턴한 시간동안 남은 요청개수보다 더 요청하면 요청제한이 됩니다.

반환값: 요청 개수를 재계산하기까지 남은 시간(단위:milisecond)

Method

value = object.GetLimitRemainCount(limitType)

limitType에 대한 제한을 하기까지 남은 요청개수를 반환합니다.

limitType: 요쳥에 대한 제한타입

LT_TRADE_REQUEST - 주문관련 RQ 요청

LT_NONTRADE_REQUEST - 시세관련 RQ 요청

LT_SUBSCRIBE - 시세관련 SB

반환값: 제한을 하기 전까지의 남은 요청개수

Event

Object.OnDisConnect

U-CYBOS의 통신 연결상태가 끊긴 경우에 이벤트가 발생합니다.

이 이벤트를 받은 후에는 더 이상 데이터 통신이 불가능합니다.

가능한 프로그램을 정리하고  안전하게 종료하도록 프로그램을 작성해야 합니다.


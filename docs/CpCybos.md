네, 알겠습니다. 제공해주신 `CpCybos` API 명세서를 이전과 동일한 형식으로 명확하게 재구성하여 보여드리겠습니다.

-----

# API 명세서: CpCybos

## 1\. 개요

`CpCybos`는 CYBOS의 통신 연결 상태, 서버 종류, API 요청 제한 등 시스템의 전반적인 상태를 확인하기 위한 COM 객체입니다.

  - **주요 기능**: CYBOS 연결 상태 확인, API 요청 가능 횟수 조회, 연결 끊김 이벤트 처리
  - **모듈 위치**: `CpUtil.dll`

## 2\. Property (속성)

속성은 읽기 전용(Read-only)으로 현재 상태 값을 반환합니다.

| 속성 | 설명 | 반환값 |
| :--- | :--- | :--- |
| `object.IsConnect` | CYBOS의 통신 연결 상태를 반환합니다. | **0**: 연결 끊김\<br\>**1**: 연결 정상 |
| `object.ServerType` | 연결된 서버의 종류를 반환합니다. | **0**: 연결 끊김\<br\>**1**: cybosplus 서버\<br\>**2**: HTS 보통서버(cybosplus 서버 제외) |
| `object.LimitRequestRemainTime` | API 요청 가능 횟수를 재계산하기까지 남은 시간을 밀리초(ms) 단위로 반환합니다. | `long` (남은 시간, ms) |

**`IsConnect` 예제 코드:**

```python
import win32com.client
inCpCybos = win32com.client.Dispatch("CpUtil.CpCybos")
if inCpCybos.IsConnect == 1:
    print("연결 정상")
else:
    print("연결 끊김")
```

## 3\. Method (메서드)

| 메서드 | 설명 |
| :--- | :--- |
| `object.GetLimitRemainCount(limitType)` | `limitType`에 지정된 요청 종류에 대해, API 제한에 도달하기까지 남은 요청 개수를 반환합니다. |

**파라미터 (`limitType`)**
| `limitType` 값 | 설명 |
| :--- | :--- |
| `LT_TRADE_REQUEST` | 주문 관련 Request/Reply 요청 |
| `LT_NONTRADE_REQUEST` | 시세 관련 Request/Reply 요청 |
| `LT_SUBSCRIBE` | 시세 관련 Subscribe/Publish 요청 |

**반환값**: 남은 요청 개수

## 4\. Event (이벤트)

### 4.1. `Object.OnDisConnect`

CYBOS의 통신 연결이 끊겼을 때 발생하는 이벤트입니다.

  - 이 이벤트가 발생하면 더 이상 데이터 통신이 불가능합니다.
  - 프로그램을 안전하게 정리하고 종료하는 로직을 이 이벤트 핸들러 내에 작성해야 합니다.
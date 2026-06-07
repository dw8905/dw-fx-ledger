# FX Core Logic Flow

이 문서는 DW FX Ledger의 FX 핵심 비즈니스 로직 흐름을 순서도로 정리한다.
기준 구현은 `apps/api/app/services/fx.py`이며, DB 스키마는 변경하지 않는다.

## 핵심 상태

```mermaid
stateDiagram-v2
    [*] --> open: buy lot 생성
    open --> split: 매도 차감 대상
    split --> sold: 매도 배정분 closed lot 생성
    split --> open: 잔여분 remaining lot 생성
    sold --> cancelled: 매도 취소
    open --> cancelled: 잔여 lot 취소
    cancelled --> open: 원 source lot 기준 restored lot 생성
```

| 상태 | 의미 |
| --- | --- |
| `open` | 매도에 사용할 수 있는 활성 매수 로트 |
| `split` | 매도 배정으로 닫힌 원본/source 로트 |
| `sold` | 매도된 배정분 closed 로트 |
| `cancelled` | 삭제 또는 매도 취소로 비활성화된 로트 |

## 매수 로트 생성

```mermaid
flowchart TD
    A["POST /fx/buy-lots"] --> B["buyDate, buyKrwAmount, buyExchangeRate 입력"]
    B --> C["buyExchangeRate 6자리 정규화"]
    C --> D["usdAmount = buyKrwAmount / buyExchangeRate"]
    D --> E["fx_buy_lots 생성"]
    E --> F["lot_status = open"]
    F --> G["is_active = true, is_deleted = false"]
    G --> H["root_buy_lot_id = 자기 buy_lot_id"]
```

## 매도 차감 전략 선택

```mermaid
flowchart TD
    A["POST /fx/sell-transactions"] --> B{"allocationStrategy"}
    B -->|"highest_rate_first"| C["open lot을 매수환율 높은순, 매수일 오래된순으로 잠금 조회"]
    B -->|"fifo"| D["open lot을 매수일 오래된순으로 잠금 조회"]
    B -->|"lifo"| E["open lot을 매수일 최신순으로 잠금 조회"]
    B -->|"manual"| F["사용자가 지정한 buyLotId/USD 금액 검증 후 잠금 조회"]
    C --> G["AllocationPlan 생성"]
    D --> G
    E --> G
    F --> H["수동 배정 합계가 sellUsdAmount와 같은지 검증"]
    H --> G
```

## 매도 로트 분할 및 배정

```mermaid
flowchart TD
    A["매도 입력값 정규화"] --> B["sellUsdAmount, sellExchangeRate"]
    B --> C["차감 대상 open lot 순회"]
    C --> D["allocatedUsd = min(source.usdAmount, 남은 매도 USD)"]
    D --> E["allocatedBuyKrw = allocatedUsd * source.buyExchangeRate 올림"]
    E --> F["allocatedSellKrw = allocatedBuyKrw * sellRate / buyRate 올림"]
    F --> G["realProfit = allocatedSellKrw - allocatedBuyKrw"]
    G --> H["displayProfit = max(realProfit, 0)"]
    H --> I["remainingUsd / remainingBuyKrw 계산"]
    I --> J{"매도 USD 전부 배정됨?"}
    J -->|"아니오"| C
    J -->|"예"| K["fx_sell_transactions 생성"]
    K --> L["sell_transaction_created 이벤트 기록"]
    L --> M["각 AllocationPlan 반영"]
    M --> N["source lot: split, inactive"]
    N --> O["closed sold lot 생성"]
    O --> P{"잔여 USD/KRW 있음?"}
    P -->|"예"| Q["remaining open lot 생성"]
    P -->|"아니오"| R["remaining lot 없음"]
    Q --> S["fx_lot_allocations 생성"]
    R --> S
    S --> T["lot_split 이벤트 기록"]
```

## 매도 취소 및 로트 복원

```mermaid
flowchart TD
    A["POST /fx/sell-transactions/{id}/cancel"] --> B["매도 거래 잠금 조회"]
    B --> C{"transaction_status == completed?"}
    C -->|"아니오"| X["409 오류"]
    C -->|"예"| D["allocation 목록 잠금 조회"]
    D --> E{"remaining lot이 이후 매도 source로 사용됨?"}
    E -->|"예"| Y["최신 체인 매도만 취소 가능: 409 오류"]
    E -->|"아니오"| F["transaction_status = cancelled"]
    F --> G["sell_transaction_cancelled 이벤트 기록"]
    G --> H["각 allocation 복원 처리"]
    H --> I["closed sold lot = cancelled"]
    I --> J{"remaining lot 있음?"}
    J -->|"예"| K["remaining lot = cancelled"]
    J -->|"아니오"| L["잔여 lot 처리 생략"]
    K --> M["source lot 원금/USD 기준 restored open lot 생성"]
    L --> M
    M --> N["lot_restored 이벤트 기록"]
```

## FX 원장 조회

```mermaid
flowchart TD
    A["GET /fx/ledger?period="] --> B["활성 open lot 조회"]
    A --> C["completed sell transaction + sold closed lot + allocation 조회"]
    B --> D["open_rows 생성: profitKrw = 0"]
    C --> E["sold_rows 생성: allocation.display_profit_krw 사용"]
    D --> F["open_rows + sold_rows 병합"]
    E --> F
    F --> G["buyDate, createdAt, buyLotId 기준 정렬"]
    G --> H["행 순회하며 cumulativeProfitKrw 계산"]
    H --> I["양수 환율차 평균 exchangeDiffAverage 계산"]
    I --> J["latestLedgerDate = 표시 기준일 최대값"]
    J --> K["period에 맞는 visible_items 필터"]
    K --> L["totalDisplayProfitKrw = visible_items의 profitKrw 합계"]
    H --> M["finalCumulativeProfitKrw = 전체 items 기준 최종 누적손익"]
    L --> N["LedgerResponse 반환"]
    M --> N
```

## 원장 기간 필터 기준

```mermaid
flowchart TD
    A["원장 행"] --> B{"sellDate 있음?"}
    B -->|"예"| C["기준일 = sellDate"]
    B -->|"아니오"| D["기준일 = buyDate"]
    C --> E{"period"}
    D --> E
    E -->|"all"| F["항상 표시"]
    E -->|"latest"| G["기준일 == latestLedgerDate"]
    E -->|"1y / 3y / 5y"| H["기준일 >= latestLedgerDate - N년"]
```

## 수익 계산 기준

| 항목 | 계산 기준 |
| --- | --- |
| `realProfitKrw` | 실제 배정 매도원화 - 배정 매수원화 |
| `displayProfitKrw` | `max(realProfitKrw, 0)` |
| `totalRealProfitKrw` | 완료된 전체 매도 거래의 실제 손익 합계 |
| `totalDisplayProfitKrw` | 현재 기간 필터에 표시된 원장 행의 표시손익 합계 |
| `finalCumulativeProfitKrw` | 기간 필터와 무관한 전체 원장 기준 최종 누적손익 |
| `exchangeDiff` | `max(sellExchangeRate - buyExchangeRate, 0)` |
| `exchangeDiffAverage` | 원장 정렬 순서상 양수 환율차의 누적 평균 |

## 주요 테이블 관계

```mermaid
erDiagram
    fx_buy_lots ||--o{ fx_buy_lots : "parent/root"
    fx_sell_transactions ||--o{ fx_lot_allocations : "has"
    fx_buy_lots ||--o{ fx_lot_allocations : "source"
    fx_buy_lots ||--o{ fx_lot_allocations : "closed"
    fx_buy_lots ||--o{ fx_lot_allocations : "remaining"
    fx_sell_transactions ||--o{ fx_lot_events : "records"
    fx_lot_allocations ||--o{ fx_lot_events : "records"
    fx_buy_lots ||--o{ fx_lot_events : "records"
```

# GPT Context Summary

이 문서는 DW FX Ledger 프로젝트를 다른 GPT/AI 세션에 넘길 때 사용하는 짧은 인수인계 문서입니다.

기능 설명, 실행 방법, 테스트 방법, 주요 화면, DB 주요 테이블, 제한사항은 `README.md`를 1차 기준으로 봅니다. 이 파일은 README를 대체하는 전체 문서가 아니라, 다음 AI 세션이 특히 놓치면 안 되는 현재 작업 맥락과 주의사항만 압축해서 담습니다.

## 먼저 읽을 문서

1. `README.md`
2. `docs/table-spec.md`
3. `docs/fx-core-flow.md`
4. 필요 시 `docs/table-spec.csv`

## 현재 용어 기준

- 사용자 노출 명칭은 `자산관리`, `자산`, `자산 코드`를 사용합니다.
- 내부 라우트/API/DB/타입 이름은 기존 호환을 위해 `item-trades`, `item_codes`, `item_trades`, `ItemTrade` 계열을 유지합니다.
- Admin 화면은 `/admin/item-codes` 경로를 유지하지만 화면 표기는 `자산 코드 관리`입니다.
- Web 화면은 `/item-trades?tab=buy|sell|inventory` 경로를 유지하지만 화면 표기는 `자산관리`입니다.

## 메뉴와 탭 구조

- 상단 메뉴는 `게시판`, `FX`, `자산관리` 중심입니다.
- FX 하위 화면은 `/fx/layout.tsx`에서 공통 탭을 렌더링합니다.
- FX 통계 화면은 `/fx/stats`이며 Recharts 기반으로 누적수익 추이, 월별 실현손익, Open 로트 환율 분포를 보여줍니다.
- FX 통계의 누적수익 차트는 전체 KRW, USD, JPY 선을 겹쳐 표시하며 범례 버튼으로 각 선을 토글할 수 있고 차트 높이는 드래그로 조절할 수 있습니다.
- FX 원장 화면은 `/fx/ledger`이며 현재 표시된 그리드를 CSV로 추출할 수 있습니다.
- 자산관리 하위 탭은 `SectionTabs` 공통 컴포넌트를 사용합니다.
- 브레드크럼은 `DW FX Ledger > FX > 매수`, `DW FX Ledger > 자산관리 > 매도`처럼 현재 섹션과 탭을 표시합니다.

## 핵심 비즈니스 주의사항

- FX 매수/매도/취소는 원본 row를 직접 줄이거나 삭제하지 않고 lot 계보와 event로 추적합니다.
- FX 중간 매도 단독 취소는 금지입니다. root lot 계보 기준 최신 매도부터만 취소할 수 있습니다.
- FX 원장의 표시손익 합계는 기간 필터 안의 표시 행 기준이고, 최종 누적손익은 전체 흐름 기준입니다.
- FX 원장/통계는 `currency_code`로 USD/JPY를 구분하고, 수익 금액은 KRW 기준이라 전체 보기에서 합산할 수 있습니다.
- 게시판은 `board_posts.board_type_code`와 `common_codes(code_group='board_type')`로 타입을 구분합니다. 기본 타입은 `general`입니다.
- 자산 재고 수량도 직접 update하지 않고 `adjustment` 거래 insert로 관리합니다.
- 자산 매수 수수료율은 실제 매수 원가가 아니라 향후 판매 수수료 기준값입니다.
- 자산 최소 이득 판매가는 `ceil(평균단가 / (1 - 수수료율))`입니다.
- 기존 0% 수수료 데이터는 재고관리 최소판매가 계산 시 기본 5%로 보정합니다.

## 테스트/운영 메모

```bash
cd apps/api
uv run pytest -q
uv run pytest -q tests/test_item_trades_api.py
uv run pytest -q tests/test_admin_api.py::test_admin_item_codes_crud_and_regular_user_forbidden
```

```bash
pnpm --filter @dw-fx-ledger/web typecheck
pnpm --filter @dw-fx-ledger/web build
pnpm --filter @dw-fx-ledger/admin typecheck
pnpm --filter @dw-fx-ledger/admin build
```

- `pnpm start`, `pnpm stop`, `pnpm status`, `pnpm restart`는 API/Web/Admin을 통합 관리합니다.
- Next build 후에는 dev 서버의 `.next` 캐시 혼선을 막기 위해 `pnpm restart`로 다시 띄우는 편이 안전합니다.
- Recharts 사용으로 `/fx/stats` 번들이 커졌으므로, 더 최적화가 필요하면 stats 차트 영역을 dynamic import로 분리합니다.
- 테스트가 dev DB를 오염시키지 않도록 자산 코드 테스트 데이터 cleanup을 유지해야 합니다.

## 현재 알려진 정리 필요 항목

- 기존 dev DB에 중복 자산 코드가 남아 있을 수 있습니다.
- 거래 기록이 연결된 자산 코드는 단순 삭제하면 참조가 깨질 수 있으므로 병합 기준과 정리 도구가 필요합니다.
- 스키마/라우트명을 `asset_*`로 바꾸는 작업은 migration과 호환성 영향이 크므로 별도 큰 작업으로 분리하는 것이 좋습니다.

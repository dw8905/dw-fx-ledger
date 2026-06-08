# GPT Context Summary

이 문서는 DW FX Ledger 프로젝트 상태를 다른 GPT/AI 세션에 전달하기 위한 복붙용 요약입니다.

## 프로젝트 개요

- 프로젝트명: DW FX Ledger
- 경로: `/home/dw/projects/dw-fx-ledger`
- 목적: FX 매수/매도 로트 기반 환차익 원장 관리 + 아이템 거래 손익/재고 관리
- 구조:
  - `apps/api`: FastAPI, SQLAlchemy, Alembic, pytest
  - `apps/web`: 사용자용 Next.js 앱
  - `apps/admin`: 관리자용 Next.js 앱
  - `packages/shared`: 공유 TS 패키지
- 인증: HttpOnly Cookie 기반 JWT Access/Refresh Token
- DB: PostgreSQL
- 패키지 매니저:
  - JS: `pnpm`
  - Python: `uv`

## 실행 명령

통합 dev 서버:

```bash
pnpm start
pnpm status
pnpm stop
pnpm restart
```

서비스:

- API: `http://127.0.0.1:8000`
- API Docs: `http://127.0.0.1:8000/docs`
- Web: `http://localhost:3000`
- Admin: `http://localhost:3001`

로그:

- `.dev/logs/api.log`
- `.dev/logs/web.log`
- `.dev/logs/admin.log`

주의:

- `pnpm restart`는 pnpm lifecycle 때문에 `pre/post`처럼 동작할 수 있어 root `package.json`에서 중간 `restart` 스크립트는 `true`로 둔다.
- `pnpm start`는 기존 포트 점유 프로세스 정리 후 `.next`를 삭제하고 API/Web/Admin을 백그라운드로 띄운다.

## 주요 테스트 명령

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

## FX 핵심 규칙

- FX 매수 로트는 `fx_buy_lots`에 저장한다.
- 부분매도 시 원본 lot을 직접 줄이지 않는다.
- 매도 처리 흐름:
  - source lot을 `split` 상태로 비활성화
  - sold lot 생성
  - remaining open lot 생성
  - allocation 생성
  - lot event 기록
- 매도 취소는 반대 이벤트를 만드는 방식이다.
- 중간 매도 단독 취소는 금지한다.
- root lot 계보 기준 최신 매도부터만 취소 가능하다.
- 원장은 `/fx/ledger`에서 엑셀형으로 조회한다.
- 원장 날짜 표기는 `YYMMDD` 형식이다.
- 원장 기간 필터에서 표시손익 합계는 기간 내 표시 행 기준이고, 최종 누적손익은 전체 흐름 기준이다.

## FX 지원 기능

- 상단 메뉴는 `FX` 하나로 묶고, 내부 탭에서 매수/매도/원장/Lab을 이동한다.
- `/fx`는 `/fx/buy-lots`로 redirect한다.
- 매수 로트 등록/수정/삭제
- 매도 등록
- 매도 차감 전략:
  - `highest_rate_first`
  - `fifo`
  - `lifo`
  - `manual`
- 매도 취소
- lot event 조회
- FX Dev Lab
- 사용자별 Admin 원장 조회

## Admin 상태

- admin role 기반 권한 체계 구현됨.
- `require_admin` dependency 있음.
- Admin read-only MVP 구현됨.
- 주요 Admin 페이지:
  - `/admin/users`
  - `/admin/users/[userId]`
  - `/admin/posts`
  - `/admin/fx/ledger?userId=`
  - `/admin/fx/events`
  - `/admin/item-codes`
- Admin API는 `/admin` prefix.
- Admin에서 FX 장부 수정/삭제는 금지 상태.
- Admin 아이템 코드 마스터는 등록/수정/비활성화 가능.
- 아이템 코드는 내부적으로 `ITEM-000001` 형식 자동 생성.
- 아이템명 중복 등록/수정은 API에서 409로 차단.

## 아이템 거래 기능

사용자 Web 경로:

- `/item-trades`

탭:

- 매수
- 매도
- 아이템별 재고관리

아이템 마스터:

- `item_codes`는 전역 관리자 마스터다.
- Web에서는 사용자가 코드를 직접 입력하지 않고 활성 아이템명을 자동완성으로 선택한다.
- Admin에서 아이템명만 입력하면 내부 코드가 자동 생성된다.

거래 테이블:

- `item_trades`
- `trade_type`:
  - `buy`
  - `sell`
  - `adjustment`
- `trade_status`:
  - `active`
  - `cancelled`

평균단가/재고 규칙:

- 평균단가 방식으로 재고 원가와 손익을 계산한다.
- 매수 수수료율 기본값은 5%지만, 실제 매수 원가에 수수료를 더하지 않는다.
- 매수 수수료율은 향후 판매 수수료 기준값으로 저장한다.
- 매도 수수료는 실제 판매 금액에서 차감한다.
- 최소 이득 판매가:
  - `ceil(평균단가 / (1 - 수수료율))`
- 기존 0% 수수료 데이터는 재고관리 최소판매가 계산 시 기본 5%로 보정한다.

재고 조정:

- 재고관리에서 수량을 직접 update하지 않는다.
- 실제 보유 수량을 입력하면 현재 수량과의 차이를 계산해 `adjustment` 거래를 insert한다.
- 예:
  - 현재 78개, 실제 80개 입력 → `quantity = +2`
  - 현재 78개, 실제 70개 입력 → `quantity = -8`
- 증가 조정은 입력 단가로 재고 원가 증가.
- 감소 조정은 현재 평균단가로 재고 원가 차감.
- 조정 기록은 취소 가능하고, 취소 시 해당 아이템의 active 거래 기준으로 재계산한다.

## 최근 이슈와 조치

1. 테스트가 실제 dev DB의 관리자 아이템 코드 API를 타면서 같은 이름의 아이템 코드가 계속 생겼다.
   - 원인: 테스트 헬퍼가 매번 `/admin/item-codes` POST로 신규 코드 생성.
   - 조치:
     - 아이템 거래 테스트는 `[TEST] ...` 이름을 사용하고 테스트 종료 후 관련 `item_trades`, `item_codes` 삭제.
     - 관리자 아이템 코드 등록/수정 시 같은 이름 중복을 409로 차단.

2. 기존 중복 아이템 코드가 DB에 남아 있다.
   - 확인된 중복:
     - `디바인스톤`: 25개
     - `카오스코어`: 6개
     - `중복`: 2개
     - `디바인 스톤`: 2개
   - 일부는 거래 기록이 연결되어 있어 단순 삭제하면 참조가 깨질 수 있다.
   - 추후 병합 기준을 정해 정리 도구를 만들어야 한다.

3. Next dev 서버 오류:
   - `Cannot find module './437.js'`, `.next/server/*manifest.json ENOENT`
   - 원인: 기존 Next 프로세스가 포트를 점유한 상태에서 `.next`가 삭제됨.
   - 조치:
     - `scripts/dev-start.sh`, `dev-stop.sh`, `dev-status.sh` 개선.
     - 포트 기준으로 실제 listener PID를 정리/기록.
     - start 전에 `.next` 삭제.

## 문서

- README: `README.md`
- 테이블 명세 Markdown: `docs/table-spec.md`
- 테이블 명세 CSV: `docs/table-spec.csv`
- FX 핵심 로직 순서도: `docs/fx-core-flow.md`
- GPT 요약: `docs/gpt-context-summary.md`

## 작업 시 주의

- DB 스키마 변경은 꼭 필요할 때만 하고 Alembic migration을 같이 작성한다.
- FX 장부의 매수/매도/취소 로직은 이벤트와 계보가 중요하므로 직접 update/delete를 피한다.
- 아이템 재고 수량도 직접 update하지 말고 `adjustment` insert로 관리한다.
- 테스트가 dev DB를 오염시키지 않도록 테스트 데이터 cleanup을 신경 써야 한다.
- 기존 중복 item code는 거래 참조 여부 확인 후 정리해야 한다.

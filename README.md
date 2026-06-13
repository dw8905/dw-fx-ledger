# DW FX Ledger

FX Ledger는 외화 매수/매도 로트를 관리하고 환차익을 계산하는 서비스입니다.

매수 로트 등록부터 부분매도, 다중 로트 차감, 매도 취소, 이벤트 이력, 엑셀형 원장 조회까지 지원합니다. 추가로 게임/마켓 자산 매수·매도·재고 조정 기록을 평균단가 방식으로 관리하는 자산관리 기능과 read-only 중심 Admin 사이트를 포함합니다.

## 기술 스택

Frontend

- Next.js
- TypeScript
- Recharts
- pnpm workspace

Backend

- FastAPI
- SQLAlchemy
- Alembic
- uv

DB

- PostgreSQL

Dev Runtime

- 로컬 직접 실행: pnpm, uv
- 컨테이너 실행: Docker Compose, Python 3.12 API 컨테이너, Node.js 22 Web/Admin 컨테이너

Auth

- HttpOnly Cookie 기반 JWT Access Token / Refresh Token

## 모노레포 구조

```text
apps/
  web/      # 사용자용 Next.js 앱
  admin/    # 관리자용 Next.js 앱
  api/      # FastAPI 백엔드

packages/
  shared/   # 공유 TypeScript 패키지
```

- `apps/web`: 로그인, 게시판, FX 매수/매도/원장/Dev Lab, 자산관리 화면을 제공합니다.
- `apps/admin`: 관리자 로그인, 사용자/게시글/FX 원장/이벤트/자산 코드 관리 화면을 제공합니다.
- `apps/api`: 인증, 게시판, FX, 자산관리, Admin API, SQLAlchemy 모델, Alembic migration, pytest를 포함합니다.
- `packages/shared`: web/admin에서 공유할 TypeScript 코드의 위치입니다.

## 구현 완료 기능

인증

- 회원가입
- 로그인
- 로그아웃
- 토큰 재발급
- 현재 사용자 조회
- HttpOnly Cookie 기반 인증 유지

게시판

- 게시글 목록
- 게시글 상세
- 게시글 작성
- 게시글 수정
- 게시글 삭제
- 댓글 목록
- 댓글 작성
- 댓글 삭제
- 조회수 증가
- `common_codes`의 `board_type` 코드로 게시판 타입을 구분합니다.
- 기본 게시판 타입은 `general`이며, 타입별 목록 필터와 작성/수정 선택을 지원합니다.

FX 매수

- 상단 메뉴에서는 `FX` 하나로 진입하고, FX 내부 공통 탭에서 매수/매도/원장/Lab을 이동합니다.
- FX 하위 화면의 탭은 `/fx/layout.tsx`에서 공통으로 렌더링합니다.
- 매수 로트 등록
- 매수 로트 수정
- 매수 로트 삭제
- 삭제는 hard delete가 아니라 soft delete로 처리합니다.

FX 매도

- 부분매도
- 다중 로트 차감
- `highest_rate_first`
- `fifo`
- `lifo`
- `manual allocation`

매도 취소

- 최신 매도만 취소 가능
- 연속 취소 가능
- 중간 매도 단독 취소 불가

이벤트

- `fx_lot_events`에 매도 생성, 로트 분할, 매도 취소, 로트 복원 이벤트를 기록합니다.

원장

- `/fx/ledger`
- 엑셀형 검산 화면
- open 매수 로트와 sold allocation row를 합쳐 조회합니다.
- 누적수익과 환율차이평균은 전체 원장 고정 정렬 기준으로 계산합니다.
- 현재 표시된 원장 그리드를 CSV로 추출할 수 있습니다.

Dev Lab

- `/fx/dev-lab`
- 최근 매도 거래와 로트 이벤트를 확인하는 개발/검증용 화면입니다.

FX 통계

- `/fx/stats`
- 원장 데이터를 기반으로 누적수익 추이, 월별 실현손익, Open 로트 환율 분포를 조회합니다.
- 차트는 Recharts 기반으로 렌더링합니다.
- 누적수익 추이는 전체 KRW 손익과 USD/JPY 통화별 누적 흐름을 겹쳐 보여줍니다.
- 누적수익 차트 범례를 클릭해 전체/USD/JPY 선을 보이거나 숨길 수 있습니다.
- 누적수익 차트 영역은 세로 드래그로 높이를 조절할 수 있습니다.
- 별도 통계 API 없이 기존 원장 API 응답을 프론트에서 집계합니다.

Admin

- admin role 기반 접근 제어
- 사용자 목록/상세 조회
- 게시글 목록 조회
- 특정 사용자 FX 원장 조회
- FX lot event 조회
- 자산 코드 마스터 등록/수정/비활성화
- 자산명 중복 등록 방지

자산관리

- `/item-trades`
- 상단 메뉴에서는 `자산관리` 하나로 진입하고, 자산관리 내부 공통 탭에서 매수/매도/자산별 재고관리를 이동합니다.
- 자산관리 탭은 `?tab=buy`, `?tab=sell`, `?tab=inventory` URL 상태로 유지합니다.
- 관리자 자산 코드 마스터를 웹에서 자동완성으로 선택합니다.
- 매수, 매도, 자산별 재고관리 탭을 제공합니다.
- 평균단가 방식으로 재고 원가와 손익을 계산합니다.
- 판매 수수료율 기본값은 5%입니다.
- 최소 이득 판매가는 `ceil(평균단가 / (1 - 수수료율))`로 계산합니다.
- 매수 수수료율은 실제 매수 비용이 아니라 향후 판매 수수료 기준값입니다.
- 매도 수수료는 판매 금액에서 차감하여 손익을 계산합니다.
- 재고관리 수량 수정은 직접 update가 아니라 `adjustment` 거래 insert로 기록합니다.
- 조정 거래는 실제 보유 수량과 시스템 수량의 차이를 기록하며 취소 가능합니다.

공통 Web UI

- 상단 브레드크럼은 현재 섹션과 하위 탭을 `DW FX Ledger > FX > 매수`, `DW FX Ledger > 자산관리 > 매도`처럼 표시합니다.
- FX와 자산관리 탭은 `SectionTabs` 공통 컴포넌트 기준으로 같은 버튼 크기, 간격, 활성 상태 스타일을 사용합니다.
- 새 섹션이나 하위 메뉴를 추가할 때도 같은 탭 규격을 우선 사용합니다.

## 핵심 비즈니스 규칙

### 매수 로트 상태

`open`

- 아직 매도에 사용 가능한 활성 매수 로트입니다.
- 매도 allocation의 source가 될 수 있습니다.
- 수정/삭제는 `open + active + not deleted` 상태에서만 제한적으로 가능합니다.

`split`

- 매도 처리로 인해 원본 로트가 분할된 상태입니다.
- 원본 row의 금액을 직접 수정하지 않고 비활성화합니다.
- 이력 추적을 위해 source lot으로 남깁니다.

`sold`

- 매도된 부분을 나타내는 새 로트입니다.
- `fx_lot_allocations.closed_buy_lot_id`로 참조됩니다.

`cancelled`

- 매수 로트 soft delete 또는 매도 취소 과정에서 비활성 처리된 로트입니다.
- hard delete 대신 이력 보존을 우선합니다.

### 매도 처리 흐름

```text
source lot
  ↓
split 상태로 비활성화
  ↓
sold lot 생성
  ↓
remaining lot 생성
  ↓
allocation 생성
  ↓
event 생성
```

원본 로트는 금액을 직접 줄이지 않습니다. source lot은 `split`으로 남기고, 매도분은 `sold lot`, 잔여분은 `remaining open lot`으로 새로 생성합니다. 이렇게 해야 부분매도와 취소 이력을 추적할 수 있습니다.

### Allocation 전략

`highest_rate_first`

- 매수환율이 가장 높은 open lot부터 차감합니다.

`fifo`

- 오래된 매수일 순서로 차감합니다.

`lifo`

- 최근 매수일 순서로 차감합니다.

`manual`

- 사용자가 매수 로트를 직접 선택하고 각 로트별 차감 USD를 입력합니다.
- 선택한 USD 합계가 매도 USD와 같아야 합니다.
- backend에서도 소유자, 상태, 중복, 잔액 초과를 다시 검증합니다.

### 매도 취소 흐름

```text
sell transaction cancelled
  ↓
sold lot cancelled
  ↓
remaining lot cancelled
  ↓
restored open lot 생성
  ↓
event 기록
```

매도 취소는 수정/삭제가 아니라 반대 이벤트를 만드는 방식입니다. 중간 매도를 단독 취소하면 이후 allocation 계보가 깨질 수 있으므로 root lot 계보 기준 최신 매도부터만 취소할 수 있습니다.

## DB 주요 테이블

컬럼, 타입, FK, unique, index, default까지 포함한 상세 명세는 아래 문서를 참고합니다.

- Markdown: [`docs/table-spec.md`](docs/table-spec.md)
- CSV: [`docs/table-spec.csv`](docs/table-spec.csv)

추가 문서:

- Docker Compose 개발 실행: [`docs/docker-dev.md`](docs/docker-dev.md)
- FX 핵심 로직 순서도: [`docs/fx-core-flow.md`](docs/fx-core-flow.md)
- GPT/AI 세션 인수인계 메모: [`docs/gpt-context-summary.md`](docs/gpt-context-summary.md)

GPT/AI 세션에 프로젝트를 넘길 때는 README를 1차 문서로 사용하고, `docs/gpt-context-summary.md`는 README와 중복되는 전체 설명 대신 현재 용어 기준, 작업 주의사항, 알려진 정리 필요 항목만 보조로 제공합니다.

`users`

- 사용자 계정, 로그인 식별자, 기본 allocation 전략을 저장합니다.

`roles`

- 역할 코드와 역할명을 저장합니다.

`user_roles`

- 사용자와 역할의 다대다 매핑입니다.

`refresh_tokens`

- Refresh Token hash, 만료일, revoke 상태를 저장합니다.

`common_codes`

- 게시판 타입처럼 여러 기능에서 재사용하는 코드값을 저장합니다.
- `code_group`, `code` 조합으로 유일하며, 현재 `board_type/general`을 기본 seed로 사용합니다.

`board_posts`

- 게시판 게시글입니다.
- `board_type_code`로 게시판 종류를 구분하므로 게시판이 늘어나도 테이블을 추가하지 않습니다.

`board_comments`

- 게시글 댓글입니다.
- 댓글 작성자 또는 admin만 삭제할 수 있습니다.
- 삭제는 hard delete가 아니라 soft delete와 `deleted` 상태로 처리합니다.

`fx_buy_lots`

- 매수 로트입니다.
- 원본, sold, remaining, restored lot이 모두 이 테이블에 저장됩니다.
- `parent_buy_lot_id`, `root_buy_lot_id`로 로트 계보를 추적합니다.
- `currency_code`로 USD/JPY 등 통화를 구분합니다.

`fx_sell_transactions`

- 매도 거래 헤더입니다.
- 매도일, 매도 USD, 매도환율, 전략, 거래 상태, 총 손익을 저장합니다.
- `currency_code`로 USD/JPY 등 통화별 매도 거래를 분리합니다.

`fx_lot_allocations`

- 매도 거래가 어떤 매수 로트를 얼마나 차감했는지 기록합니다.
- allocation 1건은 원장 화면의 sold row 1건과 대응됩니다.

`fx_lot_events`

- 로트 분할, 매도 생성, 매도 취소, 로트 복원 이벤트를 저장합니다.
- 감사 추적과 취소 검증을 위한 이력 테이블입니다.

`item_codes`

- 자산을 코드 단위로 묶는 전역 관리자 마스터입니다.
- 관리자 사이트에서 자산명으로 등록하면 내부 코드가 자동 생성되며, 웹에서는 활성 자산명만 자동완성으로 선택합니다.
- 같은 자산명 중복 등록/수정은 API에서 차단합니다.

`item_trades`

- 자산 코드별 매수/매도/재고조정 기록과 평균단가 방식 손익 계산 결과를 저장합니다.
- 최소 이득 판매가, 수수료율, 수수료, 수수료 차감 후 금액, 손익, 거래 후 보유 수량을 기록합니다.
- `trade_type`은 `buy`, `sell`, `adjustment`를 사용합니다.
- 매수/매도/조정 취소는 `cancelled` 상태로 남기고, 같은 자산의 active 거래 기준으로 재고와 평균단가를 재계산합니다.
- 자산별 재고관리에서는 active 매도 거래의 총 수익을 함께 표시합니다.
- 감소 조정은 현재 평균단가로 원가를 차감하고, 증가 조정은 입력 단가로 원가를 증가시킵니다.

## 실행 방법

### 사전 준비

- Node.js
- pnpm
- Python 3.12+
- uv
- Docker / Docker Compose

### JavaScript 의존성 설치

```bash
pnpm install
```

### PostgreSQL 실행

```bash
docker compose up -d postgres
```

기본 compose 설정:

- DB: `dw_fx_ledger`
- User: `dw_fx_ledger`
- Password: `change_me`
- Port: `5432`

로컬 환경 변수는 `.env.example`을 참고해 각 앱의 `.env`에 설정합니다. `.env` 파일은 커밋하지 않습니다.

### Docker Compose 개발 실행

호스트 WSL에 Docker, Docker Compose, Git만 있는 경우에는 API/Web/Admin 런타임을 컨테이너에서 실행할 수 있습니다. 이 구성은 PostgreSQL 컨테이너를 띄우지 않고 외부 TrueNAS PostgreSQL을 사용합니다.

```bash
bash scripts/bootstrap-docker-host.sh
cp .env.docker.example .env.docker.local
vi .env.docker.local
bash scripts/docker-dev-up.sh
```

`.env.docker.local`에는 실제 DB 비밀번호를 넣고 커밋하지 않습니다.

```text
DATABASE_URL=postgresql+psycopg://fx_ledger:실제비밀번호@192.168.0.3:30432/fx_ledger_dev
SECRET_KEY=dev-secret-change-me
```

Docker 상태 확인:

```bash
bash scripts/docker-dev-ps.sh
docker compose -f docker-compose.dev.yml ps
```

중지:

```bash
bash scripts/docker-dev-down.sh
```

DB 연결 확인:

```bash
docker compose --env-file .env.docker.local -f docker-compose.dev.yml exec api uv run alembic current
```

`/health` 응답은 API 프로세스 상태 확인용이며 DB 연결 성공을 보장하지 않습니다. 자세한 내용은 [`docs/docker-dev.md`](docs/docker-dev.md)를 참고합니다.

### 통합 Dev 실행

API, Web, Admin을 백그라운드에서 한 번에 실행합니다.

```bash
pnpm start
```

실행 상태 확인:

```bash
pnpm status
```

`pnpm status`는 Docker 컨테이너 상태가 아니라 기존 로컬 실행 방식의 `.dev/*.pid` 상태를 확인합니다.

중지:

```bash
pnpm stop
```

재시작:

```bash
pnpm restart
```

서비스 URL:

- API: http://127.0.0.1:8000
- API Docs: http://127.0.0.1:8000/docs
- Web: http://localhost:3000
- Admin: http://localhost:3001

로그:

- `.dev/logs/api.log`
- `.dev/logs/web.log`
- `.dev/logs/admin.log`

Next.js dev server와 Uvicorn `--reload`가 파일 변경을 감지하므로 일반 코드 변경은 자동 반영됩니다. 프로세스를 완전히 다시 올리고 싶으면 `pnpm restart`를 사용합니다.

### Backend 개별 실행

```bash
cd apps/api
uv sync
uv run uvicorn app.main:app --reload
```

API:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/health

### Alembic migration

```bash
cd apps/api
uv run alembic upgrade head
```

현재 migration은 인증, 공통코드, 게시판, FX 매수/매도/allocation/event, 자산 코드/거래 기록 테이블을 생성합니다.

### Frontend 개별 실행

```bash
pnpm dev:web
```

Web:

- http://localhost:3000

### Admin 개별 실행

```bash
pnpm dev:admin
```

Admin:

- http://localhost:3001

### Web + Admin 동시 실행

```bash
pnpm dev
```

## 테스트 방법

Backend lint

```bash
cd apps/api
uv run ruff check app tests
```

Backend tests

```bash
cd apps/api
uv run pytest -q
```

Frontend typecheck

```bash
pnpm --filter @dw-fx-ledger/web typecheck
```

Frontend build

```bash
pnpm --filter @dw-fx-ledger/web build
```

Admin typecheck/build

```bash
pnpm --filter @dw-fx-ledger/admin typecheck
pnpm --filter @dw-fx-ledger/admin build
```

전체 workspace build

```bash
pnpm build
```

## 주요 화면

Web:

- `/login`: 로그인
- `/register`: 회원가입
- `/posts`: 게시판
- `/fx`: FX 섹션 진입점. `/fx/buy-lots`로 이동합니다.
- `/fx/buy-lots`: FX 매수 탭, 매수 로트 목록
- `/fx/buy-lots/new`: 매수 등록
- `/fx/sell-transactions`: FX 매도 탭, 매도 거래 목록
- `/fx/sell-transactions/new`: 매도 등록
- `/fx/ledger`: FX 원장 탭, 엑셀형 원장 조회와 CSV 추출
- `/fx/stats`: FX 통계 탭, Recharts 기반 원장 통계 차트
- `/fx/dev-lab`: FX Lab 탭, 개발/검증용 FX 이벤트 확인
- `/item-trades?tab=buy`: 자산 매수 탭
- `/item-trades?tab=sell`: 자산 매도 탭
- `/item-trades?tab=inventory`: 자산별 재고관리 탭

Admin:

- `/login`: Admin 로그인
- `/admin/users`: 사용자 목록
- `/admin/users/[userId]`: 사용자 상세와 FX 요약
- `/admin/posts`: 게시글 목록
- `/admin/fx/ledger?userId=`: 특정 사용자 FX 원장
- `/admin/fx/events`: FX lot event 조회
- `/admin/item-codes`: 자산 코드 마스터 관리

## 현재 알려진 제한사항

- 매도 수정 기능은 없습니다.
- 매도 삭제 기능은 없습니다.
- 매도는 취소만 지원합니다.
- 중간 매도 단독 취소는 허용하지 않습니다.
- `/fx/ledger`는 조회 전용 검산 화면입니다.
- Admin은 현재 조회와 자산 코드 마스터 관리 중심입니다.
- Admin에서 FX 장부 자체를 수정/삭제하는 기능은 없습니다.
- 기존 중복 자산 코드 중 거래가 연결된 항목은 병합 기준을 정해 별도 정리해야 합니다.
- Recharts 사용으로 `/fx/stats` 화면의 클라이언트 번들이 다른 FX 화면보다 큽니다.

## 향후 예정

- Admin 고도화
- 리포트 화면
- Excel Export
- 통계 차트 고도화
- root lot timeline
- 원장 필터/검색 고도화
- 매수/매도 데이터 import 도구 정식화
- 자산 코드 중복 병합/정리 도구

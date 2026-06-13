# DW FX Ledger Table Specification

기준: SQLAlchemy models + Alembic migrations `20260604_0001`, `20260605_0002`, `20260607_0003`, `20260607_0004`, `20260607_0005`, `20260607_0006`, `20260611_0007`, `20260611_0008`.

## 개요

| 테이블 | 설명 |
|---|---|
| `users` | 사용자 계정, 로그인 식별자, 계정 상태, 기본 FX allocation 전략 |
| `roles` | 시스템 role 코드와 role 이름 |
| `user_roles` | 사용자와 role의 다대다 매핑 |
| `refresh_tokens` | Refresh token hash, 만료/폐기 상태 |
| `common_codes` | 게시판 타입 등 여러 기능에서 재사용하는 공통코드 |
| `board_posts` | 게시판 타입 코드로 구분되는 게시글 |
| `board_comments` | 게시글 댓글 |
| `fx_buy_lots` | FX 매수 로트. 원본, split, sold, remaining, restored 로트가 모두 저장됨 |
| `fx_sell_transactions` | FX 매도 거래 헤더 |
| `fx_lot_allocations` | 매도 거래가 차감한 매수 로트와 손익 계산 결과 |
| `fx_lot_events` | 로트 분할, 매도 생성, 매도 취소, 로트 복원 감사 이벤트 |
| `item_codes` | 자산 코드 마스터 |
| `item_trades` | 자산 매수/매도 손익 계산 기록 |

## 공통 컬럼 패턴

| 패턴 | 컬럼 | 설명 |
|---|---|---|
| Timestamp | `created_at`, `updated_at` | 생성/수정 시각. `updated_at`은 ORM에서 update 시 갱신 |
| Audit user | `created_by`, `updated_by` | 작업을 수행한 사용자. `users.user_id` FK |
| Soft delete | `is_deleted` | 논리 삭제 여부 |
| Active | `is_active` | role, 공통코드, buy lot 같은 데이터의 활성 여부 |

## 주요 상태값

| 대상 | 값 | 설명 |
|---|---|---|
| `users.user_status` | `active`, `locked`, `withdrawn` | 사용자 상태 |
| `roles.role_code` | `user`, `admin` | 일반 사용자 / 관리자 |
| `common_codes.code_group` | `board_type` | 게시판 타입 코드 그룹 |
| `board_posts.post_status` | `published`, `deleted` | 게시글 공개 / 삭제 |
| `board_comments.comment_status` | `published`, `deleted` | 댓글 공개 / 삭제 |
| `fx_buy_lots.lot_status` | `open`, `split`, `sold`, `cancelled` | 매수 로트 상태 |
| `fx_sell_transactions.transaction_status` | `completed`, `cancelled` | 매도 거래 완료 / 취소 |
| `fx_sell_transactions.allocation_strategy` | `highest_rate_first`, `fifo`, `lifo`, `manual` | 매수 로트 차감 전략 |
| `fx_lot_events.event_type` | `sell_transaction_created`, `lot_split`, `sell_transaction_cancelled`, `lot_restored` | 로트 이벤트 유형 |
| `fx_lot_events.event_status` | `completed` | 이벤트 완료 상태 |

## users

사용자 계정 테이블입니다. 로그인, 기본 allocation 전략, 계정 상태를 저장합니다.

| 컬럼 | 타입 | Null | Key | Default | 설명 |
|---|---|---:|---|---|---|
| `user_id` | `bigint` | N | PK | autoincrement | 사용자 ID |
| `email` | `varchar(255)` | N | UQ |  | 이메일 |
| `login_id` | `varchar(100)` | Y | UQ |  | 로그인 ID |
| `password_hash` | `varchar(255)` | N |  |  | 비밀번호 hash |
| `display_name` | `varchar(100)` | N |  |  | 표시 이름 |
| `user_status` | `varchar(30)` | N | IX | `active` | 계정 상태 |
| `default_allocation_strategy` | `varchar(50)` | N |  | `highest_rate_first` | 기본 FX 매도 차감 전략 |
| `is_deleted` | `boolean` | N | IX | `false` | 논리 삭제 여부 |
| `created_at` | `timestamptz` | N |  | `now()` | 생성 시각 |
| `updated_at` | `timestamptz` | N |  | `now()` | 수정 시각 |
| `created_by` | `bigint` | Y | FK `users.user_id` |  | 생성자 |
| `updated_by` | `bigint` | Y | FK `users.user_id` |  | 수정자 |

인덱스: `ix_users_user_status(user_status)`, `ix_users_is_deleted(is_deleted)`

## roles

권한 role 마스터 테이블입니다.

| 컬럼 | 타입 | Null | Key | Default | 설명 |
|---|---|---:|---|---|---|
| `role_id` | `bigint` | N | PK | autoincrement | Role ID |
| `role_code` | `varchar(50)` | N | UQ |  | Role 코드 |
| `role_name` | `varchar(100)` | N |  |  | Role 이름 |
| `description` | `text` | Y |  |  | Role 설명 |
| `is_active` | `boolean` | N |  | `true` | 활성 여부 |
| `is_deleted` | `boolean` | N |  | `false` | 논리 삭제 여부 |
| `created_at` | `timestamptz` | N |  | `now()` | 생성 시각 |
| `updated_at` | `timestamptz` | N |  | `now()` | 수정 시각 |
| `created_by` | `bigint` | Y | FK `users.user_id` |  | 생성자 |
| `updated_by` | `bigint` | Y | FK `users.user_id` |  | 수정자 |

## user_roles

사용자와 role의 매핑 테이블입니다.

| 컬럼 | 타입 | Null | Key | Default | 설명 |
|---|---|---:|---|---|---|
| `user_role_id` | `bigint` | N | PK | autoincrement | 사용자-role 매핑 ID |
| `user_id` | `bigint` | N | FK `users.user_id`, IX, UQ pair |  | 사용자 |
| `role_id` | `bigint` | N | FK `roles.role_id`, IX, UQ pair |  | Role |
| `created_at` | `timestamptz` | N |  | `now()` | 생성 시각 |
| `created_by` | `bigint` | Y | FK `users.user_id` |  | 생성자 |

제약: `uq_user_roles_user_id_role_id(user_id, role_id)`

인덱스: `ix_user_roles_user_id(user_id)`, `ix_user_roles_role_id(role_id)`

## refresh_tokens

Refresh token을 원문이 아닌 hash로 저장합니다.

| 컬럼 | 타입 | Null | Key | Default | 설명 |
|---|---|---:|---|---|---|
| `refresh_token_id` | `bigint` | N | PK | autoincrement | Refresh token ID |
| `user_id` | `bigint` | N | FK `users.user_id`, IX |  | 토큰 소유 사용자 |
| `token_hash` | `varchar(255)` | N | UQ |  | Refresh token hash |
| `expires_at` | `timestamptz` | N | IX |  | 만료 시각 |
| `revoked_at` | `timestamptz` | Y | IX |  | 폐기 시각 |
| `user_agent` | `text` | Y |  |  | 요청 User-Agent |
| `ip_address` | `inet` | Y |  |  | 요청 IP |
| `created_at` | `timestamptz` | N |  | `now()` | 생성 시각 |
| `created_by` | `bigint` | Y | FK `users.user_id` |  | 생성자 |

인덱스: `ix_refresh_tokens_user_id(user_id)`, `ix_refresh_tokens_expires_at(expires_at)`, `ix_refresh_tokens_revoked_at(revoked_at)`

## common_codes

게시판 타입처럼 여러 기능에서 재사용할 코드값을 저장하는 공통코드 테이블입니다.

| 컬럼 | 타입 | Null | Key | Default | 설명 |
|---|---|---:|---|---|---|
| `common_code_id` | `bigint` | N | PK | autoincrement | 공통코드 ID |
| `code_group` | `varchar(50)` | N | UQ pair, IX composite |  | 코드 그룹. 예: `board_type` |
| `code` | `varchar(50)` | N | UQ pair |  | 그룹 안의 실제 코드값. 예: `general` |
| `code_name` | `varchar(100)` | N |  |  | 화면 표시 이름 |
| `description` | `text` | Y |  |  | 코드 설명 |
| `sort_order` | `integer` | N | IX composite | `0` | 같은 그룹 안의 표시 순서 |
| `is_active` | `boolean` | N | IX composite | `true` | 사용 가능 여부 |
| `created_at` | `timestamptz` | N |  | `now()` | 생성 시각 |
| `updated_at` | `timestamptz` | N |  | `now()` | 수정 시각 |

제약: `uq_common_codes_group_code(code_group, code)`

인덱스: `ix_common_codes_group_active_sort(code_group, is_active, sort_order)`

## board_posts

게시판 게시글 테이블입니다. 게시판이 늘어나도 테이블을 추가하지 않고 `board_type_code`로 게시판 타입을 구분합니다.

| 컬럼 | 타입 | Null | Key | Default | 설명 |
|---|---|---:|---|---|---|
| `post_id` | `bigint` | N | PK | autoincrement | 게시글 ID |
| `author_id` | `bigint` | N | FK `users.user_id`, IX |  | 작성자 |
| `board_type_code` | `varchar(50)` | N | IX composite | `general` | 게시판 타입 코드. `common_codes(code_group='board_type')`의 `code` 값 |
| `title` | `varchar(200)` | N |  |  | 제목 |
| `content` | `text` | N |  |  | 본문 |
| `view_count` | `integer` | N |  | `0` | 조회수 |
| `post_status` | `varchar(30)` | N |  | `published` | 게시글 상태 |
| `is_deleted` | `boolean` | N | IX composite | `false` | 논리 삭제 여부 |
| `created_at` | `timestamptz` | N | IX composite | `now()` | 생성 시각 |
| `updated_at` | `timestamptz` | N |  | `now()` | 수정 시각 |
| `created_by` | `bigint` | Y | FK `users.user_id` |  | 생성자 |
| `updated_by` | `bigint` | Y | FK `users.user_id` |  | 수정자 |

인덱스: `ix_board_posts_author_id(author_id)`, `ix_board_posts_board_type_code_created_at(board_type_code, created_at)`, `ix_board_posts_created_at(created_at)`, `ix_board_posts_is_deleted_created_at(is_deleted, created_at)`

## board_comments

게시글 댓글 테이블입니다. 댓글은 물리 삭제하지 않고 `is_deleted=true`, `comment_status='deleted'`로 숨깁니다.

| 컬럼 | 타입 | Null | Key | Default | 설명 |
|---|---|---:|---|---|---|
| `comment_id` | `bigint` | N | PK | autoincrement | 댓글 ID |
| `post_id` | `bigint` | N | FK `board_posts.post_id`, IX composite |  | 댓글이 달린 게시글 |
| `author_id` | `bigint` | N | FK `users.user_id`, IX |  | 댓글 작성자 |
| `content` | `text` | N |  |  | 댓글 본문 |
| `comment_status` | `varchar(30)` | N |  | `published` | 댓글 상태 |
| `is_deleted` | `boolean` | N | IX composite | `false` | 논리 삭제 여부 |
| `created_at` | `timestamptz` | N | IX composite | `now()` | 생성 시각 |
| `updated_at` | `timestamptz` | N |  | `now()` | 수정 시각 |
| `created_by` | `bigint` | Y | FK `users.user_id` |  | 생성자 |
| `updated_by` | `bigint` | Y | FK `users.user_id` |  | 수정자 |

인덱스: `ix_board_comments_post_id_created_at(post_id, created_at)`, `ix_board_comments_author_id(author_id)`, `ix_board_comments_is_deleted_created_at(is_deleted, created_at)`

## fx_buy_lots

FX 매수 로트 테이블입니다. 원본 로트뿐 아니라 매도 과정의 split, sold, remaining, restored 로트도 저장합니다.

| 컬럼 | 타입 | Null | Key | Default | 설명 |
|---|---|---:|---|---|---|
| `buy_lot_id` | `bigint` | N | PK | autoincrement | 매수 로트 ID |
| `user_id` | `bigint` | N | FK `users.user_id`, IX |  | 소유 사용자 |
| `parent_buy_lot_id` | `bigint` | Y | FK `fx_buy_lots.buy_lot_id`, IX |  | 분할/복원 시 부모 로트 |
| `root_buy_lot_id` | `bigint` | Y | FK `fx_buy_lots.buy_lot_id`, IX |  | 로트 계보의 루트 |
| `lot_status` | `varchar(30)` | N | IX composite |  | 로트 상태 |
| `currency_code` | `varchar(3)` | N | IX composite | `USD` | 로트 통화 코드. 예: `USD`, `JPY` |
| `buy_date` | `date` | N | IX composite |  | 매수일 |
| `buy_krw_amount` | `bigint` | N |  |  | 매수 원화 금액 |
| `buy_exchange_rate` | `numeric(18,6)` | N | IX composite |  | 매수 적용 환율 |
| `usd_amount` | `numeric(18,6)` | N |  |  | 매수 USD 금액 |
| `is_active` | `boolean` | N | IX composite | `true` | active open 로트 여부 판단에 사용 |
| `is_deleted` | `boolean` | N | IX composite | `false` | 논리 삭제 여부 |
| `lock_version` | `integer` | N |  | `1` | 낙관적 잠금/변경 버전 |
| `created_at` | `timestamptz` | N |  | `now()` | 생성 시각 |
| `updated_at` | `timestamptz` | N |  | `now()` | 수정 시각 |
| `created_by` | `bigint` | Y | FK `users.user_id` |  | 생성자 |
| `updated_by` | `bigint` | Y | FK `users.user_id` |  | 수정자 |

인덱스:

- `ix_fx_buy_lots_user_id(user_id)`
- `ix_fx_buy_lots_user_id_currency_code(user_id, currency_code)`
- `ix_fx_buy_lots_user_id_lot_status_is_active_is_deleted(user_id, currency_code, lot_status, is_active, is_deleted)`
- `ix_fx_buy_lots_user_id_buy_date(user_id, buy_date)`
- `ix_fx_buy_lots_user_id_buy_exchange_rate(user_id, buy_exchange_rate)`
- `ix_fx_buy_lots_parent_buy_lot_id(parent_buy_lot_id)`
- `ix_fx_buy_lots_root_buy_lot_id(root_buy_lot_id)`

## fx_sell_transactions

FX 매도 거래 헤더 테이블입니다. 거래 전체 요약 손익을 저장합니다.

| 컬럼 | 타입 | Null | Key | Default | 설명 |
|---|---|---:|---|---|---|
| `sell_transaction_id` | `bigint` | N | PK | autoincrement | 매도 거래 ID |
| `user_id` | `bigint` | N | FK `users.user_id`, IX |  | 소유 사용자 |
| `currency_code` | `varchar(3)` | N | IX composite | `USD` | 매도 거래 통화 코드. 예: `USD`, `JPY` |
| `sell_date` | `date` | N | IX composite |  | 매도일 |
| `sell_usd_amount` | `numeric(18,6)` | N |  |  | 매도 USD 금액 |
| `sell_exchange_rate` | `numeric(18,6)` | N |  |  | 매도 적용 환율 |
| `allocation_strategy` | `varchar(50)` | N | IX |  | 차감 전략 |
| `transaction_status` | `varchar(30)` | N | IX | `completed` | 거래 상태 |
| `total_buy_krw_amount` | `bigint` | N |  |  | 차감된 매수 원화 합계 |
| `total_sell_krw_amount` | `bigint` | N |  |  | 매도 원화 합계 |
| `total_real_profit_krw` | `bigint` | N |  |  | 실제 손익 합계 |
| `total_display_profit_krw` | `bigint` | N |  |  | 원장 표시 손익 합계 |
| `memo` | `text` | Y |  |  | 메모 |
| `is_deleted` | `boolean` | N |  | `false` | 논리 삭제 여부 |
| `created_at` | `timestamptz` | N |  | `now()` | 생성 시각 |
| `updated_at` | `timestamptz` | N |  | `now()` | 수정 시각 |
| `created_by` | `bigint` | Y | FK `users.user_id` |  | 생성자 |
| `updated_by` | `bigint` | Y | FK `users.user_id` |  | 수정자 |

인덱스:

- `ix_fx_sell_transactions_user_id(user_id)`
- `ix_fx_sell_transactions_user_id_currency_code(user_id, currency_code)`
- `ix_fx_sell_transactions_user_id_sell_date(user_id, sell_date)`
- `ix_fx_sell_transactions_allocation_strategy(allocation_strategy)`
- `ix_fx_sell_transactions_transaction_status(transaction_status)`

## fx_lot_allocations

매도 거래가 어떤 매수 로트를 얼마나 차감했는지 기록합니다. 원장 화면의 sold row와 대응됩니다.

| 컬럼 | 타입 | Null | Key | Default | 설명 |
|---|---|---:|---|---|---|
| `lot_allocation_id` | `bigint` | N | PK | autoincrement | Allocation ID |
| `sell_transaction_id` | `bigint` | N | FK `fx_sell_transactions.sell_transaction_id`, IX |  | 매도 거래 |
| `source_buy_lot_id` | `bigint` | N | FK `fx_buy_lots.buy_lot_id`, IX |  | 차감 대상 원본/source 로트 |
| `closed_buy_lot_id` | `bigint` | N | FK `fx_buy_lots.buy_lot_id`, IX |  | sold 로트 |
| `remaining_buy_lot_id` | `bigint` | Y | FK `fx_buy_lots.buy_lot_id`, IX |  | 일부 차감 후 remaining 로트 |
| `allocated_usd_amount` | `numeric(18,6)` | N |  |  | 차감 USD 금액 |
| `allocated_buy_krw_amount` | `bigint` | N |  |  | 차감분 매수 원화 금액 |
| `allocated_sell_krw_amount` | `bigint` | N |  |  | 차감분 매도 원화 금액 |
| `real_profit_krw` | `bigint` | N |  |  | 실제 손익 |
| `display_profit_krw` | `bigint` | N |  |  | 원장 표시 손익 |
| `exchange_diff` | `numeric(18,6)` | N |  |  | 매도 환율 - 매수 환율. 음수는 0 처리 |
| `created_at` | `timestamptz` | N |  | `now()` | 생성 시각 |
| `created_by` | `bigint` | Y | FK `users.user_id` |  | 생성자 |

인덱스:

- `ix_fx_lot_allocations_sell_transaction_id(sell_transaction_id)`
- `ix_fx_lot_allocations_source_buy_lot_id(source_buy_lot_id)`
- `ix_fx_lot_allocations_closed_buy_lot_id(closed_buy_lot_id)`
- `ix_fx_lot_allocations_remaining_buy_lot_id(remaining_buy_lot_id)`

## fx_lot_events

로트 분할/매도/취소/복원 이벤트 감사 테이블입니다.

| 컬럼 | 타입 | Null | Key | Default | 설명 |
|---|---|---:|---|---|---|
| `lot_event_id` | `bigint` | N | PK | autoincrement | 이벤트 ID |
| `user_id` | `bigint` | N | FK `users.user_id`, IX composite |  | 이벤트 소유 사용자 |
| `event_type` | `varchar(50)` | N | IX |  | 이벤트 유형 |
| `event_status` | `varchar(30)` | N |  | `completed` | 이벤트 상태 |
| `root_buy_lot_id` | `bigint` | Y | FK `fx_buy_lots.buy_lot_id`, IX composite |  | 루트 로트 |
| `sell_transaction_id` | `bigint` | Y | FK `fx_sell_transactions.sell_transaction_id`, IX |  | 관련 매도 거래 |
| `lot_allocation_id` | `bigint` | Y | FK `fx_lot_allocations.lot_allocation_id`, IX |  | 관련 allocation |
| `source_buy_lot_id` | `bigint` | Y | FK `fx_buy_lots.buy_lot_id`, IX |  | source 로트 |
| `closed_buy_lot_id` | `bigint` | Y | FK `fx_buy_lots.buy_lot_id` |  | sold/closed 로트 |
| `remaining_buy_lot_id` | `bigint` | Y | FK `fx_buy_lots.buy_lot_id` |  | remaining 로트 |
| `restored_buy_lot_id` | `bigint` | Y | FK `fx_buy_lots.buy_lot_id`, IX |  | 취소 시 복원된 로트 |
| `related_event_id` | `bigint` | Y | FK `fx_lot_events.lot_event_id` |  | 관련 이벤트 |
| `event_payload` | `jsonb` | Y |  |  | 이벤트 부가 데이터 |
| `created_at` | `timestamptz` | N | IX composite | `now()` | 생성 시각 |
| `created_by` | `bigint` | Y | FK `users.user_id` |  | 생성자 |

인덱스:

- `ix_fx_lot_events_user_id_created_at(user_id, created_at)`
- `ix_fx_lot_events_root_buy_lot_id_created_at(root_buy_lot_id, created_at)`
- `ix_fx_lot_events_sell_transaction_id(sell_transaction_id)`
- `ix_fx_lot_events_lot_allocation_id(lot_allocation_id)`
- `ix_fx_lot_events_source_buy_lot_id(source_buy_lot_id)`
- `ix_fx_lot_events_restored_buy_lot_id(restored_buy_lot_id)`
- `ix_fx_lot_events_event_type(event_type)`

## item_codes

자산을 코드 단위로 묶기 위한 전역 관리자 마스터 테이블입니다.

| 컬럼 | 타입 | Null | Key | Default | 설명 |
|---|---|---:|---|---|---|
| `item_code_id` | `bigint` | N | PK | autoincrement | 자산 코드 ID |
| `user_id` | `bigint` | Y | FK `users.user_id`, IX |  | 과거 사용자별 코드 호환 컬럼. 전역 코드는 NULL |
| `item_code` | `varchar(80)` | N | Unique partial |  | 전역 자산 코드. 관리자 등록 시 `ITEM-000001` 형식으로 자동 생성 |
| `item_name` | `varchar(120)` | N | IX |  | 자산명 |
| `memo` | `text` | Y |  |  | 메모 |
| `is_active` | `boolean` | N | IX | `true` | 사용 가능 여부. 삭제 대신 비활성화 |
| `is_deleted` | `boolean` | N |  | `false` | 논리 삭제 여부 |
| `created_at` | `timestamptz` | N |  | `now()` | 생성 시각 |
| `updated_at` | `timestamptz` | N |  | `now()` | 수정 시각 |
| `created_by` | `bigint` | Y | FK `users.user_id` |  | 생성자 |
| `updated_by` | `bigint` | Y | FK `users.user_id` |  | 수정자 |

인덱스:

- `ix_item_codes_user_id(user_id)`
- `ix_item_codes_item_code_active(item_code)` unique where `is_deleted = false`
- `ix_item_codes_is_active(is_active)`
- `ix_item_codes_item_name(item_name)`

## item_trades

자산 코드별 매수/매도 기록과 평균단가 방식 손익 계산 결과를 저장합니다.

| 컬럼 | 타입 | Null | Key | Default | 설명 |
|---|---|---:|---|---|---|
| `item_trade_id` | `bigint` | N | PK | autoincrement | 자산 거래 기록 ID |
| `user_id` | `bigint` | N | FK `users.user_id`, IX composite |  | 기록 소유 사용자 |
| `item_code_id` | `bigint` | Y | FK `item_codes.item_code_id`, IX |  | 자산 코드 |
| `trade_type` | `varchar(20)` | N | IX | `buy` | 거래 구분. `buy`, `sell` |
| `trade_status` | `varchar(20)` | N | IX | `active` | 거래 상태. `active`, `cancelled` |
| `item_name` | `varchar(120)` | N | IX |  | 자산명 |
| `buy_date` | `date` | N | IX composite |  | 매수일. 매도 row에서는 거래일 호환 저장 |
| `buy_unit_price` | `bigint` | N |  |  | 매수 단가. 매도 row에서는 평균단가 호환 저장 |
| `quantity` | `integer` | N |  |  | 수량 |
| `fee_rate` | `numeric(8,6)` | N |  |  | 판매 수수료율. 5%는 `0.050000` |
| `minimum_profitable_unit_price` | `bigint` | N |  |  | 평균단가와 수수료 기준 최소 1개 판매가 |
| `average_buy_unit_price` | `bigint` | Y |  |  | 해당 기록 시점 평균단가 |
| `inventory_quantity_after` | `integer` | Y |  |  | 기록 반영 후 보유 수량 |
| `inventory_value_after` | `bigint` | Y |  |  | 기록 반영 후 재고 원가 |
| `sell_date` | `date` | Y |  |  | 매도일 |
| `sell_unit_price` | `bigint` | Y |  |  | 1개당 매도 가격 |
| `total_buy_amount` | `bigint` | N |  |  | 매수 row는 총 매수금액, 매도 row는 평균단가 기준 원가 |
| `total_sell_amount` | `bigint` | Y |  |  | 총 매도금액 |
| `fee_amount` | `bigint` | Y |  |  | 판매 수수료 |
| `net_sell_amount` | `bigint` | Y |  |  | 수수료 차감 후 매도금액 |
| `profit_amount` | `bigint` | Y |  |  | 손익 |
| `cancelled_at` | `timestamptz` | Y |  |  | 취소 시각 |
| `cancel_reason` | `text` | Y |  |  | 취소 사유 |
| `memo` | `text` | Y |  |  | 메모 |
| `is_deleted` | `boolean` | N |  | `false` | 논리 삭제 여부 |
| `created_at` | `timestamptz` | N | IX composite | `now()` | 생성 시각 |
| `updated_at` | `timestamptz` | N |  | `now()` | 수정 시각 |
| `created_by` | `bigint` | Y | FK `users.user_id` |  | 생성자 |
| `updated_by` | `bigint` | Y | FK `users.user_id` |  | 수정자 |

인덱스:

- `ix_item_trades_item_code_id(item_code_id)`
- `ix_item_trades_user_id_item_code_id(user_id, item_code_id)`
- `ix_item_trades_trade_type(trade_type)`
- `ix_item_trades_trade_status(trade_status)`
- `ix_item_trades_user_id_buy_date(user_id, buy_date)`
- `ix_item_trades_user_id_created_at(user_id, created_at)`
- `ix_item_trades_item_name(item_name)`

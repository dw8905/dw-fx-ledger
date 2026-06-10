from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.schemas.fx import LedgerResponse


class AdminUserListItem(BaseModel):
    """관리자 사용자 목록의 한 행에 필요한 계정/권한 요약입니다."""

    user_id: int
    email: EmailStr
    login_id: str | None
    display_name: str
    user_status: str
    roles: list[str]
    created_at: datetime


class AdminUserListResponse(BaseModel):
    """관리자 사용자 목록과 페이지네이션 메타 정보를 반환합니다."""

    items: list[AdminUserListItem]
    page: int
    size: int
    total_count: int
    total_pages: int


class AdminFxSummary(BaseModel):
    """사용자 상세에서 FX 활동 규모와 손익을 빠르게 파악하는 요약입니다."""

    total_buy_krw_amount: int
    total_buy_usd_amount: Decimal
    buy_lot_count: int
    open_lot_count: int
    sell_transaction_count: int
    lot_event_count: int
    total_real_profit_krw: int
    total_display_profit_krw: int
    final_cumulative_profit_krw: int
    latest_ledger_date: str | None
    open_usd_amount: Decimal


class AdminUserDetail(AdminUserListItem):
    """관리자 사용자 상세 화면용 계정 정보와 FX 요약을 묶은 모델입니다."""

    default_allocation_strategy: str
    updated_at: datetime
    fx_summary: AdminFxSummary


class AdminPostListItem(BaseModel):
    """관리자 게시글 목록에서 삭제 여부까지 포함해 보여주는 한 행입니다."""

    post_id: int
    author_id: int
    author_name: str
    title: str
    view_count: int
    post_status: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class AdminPostListResponse(BaseModel):
    """관리자 게시글 목록과 페이지네이션 메타 정보를 반환합니다."""

    items: list[AdminPostListItem]
    page: int
    size: int
    total_count: int
    total_pages: int


class AdminLotEventRead(BaseModel):
    """관리자 FX 이벤트 로그 그리드에서 읽는 로트 이벤트 정보입니다."""

    lot_event_id: int
    user_id: int
    event_type: str
    event_status: str
    root_buy_lot_id: int | None
    sell_transaction_id: int | None
    lot_allocation_id: int | None
    source_buy_lot_id: int | None
    closed_buy_lot_id: int | None
    remaining_buy_lot_id: int | None
    restored_buy_lot_id: int | None
    related_event_id: int | None
    event_payload: dict | None
    created_at: datetime


class AdminLotEventListResponse(BaseModel):
    """관리자 FX 이벤트 로그 목록과 페이지네이션 메타 정보를 반환합니다."""

    items: list[AdminLotEventRead]
    page: int
    size: int
    total_count: int
    total_pages: int


class AdminUserLedgerResponse(BaseModel):
    """특정 사용자 정보와 해당 사용자의 FX 원장을 함께 내려주는 응답입니다."""

    user: AdminUserListItem
    ledger: LedgerResponse


class AdminItemCodeCreateRequest(BaseModel):
    """관리자가 전역 자산 마스터를 등록할 때 받는 입력값입니다."""

    item_name: str = Field(min_length=1, max_length=120)
    memo: str | None = None
    is_active: bool = True


class AdminItemCodeUpdateRequest(BaseModel):
    """관리자가 전역 자산 마스터명/메모/활성 상태를 수정할 때 쓰는 입력값입니다."""

    item_name: str = Field(min_length=1, max_length=120)
    memo: str | None = None
    is_active: bool = True


class AdminItemCodeRead(BaseModel):
    """관리자 자산 마스터 목록에 표시할 코드, 이름, 상태 정보입니다."""

    item_code_id: int
    item_code: str
    item_name: str
    memo: str | None
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class AdminItemCodeListResponse(BaseModel):
    """관리자 자산 마스터 목록과 페이지네이션 메타 정보를 반환합니다."""

    items: list[AdminItemCodeRead]
    page: int
    size: int
    total_count: int
    total_pages: int

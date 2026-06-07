from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.schemas.fx import LedgerResponse


class AdminUserListItem(BaseModel):
    user_id: int
    email: EmailStr
    login_id: str | None
    display_name: str
    user_status: str
    roles: list[str]
    created_at: datetime


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    page: int
    size: int
    total_count: int
    total_pages: int


class AdminFxSummary(BaseModel):
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
    default_allocation_strategy: str
    updated_at: datetime
    fx_summary: AdminFxSummary


class AdminPostListItem(BaseModel):
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
    items: list[AdminPostListItem]
    page: int
    size: int
    total_count: int
    total_pages: int


class AdminLotEventRead(BaseModel):
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
    items: list[AdminLotEventRead]
    page: int
    size: int
    total_count: int
    total_pages: int


class AdminUserLedgerResponse(BaseModel):
    user: AdminUserListItem
    ledger: LedgerResponse


class AdminItemCodeCreateRequest(BaseModel):
    item_name: str = Field(min_length=1, max_length=120)
    memo: str | None = None
    is_active: bool = True


class AdminItemCodeUpdateRequest(BaseModel):
    item_name: str = Field(min_length=1, max_length=120)
    memo: str | None = None
    is_active: bool = True


class AdminItemCodeRead(BaseModel):
    item_code_id: int
    item_code: str
    item_name: str
    memo: str | None
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class AdminItemCodeListResponse(BaseModel):
    items: list[AdminItemCodeRead]
    page: int
    size: int
    total_count: int
    total_pages: int

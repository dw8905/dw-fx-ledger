from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import (
    AuditUserMixin,
    Base,
    ExchangeRate,
    KRWAmount,
    SoftDeleteMixin,
    String,
    Text,
    TimestampMixin,
    USDNumeric,
)


class FxSellTransaction(TimestampMixin, AuditUserMixin, SoftDeleteMixin, Base):
    """한 번의 외화 매도 거래와 그 거래의 전체 손익 합계를 저장합니다."""

    __tablename__ = "fx_sell_transactions"

    sell_transaction_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=False
    )
    # fx_sell_transactions.currency_code: USD/JPY처럼 이 매도 거래가 처리한 통화 코드입니다.
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD")
    sell_date: Mapped[date] = mapped_column(nullable=False)
    sell_usd_amount: Mapped[Decimal] = mapped_column(USDNumeric, nullable=False)
    sell_exchange_rate: Mapped[Decimal] = mapped_column(ExchangeRate, nullable=False)
    allocation_strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    transaction_status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="completed"
    )
    total_buy_krw_amount: Mapped[int] = mapped_column(KRWAmount, nullable=False)
    total_sell_krw_amount: Mapped[int] = mapped_column(KRWAmount, nullable=False)
    total_real_profit_krw: Mapped[int] = mapped_column(KRWAmount, nullable=False)
    total_display_profit_krw: Mapped[int] = mapped_column(KRWAmount, nullable=False)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_fx_sell_transactions_user_id", "user_id"),
        Index("ix_fx_sell_transactions_user_id_currency_code", "user_id", "currency_code"),
        Index("ix_fx_sell_transactions_user_id_sell_date", "user_id", "sell_date"),
        Index("ix_fx_sell_transactions_allocation_strategy", "allocation_strategy"),
        Index("ix_fx_sell_transactions_transaction_status", "transaction_status"),
    )


class FxBuyLot(TimestampMixin, AuditUserMixin, SoftDeleteMixin, Base):
    """매수로 생긴 외화 보유 묶음이며, 매도 시 닫힌/잔여 로트로 분리됩니다."""

    __tablename__ = "fx_buy_lots"

    buy_lot_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=False
    )
    parent_buy_lot_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("fx_buy_lots.buy_lot_id"), nullable=True
    )
    root_buy_lot_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("fx_buy_lots.buy_lot_id"), nullable=True
    )
    lot_status: Mapped[str] = mapped_column(String(30), nullable=False)
    # fx_buy_lots.currency_code: USD/JPY처럼 이 매수 로트가 보유한 통화 코드입니다.
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD")
    buy_date: Mapped[date] = mapped_column(nullable=False)
    buy_krw_amount: Mapped[int] = mapped_column(KRWAmount, nullable=False)
    buy_exchange_rate: Mapped[Decimal] = mapped_column(ExchangeRate, nullable=False)
    usd_amount: Mapped[Decimal] = mapped_column(USDNumeric, nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    lock_version: Mapped[int] = mapped_column(nullable=False, server_default="1")

    __table_args__ = (
        Index("ix_fx_buy_lots_user_id", "user_id"),
        Index("ix_fx_buy_lots_user_id_currency_code", "user_id", "currency_code"),
        Index(
            "ix_fx_buy_lots_user_id_lot_status_is_active_is_deleted",
            "user_id",
            "currency_code",
            "lot_status",
            "is_active",
            "is_deleted",
        ),
        Index("ix_fx_buy_lots_user_id_buy_date", "user_id", "buy_date"),
        Index("ix_fx_buy_lots_user_id_buy_exchange_rate", "user_id", "buy_exchange_rate"),
        Index("ix_fx_buy_lots_parent_buy_lot_id", "parent_buy_lot_id"),
        Index("ix_fx_buy_lots_root_buy_lot_id", "root_buy_lot_id"),
    )


class FxLotAllocation(Base):
    """매도 거래가 어떤 매수 로트를 얼마만큼 차감했는지 기록하는 연결 테이블입니다."""

    __tablename__ = "fx_lot_allocations"

    lot_allocation_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    sell_transaction_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fx_sell_transactions.sell_transaction_id"), nullable=False
    )
    source_buy_lot_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fx_buy_lots.buy_lot_id"), nullable=False
    )
    closed_buy_lot_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fx_buy_lots.buy_lot_id"), nullable=False
    )
    remaining_buy_lot_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("fx_buy_lots.buy_lot_id"), nullable=True
    )
    allocated_usd_amount: Mapped[Decimal] = mapped_column(USDNumeric, nullable=False)
    allocated_buy_krw_amount: Mapped[int] = mapped_column(KRWAmount, nullable=False)
    allocated_sell_krw_amount: Mapped[int] = mapped_column(KRWAmount, nullable=False)
    real_profit_krw: Mapped[int] = mapped_column(KRWAmount, nullable=False)
    display_profit_krw: Mapped[int] = mapped_column(KRWAmount, nullable=False)
    exchange_diff: Mapped[Decimal] = mapped_column(ExchangeRate, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True
    )

    __table_args__ = (
        Index("ix_fx_lot_allocations_sell_transaction_id", "sell_transaction_id"),
        Index("ix_fx_lot_allocations_source_buy_lot_id", "source_buy_lot_id"),
        Index("ix_fx_lot_allocations_closed_buy_lot_id", "closed_buy_lot_id"),
        Index("ix_fx_lot_allocations_remaining_buy_lot_id", "remaining_buy_lot_id"),
    )


class FxLotEvent(Base):
    """로트 생성, 매도 차감, 취소 복원 같은 FX 장부 이벤트를 감사 로그로 저장합니다."""

    __tablename__ = "fx_lot_events"

    lot_event_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="completed"
    )
    root_buy_lot_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("fx_buy_lots.buy_lot_id"), nullable=True
    )
    sell_transaction_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("fx_sell_transactions.sell_transaction_id"), nullable=True
    )
    lot_allocation_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("fx_lot_allocations.lot_allocation_id"), nullable=True
    )
    source_buy_lot_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("fx_buy_lots.buy_lot_id"), nullable=True
    )
    closed_buy_lot_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("fx_buy_lots.buy_lot_id"), nullable=True
    )
    remaining_buy_lot_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("fx_buy_lots.buy_lot_id"), nullable=True
    )
    restored_buy_lot_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("fx_buy_lots.buy_lot_id"), nullable=True
    )
    related_event_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("fx_lot_events.lot_event_id"), nullable=True
    )
    event_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True
    )

    __table_args__ = (
        Index("ix_fx_lot_events_user_id_created_at", "user_id", "created_at"),
        Index("ix_fx_lot_events_root_buy_lot_id_created_at", "root_buy_lot_id", "created_at"),
        Index("ix_fx_lot_events_sell_transaction_id", "sell_transaction_id"),
        Index("ix_fx_lot_events_lot_allocation_id", "lot_allocation_id"),
        Index("ix_fx_lot_events_source_buy_lot_id", "source_buy_lot_id"),
        Index("ix_fx_lot_events_restored_buy_lot_id", "restored_buy_lot_id"),
        Index("ix_fx_lot_events_event_type", "event_type"),
    )

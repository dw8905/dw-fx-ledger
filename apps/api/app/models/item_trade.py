from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Index, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import (
    ActiveMixin,
    AuditUserMixin,
    Base,
    KRWAmount,
    SoftDeleteMixin,
    String,
    Text,
    TimestampMixin,
)


class ItemTrade(TimestampMixin, AuditUserMixin, SoftDeleteMixin, Base):
    __tablename__ = "item_trades"

    item_trade_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    item_code_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("item_codes.item_code_id"), nullable=True
    )
    trade_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default="buy")
    trade_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    item_name: Mapped[str] = mapped_column(String(120), nullable=False)
    buy_date: Mapped[date] = mapped_column(nullable=False)
    buy_unit_price: Mapped[int] = mapped_column(KRWAmount, nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    fee_rate: Mapped[Decimal] = mapped_column(Numeric(8, 6), nullable=False)
    minimum_profitable_unit_price: Mapped[int] = mapped_column(KRWAmount, nullable=False)
    average_buy_unit_price: Mapped[int | None] = mapped_column(KRWAmount, nullable=True)
    inventory_quantity_after: Mapped[int | None] = mapped_column(nullable=True)
    inventory_value_after: Mapped[int | None] = mapped_column(KRWAmount, nullable=True)
    sell_date: Mapped[date | None] = mapped_column(nullable=True)
    sell_unit_price: Mapped[int | None] = mapped_column(KRWAmount, nullable=True)
    total_buy_amount: Mapped[int] = mapped_column(KRWAmount, nullable=False)
    total_sell_amount: Mapped[int | None] = mapped_column(KRWAmount, nullable=True)
    fee_amount: Mapped[int | None] = mapped_column(KRWAmount, nullable=True)
    net_sell_amount: Mapped[int | None] = mapped_column(KRWAmount, nullable=True)
    profit_amount: Mapped[int | None] = mapped_column(KRWAmount, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_item_trades_item_code_id", "item_code_id"),
        Index("ix_item_trades_user_id_item_code_id", "user_id", "item_code_id"),
        Index("ix_item_trades_trade_type", "trade_type"),
        Index("ix_item_trades_trade_status", "trade_status"),
        Index("ix_item_trades_user_id_buy_date", "user_id", "buy_date"),
        Index("ix_item_trades_user_id_created_at", "user_id", "created_at"),
        Index("ix_item_trades_item_name", "item_name"),
    )


class ItemCode(TimestampMixin, AuditUserMixin, ActiveMixin, SoftDeleteMixin, Base):
    __tablename__ = "item_codes"

    item_code_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=True)
    item_code: Mapped[str] = mapped_column(String(80), nullable=False)
    item_name: Mapped[str] = mapped_column(String(120), nullable=False)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_item_codes_user_id", "user_id"),
        Index(
            "ix_item_codes_item_code_active",
            "item_code",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
        Index("ix_item_codes_is_active", "is_active"),
        Index("ix_item_codes_item_name", "item_name"),
    )

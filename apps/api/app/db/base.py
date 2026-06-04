from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class AuditUserMixin:
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True
    )
    updated_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True
    )


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(nullable=False, server_default="false")


class ActiveMixin:
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default="true")


PK = BigInteger
KRWAmount = BigInteger
USDNumeric = Numeric(18, 6)
ExchangeRate = Numeric(18, 6)

__all__ = [
    "ActiveMixin",
    "AuditUserMixin",
    "Base",
    "ExchangeRate",
    "INET",
    "Integer",
    "KRWAmount",
    "PK",
    "SoftDeleteMixin",
    "String",
    "Text",
    "TimestampMixin",
    "USDNumeric",
    "Decimal",
]

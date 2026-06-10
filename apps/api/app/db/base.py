from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """모든 SQLAlchemy ORM 모델이 상속하는 공통 선언 베이스입니다."""

    pass


class TimestampMixin:
    """생성일/수정일을 공통 컬럼으로 제공하는 믹스인입니다."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class AuditUserMixin:
    """레코드를 생성/수정한 사용자 ID를 남기기 위한 공통 컬럼 묶음입니다."""

    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True
    )
    updated_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True
    )


class SoftDeleteMixin:
    """물리 삭제 대신 숨김 처리할 수 있도록 is_deleted 플래그를 제공합니다."""

    is_deleted: Mapped[bool] = mapped_column(nullable=False, server_default="false")


class ActiveMixin:
    """마스터 데이터처럼 활성/비활성을 구분해야 하는 테이블에 쓰는 믹스인입니다."""

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

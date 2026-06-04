from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import ActiveMixin, Base, INET, SoftDeleteMixin, String, Text, TimestampMixin


class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    login_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="active")
    default_allocation_strategy: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="highest_rate_first"
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True
    )
    updated_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True
    )

    roles: Mapped[list["UserRole"]] = relationship(
        back_populates="user", foreign_keys="UserRole.user_id"
    )

    __table_args__ = (
        Index("ix_users_user_status", "user_status"),
        Index("ix_users_is_deleted", "is_deleted"),
    )


class Role(TimestampMixin, ActiveMixin, SoftDeleteMixin, Base):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    role_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True
    )
    updated_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True
    )

    users: Mapped[list["UserRole"]] = relationship(back_populates="role")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("roles.role_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True
    )

    user: Mapped[User] = relationship(back_populates="roles", foreign_keys=[user_id])
    role: Mapped[Role] = relationship(back_populates="users")

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_id_role_id"),
        Index("ix_user_roles_user_id", "user_id"),
        Index("ix_user_roles_role_id", "role_id"),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    refresh_token_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=True
    )

    __table_args__ = (
        Index("ix_refresh_tokens_user_id", "user_id"),
        Index("ix_refresh_tokens_expires_at", "expires_at"),
        Index("ix_refresh_tokens_revoked_at", "revoked_at"),
    )

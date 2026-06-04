"""initial erd

Revision ID: 20260604_0001
Revises:
Create Date: 2026-06-04
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260604_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _audit_fk(table_name: str, column_name: str) -> None:
    op.create_foreign_key(
        f"fk_{table_name}_{column_name}_users",
        table_name,
        "users",
        [column_name],
        ["user_id"],
    )


def _drop_audit_fk(table_name: str, column_name: str) -> None:
    op.drop_constraint(f"fk_{table_name}_{column_name}_users", table_name, type_="foreignkey")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("login_id", sa.String(length=100), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("user_status", sa.String(length=30), server_default="active", nullable=False),
        sa.Column(
            "default_allocation_strategy",
            sa.String(length=50),
            server_default="highest_rate_first",
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("login_id"),
    )
    op.create_index("ix_users_user_status", "users", ["user_status"])
    op.create_index("ix_users_is_deleted", "users", ["is_deleted"])

    op.create_table(
        "roles",
        sa.Column("role_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("role_code", sa.String(length=50), nullable=False),
        sa.Column("role_name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("role_id"),
        sa.UniqueConstraint("role_code"),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_role_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("user_role_id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_id_role_id"),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("refresh_token_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("refresh_token_id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])
    op.create_index("ix_refresh_tokens_revoked_at", "refresh_tokens", ["revoked_at"])

    op.create_table(
        "board_posts",
        sa.Column("post_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("view_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("post_status", sa.String(length=30), server_default="published", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("post_id"),
    )
    op.create_index("ix_board_posts_author_id", "board_posts", ["author_id"])
    op.create_index("ix_board_posts_created_at", "board_posts", ["created_at"])
    op.create_index("ix_board_posts_is_deleted_created_at", "board_posts", ["is_deleted", "created_at"])

    op.create_table(
        "fx_sell_transactions",
        sa.Column("sell_transaction_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("sell_date", sa.Date(), nullable=False),
        sa.Column("sell_usd_amount", sa.Numeric(18, 6), nullable=False),
        sa.Column("sell_exchange_rate", sa.Numeric(18, 6), nullable=False),
        sa.Column("allocation_strategy", sa.String(length=50), nullable=False),
        sa.Column("transaction_status", sa.String(length=30), server_default="completed", nullable=False),
        sa.Column("total_buy_krw_amount", sa.BigInteger(), nullable=False),
        sa.Column("total_sell_krw_amount", sa.BigInteger(), nullable=False),
        sa.Column("total_real_profit_krw", sa.BigInteger(), nullable=False),
        sa.Column("total_display_profit_krw", sa.BigInteger(), nullable=False),
        sa.Column("memo", sa.Text(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("sell_transaction_id"),
    )
    op.create_index("ix_fx_sell_transactions_user_id", "fx_sell_transactions", ["user_id"])
    op.create_index(
        "ix_fx_sell_transactions_user_id_sell_date",
        "fx_sell_transactions",
        ["user_id", "sell_date"],
    )
    op.create_index(
        "ix_fx_sell_transactions_allocation_strategy",
        "fx_sell_transactions",
        ["allocation_strategy"],
    )
    op.create_index(
        "ix_fx_sell_transactions_transaction_status",
        "fx_sell_transactions",
        ["transaction_status"],
    )

    op.create_table(
        "fx_buy_lots",
        sa.Column("buy_lot_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("parent_buy_lot_id", sa.BigInteger(), nullable=True),
        sa.Column("root_buy_lot_id", sa.BigInteger(), nullable=True),
        sa.Column("lot_status", sa.String(length=30), nullable=False),
        sa.Column("buy_date", sa.Date(), nullable=False),
        sa.Column("buy_krw_amount", sa.BigInteger(), nullable=False),
        sa.Column("buy_exchange_rate", sa.Numeric(18, 6), nullable=False),
        sa.Column("usd_amount", sa.Numeric(18, 6), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("lock_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["parent_buy_lot_id"], ["fx_buy_lots.buy_lot_id"]),
        sa.ForeignKeyConstraint(["root_buy_lot_id"], ["fx_buy_lots.buy_lot_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("buy_lot_id"),
    )
    op.create_index("ix_fx_buy_lots_user_id", "fx_buy_lots", ["user_id"])
    op.create_index(
        "ix_fx_buy_lots_user_id_lot_status_is_active_is_deleted",
        "fx_buy_lots",
        ["user_id", "lot_status", "is_active", "is_deleted"],
    )
    op.create_index("ix_fx_buy_lots_user_id_buy_date", "fx_buy_lots", ["user_id", "buy_date"])
    op.create_index(
        "ix_fx_buy_lots_user_id_buy_exchange_rate",
        "fx_buy_lots",
        ["user_id", "buy_exchange_rate"],
    )
    op.create_index("ix_fx_buy_lots_parent_buy_lot_id", "fx_buy_lots", ["parent_buy_lot_id"])
    op.create_index("ix_fx_buy_lots_root_buy_lot_id", "fx_buy_lots", ["root_buy_lot_id"])
    op.create_table(
        "fx_lot_allocations",
        sa.Column("lot_allocation_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("sell_transaction_id", sa.BigInteger(), nullable=False),
        sa.Column("source_buy_lot_id", sa.BigInteger(), nullable=False),
        sa.Column("closed_buy_lot_id", sa.BigInteger(), nullable=False),
        sa.Column("remaining_buy_lot_id", sa.BigInteger(), nullable=True),
        sa.Column("allocated_usd_amount", sa.Numeric(18, 6), nullable=False),
        sa.Column("allocated_buy_krw_amount", sa.BigInteger(), nullable=False),
        sa.Column("allocated_sell_krw_amount", sa.BigInteger(), nullable=False),
        sa.Column("real_profit_krw", sa.BigInteger(), nullable=False),
        sa.Column("display_profit_krw", sa.BigInteger(), nullable=False),
        sa.Column("exchange_diff", sa.Numeric(18, 6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["closed_buy_lot_id"], ["fx_buy_lots.buy_lot_id"]),
        sa.ForeignKeyConstraint(["remaining_buy_lot_id"], ["fx_buy_lots.buy_lot_id"]),
        sa.ForeignKeyConstraint(["sell_transaction_id"], ["fx_sell_transactions.sell_transaction_id"]),
        sa.ForeignKeyConstraint(["source_buy_lot_id"], ["fx_buy_lots.buy_lot_id"]),
        sa.PrimaryKeyConstraint("lot_allocation_id"),
    )
    op.create_index(
        "ix_fx_lot_allocations_sell_transaction_id",
        "fx_lot_allocations",
        ["sell_transaction_id"],
    )
    op.create_index(
        "ix_fx_lot_allocations_source_buy_lot_id",
        "fx_lot_allocations",
        ["source_buy_lot_id"],
    )
    op.create_index(
        "ix_fx_lot_allocations_closed_buy_lot_id",
        "fx_lot_allocations",
        ["closed_buy_lot_id"],
    )
    op.create_index(
        "ix_fx_lot_allocations_remaining_buy_lot_id",
        "fx_lot_allocations",
        ["remaining_buy_lot_id"],
    )

    audit_columns = {
        "users": ["created_by", "updated_by"],
        "roles": ["created_by", "updated_by"],
        "user_roles": ["created_by"],
        "refresh_tokens": ["created_by"],
        "board_posts": ["created_by", "updated_by"],
        "fx_sell_transactions": ["created_by", "updated_by"],
        "fx_buy_lots": ["created_by", "updated_by"],
        "fx_lot_allocations": ["created_by"],
    }
    for table_name, column_names in audit_columns.items():
        for column_name in column_names:
            _audit_fk(table_name, column_name)


def downgrade() -> None:
    audit_columns = {
        "fx_lot_allocations": ["created_by"],
        "fx_buy_lots": ["created_by", "updated_by"],
        "fx_sell_transactions": ["created_by", "updated_by"],
        "board_posts": ["created_by", "updated_by"],
        "refresh_tokens": ["created_by"],
        "user_roles": ["created_by"],
        "roles": ["created_by", "updated_by"],
        "users": ["created_by", "updated_by"],
    }
    for table_name, column_names in audit_columns.items():
        for column_name in column_names:
            _drop_audit_fk(table_name, column_name)

    op.drop_table("fx_lot_allocations")
    op.drop_table("fx_buy_lots")
    op.drop_table("fx_sell_transactions")
    op.drop_table("board_posts")
    op.drop_table("refresh_tokens")
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.drop_table("users")

"""add item trades

Revision ID: 20260607_0003
Revises: 20260605_0002
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260607_0003"
down_revision: str | Sequence[str] | None = "20260605_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "item_trades",
        sa.Column("item_trade_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("item_name", sa.String(length=120), nullable=False),
        sa.Column("buy_date", sa.Date(), nullable=False),
        sa.Column("buy_unit_price", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("fee_rate", sa.Numeric(8, 6), nullable=False),
        sa.Column("minimum_profitable_unit_price", sa.BigInteger(), nullable=False),
        sa.Column("sell_date", sa.Date(), nullable=True),
        sa.Column("sell_unit_price", sa.BigInteger(), nullable=True),
        sa.Column("total_buy_amount", sa.BigInteger(), nullable=False),
        sa.Column("total_sell_amount", sa.BigInteger(), nullable=True),
        sa.Column("fee_amount", sa.BigInteger(), nullable=True),
        sa.Column("net_sell_amount", sa.BigInteger(), nullable=True),
        sa.Column("profit_amount", sa.BigInteger(), nullable=True),
        sa.Column("memo", sa.Text(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("item_trade_id"),
    )
    op.create_index("ix_item_trades_user_id_buy_date", "item_trades", ["user_id", "buy_date"])
    op.create_index("ix_item_trades_user_id_created_at", "item_trades", ["user_id", "created_at"])
    op.create_index("ix_item_trades_item_name", "item_trades", ["item_name"])


def downgrade() -> None:
    op.drop_index("ix_item_trades_item_name", table_name="item_trades")
    op.drop_index("ix_item_trades_user_id_created_at", table_name="item_trades")
    op.drop_index("ix_item_trades_user_id_buy_date", table_name="item_trades")
    op.drop_table("item_trades")

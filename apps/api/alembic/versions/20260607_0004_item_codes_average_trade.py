"""item codes average trade

Revision ID: 20260607_0004
Revises: 20260607_0003
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260607_0004"
down_revision: str | Sequence[str] | None = "20260607_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "item_codes",
        sa.Column("item_code_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("item_code", sa.String(length=80), nullable=False),
        sa.Column("item_name", sa.String(length=120), nullable=False),
        sa.Column("memo", sa.Text(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("item_code_id"),
    )
    op.create_index("ix_item_codes_user_id", "item_codes", ["user_id"])
    op.create_index("ix_item_codes_user_id_item_code", "item_codes", ["user_id", "item_code"], unique=True)
    op.create_index("ix_item_codes_item_name", "item_codes", ["item_name"])

    op.add_column("item_trades", sa.Column("item_code_id", sa.BigInteger(), nullable=True))
    op.add_column(
        "item_trades",
        sa.Column("trade_type", sa.String(length=20), server_default="buy", nullable=False),
    )
    op.add_column("item_trades", sa.Column("average_buy_unit_price", sa.BigInteger(), nullable=True))
    op.add_column("item_trades", sa.Column("inventory_quantity_after", sa.Integer(), nullable=True))
    op.add_column("item_trades", sa.Column("inventory_value_after", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_item_trades_item_code_id_item_codes",
        "item_trades",
        "item_codes",
        ["item_code_id"],
        ["item_code_id"],
    )
    op.create_index("ix_item_trades_item_code_id", "item_trades", ["item_code_id"])
    op.create_index("ix_item_trades_user_id_item_code_id", "item_trades", ["user_id", "item_code_id"])
    op.create_index("ix_item_trades_trade_type", "item_trades", ["trade_type"])

    op.execute(
        """
        INSERT INTO item_codes (user_id, item_code, item_name, created_by, updated_by)
        SELECT DISTINCT user_id, item_name, item_name, created_by, updated_by
        FROM item_trades
        WHERE item_name IS NOT NULL
        ON CONFLICT (user_id, item_code) DO NOTHING
        """
    )
    op.execute(
        """
        UPDATE item_trades AS trade
        SET item_code_id = code.item_code_id,
            average_buy_unit_price = trade.buy_unit_price,
            inventory_quantity_after = trade.quantity,
            inventory_value_after = trade.total_buy_amount
        FROM item_codes AS code
        WHERE code.user_id = trade.user_id
          AND code.item_code = trade.item_name
          AND trade.item_code_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_item_trades_trade_type", table_name="item_trades")
    op.drop_index("ix_item_trades_user_id_item_code_id", table_name="item_trades")
    op.drop_index("ix_item_trades_item_code_id", table_name="item_trades")
    op.drop_constraint("fk_item_trades_item_code_id_item_codes", "item_trades", type_="foreignkey")
    op.drop_column("item_trades", "inventory_value_after")
    op.drop_column("item_trades", "inventory_quantity_after")
    op.drop_column("item_trades", "average_buy_unit_price")
    op.drop_column("item_trades", "trade_type")
    op.drop_column("item_trades", "item_code_id")
    op.drop_index("ix_item_codes_item_name", table_name="item_codes")
    op.drop_index("ix_item_codes_user_id_item_code", table_name="item_codes")
    op.drop_index("ix_item_codes_user_id", table_name="item_codes")
    op.drop_table("item_codes")

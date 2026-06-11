"""add fx currency code

Revision ID: 20260611_0007
Revises: 20260607_0006
Create Date: 2026-06-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260611_0007"
down_revision: str | Sequence[str] | None = "20260607_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "fx_buy_lots",
        sa.Column("currency_code", sa.String(length=3), server_default="USD", nullable=False),
    )
    op.add_column(
        "fx_sell_transactions",
        sa.Column("currency_code", sa.String(length=3), server_default="USD", nullable=False),
    )
    op.create_index(
        "ix_fx_buy_lots_user_id_currency_code",
        "fx_buy_lots",
        ["user_id", "currency_code"],
    )
    op.create_index(
        "ix_fx_sell_transactions_user_id_currency_code",
        "fx_sell_transactions",
        ["user_id", "currency_code"],
    )
    op.drop_index(
        "ix_fx_buy_lots_user_id_lot_status_is_active_is_deleted",
        table_name="fx_buy_lots",
    )
    op.create_index(
        "ix_fx_buy_lots_user_id_lot_status_is_active_is_deleted",
        "fx_buy_lots",
        ["user_id", "currency_code", "lot_status", "is_active", "is_deleted"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fx_buy_lots_user_id_lot_status_is_active_is_deleted",
        table_name="fx_buy_lots",
    )
    op.create_index(
        "ix_fx_buy_lots_user_id_lot_status_is_active_is_deleted",
        "fx_buy_lots",
        ["user_id", "lot_status", "is_active", "is_deleted"],
    )
    op.drop_index("ix_fx_sell_transactions_user_id_currency_code", table_name="fx_sell_transactions")
    op.drop_index("ix_fx_buy_lots_user_id_currency_code", table_name="fx_buy_lots")
    op.drop_column("fx_sell_transactions", "currency_code")
    op.drop_column("fx_buy_lots", "currency_code")

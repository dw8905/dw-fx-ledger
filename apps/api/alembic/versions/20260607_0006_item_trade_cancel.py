"""item trade cancel

Revision ID: 20260607_0006
Revises: 20260607_0005
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260607_0006"
down_revision: str | Sequence[str] | None = "20260607_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "item_trades",
        sa.Column("trade_status", sa.String(length=20), server_default="active", nullable=False),
    )
    op.add_column("item_trades", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("item_trades", sa.Column("cancel_reason", sa.Text(), nullable=True))
    op.create_index("ix_item_trades_trade_status", "item_trades", ["trade_status"])


def downgrade() -> None:
    op.drop_index("ix_item_trades_trade_status", table_name="item_trades")
    op.drop_column("item_trades", "cancel_reason")
    op.drop_column("item_trades", "cancelled_at")
    op.drop_column("item_trades", "trade_status")

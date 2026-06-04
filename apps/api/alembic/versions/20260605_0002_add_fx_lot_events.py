"""add fx lot events

Revision ID: 20260605_0002
Revises: 20260604_0001
Create Date: 2026-06-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260605_0002"
down_revision: str | Sequence[str] | None = "20260604_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fx_lot_events",
        sa.Column("lot_event_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("event_status", sa.String(length=30), server_default="completed", nullable=False),
        sa.Column("root_buy_lot_id", sa.BigInteger(), nullable=True),
        sa.Column("sell_transaction_id", sa.BigInteger(), nullable=True),
        sa.Column("lot_allocation_id", sa.BigInteger(), nullable=True),
        sa.Column("source_buy_lot_id", sa.BigInteger(), nullable=True),
        sa.Column("closed_buy_lot_id", sa.BigInteger(), nullable=True),
        sa.Column("remaining_buy_lot_id", sa.BigInteger(), nullable=True),
        sa.Column("restored_buy_lot_id", sa.BigInteger(), nullable=True),
        sa.Column("related_event_id", sa.BigInteger(), nullable=True),
        sa.Column("event_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["closed_buy_lot_id"], ["fx_buy_lots.buy_lot_id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["lot_allocation_id"], ["fx_lot_allocations.lot_allocation_id"]),
        sa.ForeignKeyConstraint(["related_event_id"], ["fx_lot_events.lot_event_id"]),
        sa.ForeignKeyConstraint(["remaining_buy_lot_id"], ["fx_buy_lots.buy_lot_id"]),
        sa.ForeignKeyConstraint(["restored_buy_lot_id"], ["fx_buy_lots.buy_lot_id"]),
        sa.ForeignKeyConstraint(["root_buy_lot_id"], ["fx_buy_lots.buy_lot_id"]),
        sa.ForeignKeyConstraint(["sell_transaction_id"], ["fx_sell_transactions.sell_transaction_id"]),
        sa.ForeignKeyConstraint(["source_buy_lot_id"], ["fx_buy_lots.buy_lot_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("lot_event_id"),
    )
    op.create_index("ix_fx_lot_events_user_id_created_at", "fx_lot_events", ["user_id", "created_at"])
    op.create_index(
        "ix_fx_lot_events_root_buy_lot_id_created_at",
        "fx_lot_events",
        ["root_buy_lot_id", "created_at"],
    )
    op.create_index("ix_fx_lot_events_sell_transaction_id", "fx_lot_events", ["sell_transaction_id"])
    op.create_index("ix_fx_lot_events_lot_allocation_id", "fx_lot_events", ["lot_allocation_id"])
    op.create_index("ix_fx_lot_events_source_buy_lot_id", "fx_lot_events", ["source_buy_lot_id"])
    op.create_index("ix_fx_lot_events_restored_buy_lot_id", "fx_lot_events", ["restored_buy_lot_id"])
    op.create_index("ix_fx_lot_events_event_type", "fx_lot_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_fx_lot_events_event_type", table_name="fx_lot_events")
    op.drop_index("ix_fx_lot_events_restored_buy_lot_id", table_name="fx_lot_events")
    op.drop_index("ix_fx_lot_events_source_buy_lot_id", table_name="fx_lot_events")
    op.drop_index("ix_fx_lot_events_lot_allocation_id", table_name="fx_lot_events")
    op.drop_index("ix_fx_lot_events_sell_transaction_id", table_name="fx_lot_events")
    op.drop_index("ix_fx_lot_events_root_buy_lot_id_created_at", table_name="fx_lot_events")
    op.drop_index("ix_fx_lot_events_user_id_created_at", table_name="fx_lot_events")
    op.drop_table("fx_lot_events")

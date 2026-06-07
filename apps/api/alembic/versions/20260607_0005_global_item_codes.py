"""global item codes

Revision ID: 20260607_0005
Revises: 20260607_0004
Create Date: 2026-06-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260607_0005"
down_revision: str | Sequence[str] | None = "20260607_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("item_codes", sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False))
    op.drop_index("ix_item_codes_user_id_item_code", table_name="item_codes")
    op.alter_column("item_codes", "user_id", existing_type=sa.BigInteger(), nullable=True)

    op.execute(
        """
        WITH canonical AS (
            SELECT MIN(item_code_id) AS keep_id, item_code
            FROM item_codes
            WHERE is_deleted = false
            GROUP BY item_code
        )
        UPDATE item_trades AS trade
        SET item_code_id = canonical.keep_id
        FROM item_codes AS code
        JOIN canonical ON canonical.item_code = code.item_code
        WHERE trade.item_code_id = code.item_code_id
          AND code.item_code_id <> canonical.keep_id
        """
    )
    op.execute(
        """
        UPDATE item_codes AS code
        SET is_deleted = true,
            is_active = false
        FROM (
            SELECT item_code_id,
                   MIN(item_code_id) OVER (PARTITION BY item_code) AS keep_id
            FROM item_codes
            WHERE is_deleted = false
        ) AS ranked
        WHERE code.item_code_id = ranked.item_code_id
          AND ranked.item_code_id <> ranked.keep_id
        """
    )
    op.execute("UPDATE item_codes SET user_id = NULL WHERE is_deleted = false")
    op.create_index(
        "ix_item_codes_item_code_active",
        "item_codes",
        ["item_code"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )
    op.create_index("ix_item_codes_is_active", "item_codes", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_item_codes_is_active", table_name="item_codes")
    op.drop_index("ix_item_codes_item_code_active", table_name="item_codes")
    op.alter_column("item_codes", "user_id", existing_type=sa.BigInteger(), nullable=False)
    op.create_index("ix_item_codes_user_id_item_code", "item_codes", ["user_id", "item_code"], unique=True)
    op.drop_column("item_codes", "is_active")

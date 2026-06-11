"""add common codes and board type

Revision ID: 20260611_0008
Revises: 20260611_0007
Create Date: 2026-06-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260611_0008"
down_revision: str | Sequence[str] | None = "20260611_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "common_codes",
        sa.Column("common_code_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("code_group", sa.String(length=50), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("code_name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("common_code_id"),
        sa.UniqueConstraint("code_group", "code", name="uq_common_codes_group_code"),
    )
    op.create_index(
        "ix_common_codes_group_active_sort",
        "common_codes",
        ["code_group", "is_active", "sort_order"],
    )
    op.bulk_insert(
        sa.table(
            "common_codes",
            sa.column("code_group", sa.String()),
            sa.column("code", sa.String()),
            sa.column("code_name", sa.String()),
            sa.column("description", sa.Text()),
            sa.column("sort_order", sa.Integer()),
            sa.column("is_active", sa.Boolean()),
        ),
        [
            {
                "code_group": "board_type",
                "code": "general",
                "code_name": "일반 게시판",
                "description": "기본 게시글이 저장되는 일반 게시판 타입입니다.",
                "sort_order": 1,
                "is_active": True,
            }
        ],
    )
    op.add_column(
        "board_posts",
        sa.Column("board_type_code", sa.String(length=50), server_default="general", nullable=False),
    )
    op.create_index(
        "ix_board_posts_board_type_code_created_at",
        "board_posts",
        ["board_type_code", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_board_posts_board_type_code_created_at", table_name="board_posts")
    op.drop_column("board_posts", "board_type_code")
    op.drop_index("ix_common_codes_group_active_sort", table_name="common_codes")
    op.drop_table("common_codes")

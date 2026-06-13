"""add board comments

Revision ID: 20260613_0009
Revises: 20260611_0008
Create Date: 2026-06-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260613_0009"
down_revision: str | Sequence[str] | None = "20260611_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "board_comments",
        sa.Column("comment_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("post_id", sa.BigInteger(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("comment_status", sa.String(length=30), server_default="published", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["post_id"], ["board_posts.post_id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("comment_id"),
    )
    op.create_index(
        "ix_board_comments_post_id_created_at",
        "board_comments",
        ["post_id", "created_at"],
    )
    op.create_index("ix_board_comments_author_id", "board_comments", ["author_id"])
    op.create_index(
        "ix_board_comments_is_deleted_created_at",
        "board_comments",
        ["is_deleted", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_board_comments_is_deleted_created_at", table_name="board_comments")
    op.drop_index("ix_board_comments_author_id", table_name="board_comments")
    op.drop_index("ix_board_comments_post_id_created_at", table_name="board_comments")
    op.drop_table("board_comments")

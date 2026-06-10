from sqlalchemy import BigInteger, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import AuditUserMixin, Base, Integer, SoftDeleteMixin, String, Text, TimestampMixin


class BoardPost(TimestampMixin, AuditUserMixin, SoftDeleteMixin, Base):
    """게시판 글 본문, 작성자, 조회수, 게시 상태를 저장하는 모델입니다."""

    __tablename__ = "board_posts"

    post_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    post_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="published")

    __table_args__ = (
        Index("ix_board_posts_author_id", "author_id"),
        Index("ix_board_posts_created_at", "created_at"),
        Index("ix_board_posts_is_deleted_created_at", "is_deleted", "created_at"),
    )

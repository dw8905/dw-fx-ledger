from sqlalchemy import BigInteger, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import AuditUserMixin, Base, Integer, SoftDeleteMixin, String, Text, TimestampMixin


class BoardPost(TimestampMixin, AuditUserMixin, SoftDeleteMixin, Base):
    """게시판 글 본문, 작성자, 조회수, 게시 상태를 저장하는 모델입니다."""

    __tablename__ = "board_posts"

    # board_posts.post_id: 게시글 한 건을 식별하는 내부 PK입니다.
    post_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # board_posts.author_id: 게시글을 작성한 users.user_id입니다.
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=False
    )
    # board_posts.board_type_code: common_codes(code_group='board_type')의 code 값으로 게시판 종류를 구분합니다.
    board_type_code: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="general"
    )
    # board_posts.title: 목록과 상세 화면에 표시하는 게시글 제목입니다.
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # board_posts.content: 상세 화면에 표시하는 게시글 본문입니다.
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # board_posts.view_count: 상세 조회가 성공할 때마다 1씩 증가하는 조회수입니다.
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    # board_posts.post_status: published/deleted 등 게시글의 공개 상태를 저장합니다.
    post_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="published")

    __table_args__ = (
        Index("ix_board_posts_author_id", "author_id"),
        Index("ix_board_posts_board_type_code_created_at", "board_type_code", "created_at"),
        Index("ix_board_posts_created_at", "created_at"),
        Index("ix_board_posts_is_deleted_created_at", "is_deleted", "created_at"),
    )


class BoardComment(TimestampMixin, AuditUserMixin, SoftDeleteMixin, Base):
    """게시글에 달린 댓글 본문과 작성자를 저장하는 모델입니다."""

    __tablename__ = "board_comments"

    comment_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("board_posts.post_id"), nullable=False
    )
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    comment_status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="published"
    )

    __table_args__ = (
        Index("ix_board_comments_post_id_created_at", "post_id", "created_at"),
        Index("ix_board_comments_author_id", "author_id"),
        Index("ix_board_comments_is_deleted_created_at", "is_deleted", "created_at"),
    )

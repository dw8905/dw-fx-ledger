from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.auth import User
from app.models.board import BoardPost
from app.schemas.posts import (
    PostDetailResponse,
    PostListItem,
    PostListResponse,
    PostMutationResponse,
)
from app.services.roles import ADMIN_ROLE_CODE, user_has_role

PUBLISHED = "published"
DELETED = "deleted"


def is_admin(user: User) -> bool:
    """게시글 수정/삭제 권한 판단에서 현재 사용자가 admin인지 확인합니다."""

    return user_has_role(user, ADMIN_ROLE_CODE)


def can_mutate_post(user: User, post: BoardPost) -> bool:
    """작성자 본인 또는 admin만 게시글을 수정/삭제할 수 있게 판정합니다."""

    return post.author_id == user.user_id or is_admin(user)


def _base_visible_posts_query() -> Select[tuple[BoardPost, str]]:
    """일반 사용자가 볼 수 있는 published 게시글과 작성자명을 함께 조회하는 기본 쿼리입니다."""

    return (
        select(BoardPost, User.display_name)
        .join(User, User.user_id == BoardPost.author_id)
        .where(BoardPost.is_deleted.is_(False), BoardPost.post_status == PUBLISHED)
    )


def list_posts(db: Session, *, page: int, size: int, keyword: str | None = None) -> PostListResponse:
    """게시판 목록에서 검색어와 페이지네이션을 적용해 공개 게시글만 반환합니다."""

    filters = [BoardPost.is_deleted.is_(False), BoardPost.post_status == PUBLISHED]
    if keyword:
        pattern = f"%{keyword.strip()}%"
        filters.append(
            or_(
                BoardPost.title.ilike(pattern),
                BoardPost.content.ilike(pattern),
                User.display_name.ilike(pattern),
            )
        )

    total_count = db.scalar(
        select(func.count())
        .select_from(BoardPost)
        .join(User, User.user_id == BoardPost.author_id)
        .where(*filters)
    )
    rows = db.execute(
        _base_visible_posts_query()
        .where(*filters)
        .order_by(BoardPost.created_at.desc(), BoardPost.post_id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()

    return PostListResponse(
        items=[
            PostListItem(
                postId=post.post_id,
                title=post.title,
                authorName=author_name,
                viewCount=post.view_count,
                createdAt=post.created_at,
            )
            for post, author_name in rows
        ],
        page=page,
        size=size,
        totalCount=total_count or 0,
    )


def get_visible_post_with_author(db: Session, post_id: int) -> tuple[BoardPost, str] | None:
    """상세 조회 가능한 게시글 하나와 작성자 표시명을 함께 찾습니다."""

    return db.execute(
        _base_visible_posts_query().where(BoardPost.post_id == post_id)
    ).one_or_none()


def get_post_detail(db: Session, post_id: int) -> PostDetailResponse | None:
    """게시글 상세를 조회하면서 실제 상세 진입 1회당 조회수를 1 증가시킵니다."""

    row = get_visible_post_with_author(db, post_id)
    if row is None:
        return None

    post, author_name = row
    post.view_count += 1
    db.flush()
    db.refresh(post)
    return to_detail_response(post, author_name)


def get_post_for_mutation(db: Session, post_id: int) -> BoardPost | None:
    """수정/삭제 대상이 되는 공개 게시글 원본 모델을 조회합니다."""

    return db.scalar(
        select(BoardPost).where(
            BoardPost.post_id == post_id,
            BoardPost.is_deleted.is_(False),
            BoardPost.post_status == PUBLISHED,
        )
    )


def create_post(db: Session, *, title: str, content: str, author: User) -> PostMutationResponse:
    """현재 사용자를 작성자로 하여 새 게시글을 생성합니다."""

    post = BoardPost(
        author_id=author.user_id,
        title=title,
        content=content,
        created_by=author.user_id,
        updated_by=author.user_id,
    )
    db.add(post)
    db.flush()
    db.refresh(post)
    return to_mutation_response(post, author.display_name)


def update_post(
    db: Session,
    *,
    post: BoardPost,
    title: str,
    content: str,
    updated_by: User,
) -> PostMutationResponse:
    """권한 확인이 끝난 게시글의 제목과 본문을 최신 입력값으로 갱신합니다."""

    post.title = title
    post.content = content
    post.updated_by = updated_by.user_id
    db.flush()
    db.refresh(post)
    author_name = db.scalar(select(User.display_name).where(User.user_id == post.author_id)) or ""
    return to_mutation_response(post, author_name)


def delete_post(db: Session, *, post: BoardPost, deleted_by: User) -> None:
    """게시글을 물리 삭제하지 않고 deleted 상태로 전환합니다."""

    post.is_deleted = True
    post.post_status = DELETED
    post.updated_by = deleted_by.user_id
    db.flush()


def to_detail_response(post: BoardPost, author_name: str) -> PostDetailResponse:
    """BoardPost 모델을 상세 화면 응답 스키마로 변환합니다."""

    return PostDetailResponse(
        postId=post.post_id,
        title=post.title,
        content=post.content,
        authorId=post.author_id,
        authorName=author_name,
        viewCount=post.view_count,
        postStatus=post.post_status,
        createdAt=post.created_at,
        updatedAt=post.updated_at,
    )


def to_mutation_response(post: BoardPost, author_name: str) -> PostMutationResponse:
    """생성/수정 직후 재사용할 게시글 응답 스키마로 변환합니다."""

    return PostMutationResponse(
        postId=post.post_id,
        title=post.title,
        content=post.content,
        authorId=post.author_id,
        authorName=author_name,
        viewCount=post.view_count,
        postStatus=post.post_status,
        createdAt=post.created_at,
        updatedAt=post.updated_at,
    )

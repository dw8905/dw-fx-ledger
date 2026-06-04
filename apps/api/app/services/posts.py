from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.auth import User
from app.models.board import BoardPost
from app.schemas.posts import (
    PostDetailResponse,
    PostListItem,
    PostListResponse,
    PostMutationResponse,
)

PUBLISHED = "published"
DELETED = "deleted"


def is_admin(user: User) -> bool:
    return any(user_role.role and user_role.role.role_code == "admin" for user_role in user.roles)


def can_mutate_post(user: User, post: BoardPost) -> bool:
    return post.author_id == user.user_id or is_admin(user)


def _base_visible_posts_query() -> Select[tuple[BoardPost, str]]:
    return (
        select(BoardPost, User.display_name)
        .join(User, User.user_id == BoardPost.author_id)
        .where(BoardPost.is_deleted.is_(False), BoardPost.post_status == PUBLISHED)
    )


def list_posts(db: Session, *, page: int, size: int) -> PostListResponse:
    total_count = db.scalar(
        select(func.count())
        .select_from(BoardPost)
        .where(BoardPost.is_deleted.is_(False), BoardPost.post_status == PUBLISHED)
    )
    rows = db.execute(
        _base_visible_posts_query()
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
    return db.execute(
        _base_visible_posts_query().where(BoardPost.post_id == post_id)
    ).one_or_none()


def get_post_detail(db: Session, post_id: int) -> PostDetailResponse | None:
    row = get_visible_post_with_author(db, post_id)
    if row is None:
        return None

    post, author_name = row
    post.view_count += 1
    db.flush()
    db.refresh(post)
    return to_detail_response(post, author_name)


def get_post_for_mutation(db: Session, post_id: int) -> BoardPost | None:
    return db.scalar(
        select(BoardPost).where(
            BoardPost.post_id == post_id,
            BoardPost.is_deleted.is_(False),
            BoardPost.post_status == PUBLISHED,
        )
    )


def create_post(db: Session, *, title: str, content: str, author: User) -> PostMutationResponse:
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
    post.title = title
    post.content = content
    post.updated_by = updated_by.user_id
    db.flush()
    db.refresh(post)
    author_name = db.scalar(select(User.display_name).where(User.user_id == post.author_id)) or ""
    return to_mutation_response(post, author_name)


def delete_post(db: Session, *, post: BoardPost, deleted_by: User) -> None:
    post.is_deleted = True
    post.post_status = DELETED
    post.updated_by = deleted_by.user_id
    db.flush()


def to_detail_response(post: BoardPost, author_name: str) -> PostDetailResponse:
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

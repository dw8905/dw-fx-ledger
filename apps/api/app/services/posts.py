from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.auth import User
from app.models.board import BoardPost
from app.models.common import CommonCode
from app.schemas.posts import (
    BoardTypeItem,
    PostDetailResponse,
    PostListItem,
    PostListResponse,
    PostMutationResponse,
)
from app.services.roles import ADMIN_ROLE_CODE, user_has_role

PUBLISHED = "published"
DELETED = "deleted"
BOARD_TYPE_GROUP = "board_type"
DEFAULT_BOARD_TYPE_CODE = "general"


class InvalidBoardTypeError(ValueError):
    """요청한 게시판 타입 코드가 공통코드에 없거나 비활성일 때 사용합니다."""


def is_admin(user: User) -> bool:
    """게시글 수정/삭제 권한 판단에서 현재 사용자가 admin인지 확인합니다."""

    return user_has_role(user, ADMIN_ROLE_CODE)


def can_mutate_post(user: User, post: BoardPost) -> bool:
    """작성자 본인 또는 admin만 게시글을 수정/삭제할 수 있게 판정합니다."""

    return post.author_id == user.user_id or is_admin(user)


def normalize_board_type_code(board_type_code: str | None) -> str:
    """빈 게시판 타입 입력을 기본 게시판 코드로 치환합니다."""

    return (board_type_code or DEFAULT_BOARD_TYPE_CODE).strip() or DEFAULT_BOARD_TYPE_CODE


def get_active_board_type(db: Session, board_type_code: str) -> CommonCode | None:
    """common_codes에서 활성화된 게시판 타입 코드 한 건을 조회합니다."""

    return db.scalar(
        select(CommonCode).where(
            CommonCode.code_group == BOARD_TYPE_GROUP,
            CommonCode.code == board_type_code,
            CommonCode.is_active.is_(True),
        )
    )


def require_active_board_type(db: Session, board_type_code: str | None) -> CommonCode:
    """요청 게시판 타입이 유효한지 검증하고 없으면 명시적인 예외를 발생시킵니다."""

    normalized_code = normalize_board_type_code(board_type_code)
    board_type = get_active_board_type(db, normalized_code)
    if board_type is None:
        raise InvalidBoardTypeError(f"Invalid board type: {normalized_code}")
    return board_type


def list_board_types(db: Session) -> list[BoardTypeItem]:
    """프론트가 게시판 타입 선택 UI를 만들 수 있도록 활성 공통코드 목록을 반환합니다."""

    rows = db.scalars(
        select(CommonCode)
        .where(CommonCode.code_group == BOARD_TYPE_GROUP, CommonCode.is_active.is_(True))
        .order_by(CommonCode.sort_order.asc(), CommonCode.code.asc())
    ).all()
    return [BoardTypeItem(code=row.code, name=row.code_name) for row in rows]


def board_type_name_or_code(board_type_code: str, code_name: str | None) -> str:
    """공통코드 이름이 없을 때도 화면이 깨지지 않도록 코드값을 대체 이름으로 사용합니다."""

    return code_name or board_type_code


def _base_visible_posts_query() -> Select[tuple[BoardPost, str, str | None]]:
    """일반 사용자가 볼 수 있는 published 게시글과 작성자명을 함께 조회하는 기본 쿼리입니다."""

    return (
        select(BoardPost, User.display_name, CommonCode.code_name)
        .join(User, User.user_id == BoardPost.author_id)
        .outerjoin(
            CommonCode,
            and_(
                CommonCode.code_group == BOARD_TYPE_GROUP,
                CommonCode.code == BoardPost.board_type_code,
            ),
        )
        .where(BoardPost.is_deleted.is_(False), BoardPost.post_status == PUBLISHED)
    )


def list_posts(
    db: Session,
    *,
    page: int,
    size: int,
    keyword: str | None = None,
    board_type_code: str | None = None,
) -> PostListResponse:
    """게시판 목록에서 검색어와 페이지네이션을 적용해 공개 게시글만 반환합니다."""

    board_type = require_active_board_type(db, board_type_code)
    filters = [
        BoardPost.is_deleted.is_(False),
        BoardPost.post_status == PUBLISHED,
        BoardPost.board_type_code == board_type.code,
    ]
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
                boardTypeCode=post.board_type_code,
                boardTypeName=board_type_name_or_code(post.board_type_code, board_type_name),
                title=post.title,
                authorName=author_name,
                viewCount=post.view_count,
                createdAt=post.created_at,
            )
            for post, author_name, board_type_name in rows
        ],
        page=page,
        size=size,
        totalCount=total_count or 0,
    )


def get_visible_post_with_author(db: Session, post_id: int) -> tuple[BoardPost, str, str | None] | None:
    """상세 조회 가능한 게시글 하나와 작성자 표시명을 함께 찾습니다."""

    return db.execute(
        _base_visible_posts_query().where(BoardPost.post_id == post_id)
    ).one_or_none()


def get_post_detail(db: Session, post_id: int) -> PostDetailResponse | None:
    """게시글 상세를 조회하면서 실제 상세 진입 1회당 조회수를 1 증가시킵니다."""

    row = get_visible_post_with_author(db, post_id)
    if row is None:
        return None

    post, author_name, board_type_name = row
    post.view_count += 1
    db.flush()
    db.refresh(post)
    return to_detail_response(post, author_name, board_type_name)


def get_post_for_mutation(db: Session, post_id: int) -> BoardPost | None:
    """수정/삭제 대상이 되는 공개 게시글 원본 모델을 조회합니다."""

    return db.scalar(
        select(BoardPost).where(
            BoardPost.post_id == post_id,
            BoardPost.is_deleted.is_(False),
            BoardPost.post_status == PUBLISHED,
        )
    )


def create_post(
    db: Session,
    *,
    title: str,
    content: str,
    author: User,
    board_type_code: str | None = None,
) -> PostMutationResponse:
    """현재 사용자를 작성자로 하여 새 게시글을 생성합니다."""

    board_type = require_active_board_type(db, board_type_code)
    post = BoardPost(
        author_id=author.user_id,
        board_type_code=board_type.code,
        title=title,
        content=content,
        created_by=author.user_id,
        updated_by=author.user_id,
    )
    db.add(post)
    db.flush()
    db.refresh(post)
    return to_mutation_response(post, author.display_name, board_type.code_name)


def update_post(
    db: Session,
    *,
    post: BoardPost,
    title: str,
    content: str,
    board_type_code: str | None,
    updated_by: User,
) -> PostMutationResponse:
    """권한 확인이 끝난 게시글의 제목과 본문을 최신 입력값으로 갱신합니다."""

    board_type_name: str | None = None
    if board_type_code is not None:
        board_type = require_active_board_type(db, board_type_code)
        post.board_type_code = board_type.code
        board_type_name = board_type.code_name

    post.title = title
    post.content = content
    post.updated_by = updated_by.user_id
    db.flush()
    db.refresh(post)
    author_name = db.scalar(select(User.display_name).where(User.user_id == post.author_id)) or ""
    if board_type_name is None:
        board_type_name = db.scalar(
            select(CommonCode.code_name).where(
                CommonCode.code_group == BOARD_TYPE_GROUP,
                CommonCode.code == post.board_type_code,
            )
        )
    return to_mutation_response(post, author_name, board_type_name)


def delete_post(db: Session, *, post: BoardPost, deleted_by: User) -> None:
    """게시글을 물리 삭제하지 않고 deleted 상태로 전환합니다."""

    post.is_deleted = True
    post.post_status = DELETED
    post.updated_by = deleted_by.user_id
    db.flush()


def to_detail_response(
    post: BoardPost,
    author_name: str,
    board_type_name: str | None,
) -> PostDetailResponse:
    """BoardPost 모델을 상세 화면 응답 스키마로 변환합니다."""

    return PostDetailResponse(
        postId=post.post_id,
        boardTypeCode=post.board_type_code,
        boardTypeName=board_type_name_or_code(post.board_type_code, board_type_name),
        title=post.title,
        content=post.content,
        authorId=post.author_id,
        authorName=author_name,
        viewCount=post.view_count,
        postStatus=post.post_status,
        createdAt=post.created_at,
        updatedAt=post.updated_at,
    )


def to_mutation_response(
    post: BoardPost,
    author_name: str,
    board_type_name: str | None,
) -> PostMutationResponse:
    """생성/수정 직후 재사용할 게시글 응답 스키마로 변환합니다."""

    return PostMutationResponse(
        postId=post.post_id,
        boardTypeCode=post.board_type_code,
        boardTypeName=board_type_name_or_code(post.board_type_code, board_type_name),
        title=post.title,
        content=post.content,
        authorId=post.author_id,
        authorName=author_name,
        viewCount=post.view_count,
        postStatus=post.post_status,
        createdAt=post.created_at,
        updatedAt=post.updated_at,
    )

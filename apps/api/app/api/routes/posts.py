from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.schemas.posts import (
    BoardTypeItem,
    PostCommentCreateRequest,
    PostCommentDeleteResponse,
    PostCommentItem,
    PostCreateRequest,
    PostDeleteResponse,
    PostDetailResponse,
    PostListResponse,
    PostMutationResponse,
    PostUpdateRequest,
)
from app.services.posts import (
    InvalidBoardTypeError,
    can_mutate_comment,
    can_mutate_post,
    create_comment,
    create_post,
    delete_comment,
    delete_post,
    get_comment_for_mutation,
    get_post_detail,
    get_post_for_mutation,
    list_comments,
    list_board_types,
    list_posts,
    update_post,
)

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=PostListResponse)
def list_post_route(
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
    keyword: str | None = None,
    board_type_code: str | None = None,
) -> PostListResponse:
    """게시글 목록을 검색어와 페이지 조건에 맞춰 반환합니다."""

    try:
        return list_posts(db, page=page, size=size, keyword=keyword, board_type_code=board_type_code)
    except InvalidBoardTypeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/board-types", response_model=list[BoardTypeItem])
def list_board_types_route(db: Annotated[Session, Depends(get_db)]) -> list[BoardTypeItem]:
    """게시글 작성/목록 필터에서 사용할 활성 게시판 타입 목록을 반환합니다."""

    return list_board_types(db)


@router.get("/{post_id}/comments", response_model=list[PostCommentItem])
def list_post_comments_route(
    post_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> list[PostCommentItem]:
    """게시글에 달린 공개 댓글 목록을 반환합니다."""

    comments = list_comments(db, post_id=post_id)
    if comments is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return comments


@router.post("/{post_id}/comments", response_model=PostCommentItem, status_code=status.HTTP_201_CREATED)
def create_post_comment_route(
    post_id: int,
    payload: PostCommentCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PostCommentItem:
    """로그인 사용자가 게시글에 댓글을 작성합니다."""

    comment = create_comment(db, post_id=post_id, content=payload.content, author=current_user)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    db.commit()
    return comment


@router.delete("/{post_id}/comments/{comment_id}", response_model=PostCommentDeleteResponse)
def delete_post_comment_route(
    post_id: int,
    comment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PostCommentDeleteResponse:
    """댓글 존재 여부와 삭제 권한을 확인한 뒤 소프트 삭제합니다."""

    comment = get_comment_for_mutation(db, post_id=post_id, comment_id=comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    if not can_mutate_comment(current_user, comment):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    delete_comment(db, comment=comment, deleted_by=current_user)
    db.commit()
    return PostCommentDeleteResponse(message="Comment deleted")


@router.get("/{post_id}", response_model=PostDetailResponse)
def get_post_route(post_id: int, db: Annotated[Session, Depends(get_db)]) -> PostDetailResponse:
    """게시글 상세를 조회하고 조회수 증가 결과를 commit합니다."""

    post = get_post_detail(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    db.commit()
    return post


@router.post("", response_model=PostMutationResponse, status_code=status.HTTP_201_CREATED)
def create_post_route(
    payload: PostCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PostMutationResponse:
    """로그인 사용자가 작성한 새 게시글을 생성합니다."""

    try:
        post = create_post(
            db,
            title=payload.title,
            content=payload.content,
            author=current_user,
            board_type_code=payload.boardTypeCode,
        )
    except InvalidBoardTypeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    return post


@router.put("/{post_id}", response_model=PostMutationResponse)
def update_post_route(
    post_id: int,
    payload: PostUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PostMutationResponse:
    """게시글 존재 여부와 수정 권한을 확인한 뒤 제목/본문을 수정합니다."""

    post = get_post_for_mutation(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if not can_mutate_post(current_user, post):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    try:
        updated_post = update_post(
            db,
            post=post,
            title=payload.title,
            content=payload.content,
            board_type_code=payload.boardTypeCode,
            updated_by=current_user,
        )
    except InvalidBoardTypeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    return updated_post


@router.delete("/{post_id}", response_model=PostDeleteResponse)
def delete_post_route(
    post_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PostDeleteResponse:
    """게시글 존재 여부와 삭제 권한을 확인한 뒤 소프트 삭제합니다."""

    post = get_post_for_mutation(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if not can_mutate_post(current_user, post):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    delete_post(db, post=post, deleted_by=current_user)
    db.commit()
    return PostDeleteResponse(message="Post deleted")

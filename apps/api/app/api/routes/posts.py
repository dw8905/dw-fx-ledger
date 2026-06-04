from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.schemas.posts import (
    PostCreateRequest,
    PostDeleteResponse,
    PostDetailResponse,
    PostListResponse,
    PostMutationResponse,
    PostUpdateRequest,
)
from app.services.posts import (
    can_mutate_post,
    create_post,
    delete_post,
    get_post_detail,
    get_post_for_mutation,
    list_posts,
    update_post,
)

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=PostListResponse)
def list_post_route(
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PostListResponse:
    return list_posts(db, page=page, size=size)


@router.get("/{post_id}", response_model=PostDetailResponse)
def get_post_route(post_id: int, db: Annotated[Session, Depends(get_db)]) -> PostDetailResponse:
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
    post = create_post(db, title=payload.title, content=payload.content, author=current_user)
    db.commit()
    return post


@router.put("/{post_id}", response_model=PostMutationResponse)
def update_post_route(
    post_id: int,
    payload: PostUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PostMutationResponse:
    post = get_post_for_mutation(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if not can_mutate_post(current_user, post):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    updated_post = update_post(
        db,
        post=post,
        title=payload.title,
        content=payload.content,
        updated_by=current_user,
    )
    db.commit()
    return updated_post


@router.delete("/{post_id}", response_model=PostDeleteResponse)
def delete_post_route(
    post_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PostDeleteResponse:
    post = get_post_for_mutation(db, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if not can_mutate_post(current_user, post):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    delete_post(db, post=post, deleted_by=current_user)
    db.commit()
    return PostDeleteResponse(message="Post deleted")

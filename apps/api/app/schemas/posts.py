from datetime import datetime

from pydantic import BaseModel, Field


class PostCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class PostUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class PostListItem(BaseModel):
    postId: int
    title: str
    authorName: str
    viewCount: int
    createdAt: datetime


class PostListResponse(BaseModel):
    items: list[PostListItem]
    page: int
    size: int
    totalCount: int


class PostDetailResponse(BaseModel):
    postId: int
    title: str
    content: str
    authorId: int
    authorName: str
    viewCount: int
    postStatus: str
    createdAt: datetime
    updatedAt: datetime


class PostMutationResponse(BaseModel):
    postId: int
    title: str
    content: str
    authorId: int
    authorName: str
    viewCount: int
    postStatus: str
    createdAt: datetime
    updatedAt: datetime


class PostDeleteResponse(BaseModel):
    message: str

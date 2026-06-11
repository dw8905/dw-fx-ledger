from datetime import datetime

from pydantic import BaseModel, Field


class PostCreateRequest(BaseModel):
    """게시글 생성 화면에서 입력한 제목과 본문을 검증합니다."""

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    boardTypeCode: str = Field(default="general", min_length=1, max_length=50)


class PostUpdateRequest(BaseModel):
    """게시글 수정 화면에서 입력한 제목과 본문을 검증합니다."""

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    boardTypeCode: str | None = Field(default=None, min_length=1, max_length=50)


class BoardTypeItem(BaseModel):
    """게시판 타입 공통코드 한 건을 프론트 선택 UI에 맞춰 반환합니다."""

    code: str
    name: str


class PostListItem(BaseModel):
    """게시글 목록 테이블의 한 행에 필요한 요약 정보입니다."""

    postId: int
    boardTypeCode: str
    boardTypeName: str
    title: str
    authorName: str
    viewCount: int
    createdAt: datetime


class PostListResponse(BaseModel):
    """게시글 목록과 페이지네이션 메타 정보를 함께 내려주는 응답입니다."""

    items: list[PostListItem]
    page: int
    size: int
    totalCount: int


class PostDetailResponse(BaseModel):
    """게시글 상세 화면에서 본문과 작성자/조회수 정보를 보여주는 응답입니다."""

    postId: int
    boardTypeCode: str
    boardTypeName: str
    title: str
    content: str
    authorId: int
    authorName: str
    viewCount: int
    postStatus: str
    createdAt: datetime
    updatedAt: datetime


class PostMutationResponse(BaseModel):
    """게시글 생성/수정 직후 화면 갱신에 필요한 최신 게시글 정보입니다."""

    postId: int
    boardTypeCode: str
    boardTypeName: str
    title: str
    content: str
    authorId: int
    authorName: str
    viewCount: int
    postStatus: str
    createdAt: datetime
    updatedAt: datetime


class PostDeleteResponse(BaseModel):
    """게시글 삭제 요청이 끝났음을 알려주는 단순 메시지 응답입니다."""

    message: str

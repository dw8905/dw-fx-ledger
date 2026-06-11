import { apiFetch } from "./api";

export type PostListItem = {
  /** 게시글 목록 테이블의 한 행에 표시할 게시글 요약입니다. */
  postId: number;
  boardTypeCode: string;
  boardTypeName: string;
  title: string;
  authorName: string;
  viewCount: number;
  createdAt: string;
};

export type PostListResponse = {
  /** 게시글 목록과 페이지네이션 정보를 담은 응답입니다. */
  items: PostListItem[];
  page: number;
  size: number;
  totalCount: number;
};

export type PostDetail = {
  /** 게시글 상세/수정 화면에서 사용하는 전체 게시글 정보입니다. */
  postId: number;
  boardTypeCode: string;
  boardTypeName: string;
  title: string;
  content: string;
  authorId: number;
  authorName: string;
  viewCount: number;
  postStatus: string;
  createdAt: string;
  updatedAt: string;
};

export type BoardType = {
  /** 공통코드 기반 게시판 타입 선택 옵션입니다. */
  code: string;
  name: string;
};

export type PostInput = {
  /** 게시글 저장 API가 받는 제목, 본문, 게시판 타입 입력값입니다. */
  title: string;
  content: string;
  boardTypeCode?: string;
};

export async function listBoardTypes() {
  /** 활성화된 게시판 타입 공통코드 목록을 조회합니다. */

  return apiFetch<BoardType[]>("/posts/board-types", {
    skipRefresh: true
  });
}

export async function listPosts(page = 1, size = 10, keyword = "", boardTypeCode = "general") {
  /** 게시글 목록을 게시판 타입, 페이지, 검색어 기준으로 조회합니다. */

  const params = new URLSearchParams({
    page: String(page),
    size: String(size),
    board_type_code: boardTypeCode
  });
  if (keyword) {
    params.set("keyword", keyword);
  }
  return apiFetch<PostListResponse>(`/posts?${params}`, {
    skipRefresh: true
  });
}

export async function getPost(postId: number) {
  /** 게시글 상세를 조회하며 서버에서 조회수 1 증가가 일어납니다. */

  return apiFetch<PostDetail>(`/posts/${postId}`, {
    skipRefresh: true
  });
}

export async function createPost(input: PostInput) {
  /** 로그인 사용자의 새 게시글을 생성합니다. */

  return apiFetch<PostDetail>("/posts", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function updatePost(postId: number, input: PostInput) {
  /** 게시글 작성자 또는 admin 권한으로 제목/본문을 수정합니다. */

  return apiFetch<PostDetail>(`/posts/${postId}`, {
    method: "PUT",
    body: JSON.stringify(input)
  });
}

export async function deletePost(postId: number) {
  /** 게시글을 서버에서 소프트 삭제 처리합니다. */

  return apiFetch<{ message: string }>(`/posts/${postId}`, {
    method: "DELETE"
  });
}

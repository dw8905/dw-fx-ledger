import { apiFetch } from "./api";

export type PostListItem = {
  /** 게시글 목록 테이블의 한 행에 표시할 게시글 요약입니다. */
  postId: number;
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
  title: string;
  content: string;
  authorId: number;
  authorName: string;
  viewCount: number;
  postStatus: string;
  createdAt: string;
  updatedAt: string;
};

export async function listPosts(page = 1, size = 10, keyword = "") {
  /** 게시글 목록을 페이지와 검색어 기준으로 조회합니다. */

  const params = new URLSearchParams({
    page: String(page),
    size: String(size)
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

export async function createPost(input: { title: string; content: string }) {
  /** 로그인 사용자의 새 게시글을 생성합니다. */

  return apiFetch<PostDetail>("/posts", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function updatePost(postId: number, input: { title: string; content: string }) {
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

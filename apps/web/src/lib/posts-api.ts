import { apiFetch } from "./api";

export type PostListItem = {
  postId: number;
  title: string;
  authorName: string;
  viewCount: number;
  createdAt: string;
};

export type PostListResponse = {
  items: PostListItem[];
  page: number;
  size: number;
  totalCount: number;
};

export type PostDetail = {
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
  return apiFetch<PostDetail>(`/posts/${postId}`, {
    skipRefresh: true
  });
}

export async function createPost(input: { title: string; content: string }) {
  return apiFetch<PostDetail>("/posts", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function updatePost(postId: number, input: { title: string; content: string }) {
  return apiFetch<PostDetail>(`/posts/${postId}`, {
    method: "PUT",
    body: JSON.stringify(input)
  });
}

export async function deletePost(postId: number) {
  return apiFetch<{ message: string }>(`/posts/${postId}`, {
    method: "DELETE"
  });
}

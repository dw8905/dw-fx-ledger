"use client";

import { FormEvent, useEffect, useState } from "react";
import { AdminGuard } from "../../../src/components/admin-guard";
import { AdminShell } from "../../../src/components/admin-shell";
import { Pagination } from "../../../src/components/pagination";
import { listPosts, type AdminPost, type Paginated } from "../../../src/lib/admin-api";
import { formatDateTime, formatNumber } from "../../../src/lib/format";

type PostFilters = {
  keyword: string;
  postStatus: string;
  includeDeleted: boolean;
};

const initialFilters: PostFilters = {
  keyword: "",
  postStatus: "",
  includeDeleted: true
};

function PostsContent() {
  const [draftFilters, setDraftFilters] = useState<PostFilters>(initialFilters);
  const [filters, setFilters] = useState<PostFilters>(initialFilters);
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [data, setData] = useState<Paginated<AdminPost> | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    listPosts({
      page,
      size,
      includeDeleted: filters.includeDeleted,
      keyword: filters.keyword,
      postStatus: filters.postStatus
    })
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "게시글 목록을 불러오지 못했습니다.")
      );
  }, [filters, page, size]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setFilters(draftFilters);
  }

  function resetFilters() {
    setDraftFilters(initialFilters);
    setFilters(initialFilters);
    setPage(1);
  }

  return (
    <AdminShell>
      <main className="content-page">
        <section className="content-header">
          <div>
            <p className="eyebrow">Posts</p>
            <h1>게시글 관리 목록</h1>
          </div>
        </section>
        <form className="filter-bar" onSubmit={handleSubmit}>
          <label>
            검색
            <input
              placeholder="제목, 내용, 작성자"
              value={draftFilters.keyword}
              onChange={(event) =>
                setDraftFilters((current) => ({ ...current, keyword: event.target.value }))
              }
            />
          </label>
          <label>
            상태
            <select
              value={draftFilters.postStatus}
              onChange={(event) =>
                setDraftFilters((current) => ({ ...current, postStatus: event.target.value }))
              }
            >
              <option value="">전체</option>
              <option value="published">published</option>
              <option value="deleted">deleted</option>
            </select>
          </label>
          <label className="check-control">
            <input
              checked={draftFilters.includeDeleted}
              type="checkbox"
              onChange={(event) =>
                setDraftFilters((current) => ({ ...current, includeDeleted: event.target.checked }))
              }
            />
            삭제글 포함
          </label>
          <button className="primary-button" type="submit">
            검색
          </button>
          <button className="secondary-button" type="button" onClick={resetFilters}>
            초기화
          </button>
        </form>
        {error ? <p className="form-error">{error}</p> : null}
        {!data ? (
          <p>게시글을 불러오는 중입니다.</p>
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>제목</th>
                    <th>작성자</th>
                    <th>조회수</th>
                    <th>상태</th>
                    <th>삭제</th>
                    <th>작성일</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((post) => (
                    <tr key={post.post_id}>
                      <td>{post.post_id}</td>
                      <td>{post.title}</td>
                      <td>
                        #{post.author_id} {post.author_name}
                      </td>
                      <td>{formatNumber(post.view_count)}</td>
                      <td>{post.post_status}</td>
                      <td>{post.is_deleted ? "Y" : "N"}</td>
                      <td>{formatDateTime(post.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              page={data.page}
              size={data.size}
              totalCount={data.total_count}
              totalPages={data.total_pages}
              onPageChange={setPage}
              onSizeChange={(nextSize) => {
                setSize(nextSize);
                setPage(1);
              }}
            />
          </>
        )}
      </main>
    </AdminShell>
  );
}

export default function PostsPage() {
  return (
    <AdminGuard>
      <PostsContent />
    </AdminGuard>
  );
}

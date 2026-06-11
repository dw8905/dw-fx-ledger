"use client";

import { FormEvent, useEffect, useState } from "react";
import { AdminGuard } from "../../../src/components/admin-guard";
import { AdminShell } from "../../../src/components/admin-shell";
import { Pagination } from "../../../src/components/pagination";
import {
  listBoardTypes,
  listPosts,
  type AdminPost,
  type BoardType,
  type Paginated
} from "../../../src/lib/admin-api";
import { formatDateTime, formatNumber } from "../../../src/lib/format";

type PostFilters = {
  /** 관리자 게시글 목록의 검색어, 게시 상태, 삭제글 포함 여부 필터입니다. */
  keyword: string;
  boardTypeCode: string;
  postStatus: string;
  includeDeleted: boolean;
};

const initialFilters: PostFilters = {
  keyword: "",
  boardTypeCode: "",
  postStatus: "",
  includeDeleted: true
};

function PostsContent() {
  /** 게시글 관리 목록의 검색/필터/페이지네이션 상태와 조회 결과를 관리합니다. */

  const [draftFilters, setDraftFilters] = useState<PostFilters>(initialFilters);
  const [filters, setFilters] = useState<PostFilters>(initialFilters);
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [data, setData] = useState<Paginated<AdminPost> | null>(null);
  const [boardTypes, setBoardTypes] = useState<BoardType[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    listBoardTypes().then(setBoardTypes).catch(() => setBoardTypes([]));
  }, []);

  useEffect(() => {
    setError("");
    listPosts({
      page,
      size,
      boardTypeCode: filters.boardTypeCode,
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
    /** 검색 폼 입력값을 실제 게시글 조회 필터로 확정합니다. */

    event.preventDefault();
    setPage(1);
    setFilters(draftFilters);
  }

  function resetFilters() {
    /** 게시글 필터를 초기값으로 되돌리고 첫 페이지를 다시 조회합니다. */

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
            게시판
            <select
              value={draftFilters.boardTypeCode}
              onChange={(event) =>
                setDraftFilters((current) => ({ ...current, boardTypeCode: event.target.value }))
              }
            >
              <option value="">전체</option>
              {boardTypes.map((boardType) => (
                <option key={boardType.code} value={boardType.code}>
                  {boardType.name}
                </option>
              ))}
            </select>
          </label>
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
                    <th>게시판</th>
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
                      <td>{post.board_type_name}</td>
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
  /** 관리자 게시글 목록 화면 전체를 admin 권한 가드로 보호합니다. */

  return (
    <AdminGuard>
      <PostsContent />
    </AdminGuard>
  );
}

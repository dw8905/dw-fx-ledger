"use client";

import { useEffect, useState } from "react";
import { AdminGuard } from "../../../src/components/admin-guard";
import { AdminShell } from "../../../src/components/admin-shell";
import { listPosts, type AdminPost, type Paginated } from "../../../src/lib/admin-api";
import { formatDateTime, formatNumber } from "../../../src/lib/format";

function PostsContent() {
  const [includeDeleted, setIncludeDeleted] = useState(true);
  const [data, setData] = useState<Paginated<AdminPost> | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    listPosts({ includeDeleted })
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "게시글 목록을 불러오지 못했습니다.")
      );
  }, [includeDeleted]);

  return (
    <AdminShell>
      <main className="content-page">
        <section className="content-header">
          <div>
            <p className="eyebrow">Posts</p>
            <h1>게시글 관리 목록</h1>
          </div>
          <label className="check-control">
            <input
              checked={includeDeleted}
              type="checkbox"
              onChange={(event) => setIncludeDeleted(event.target.checked)}
            />
            삭제글 포함
          </label>
        </section>
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
            <p className="pagination-summary">
              page {data.page} / size {data.size} / total {formatNumber(data.total_count)}
            </p>
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

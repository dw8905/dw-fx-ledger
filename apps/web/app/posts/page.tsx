"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Pagination } from "../../src/components/pagination";
import { formatDateTime } from "../../src/lib/format";
import { listPosts, type PostListResponse } from "../../src/lib/posts-api";

export default function PostsPage() {
  const [data, setData] = useState<PostListResponse | null>(null);
  const [keywordInput, setKeywordInput] = useState("");
  const [keyword, setKeyword] = useState("");
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    listPosts(page, size, keyword)
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "목록을 불러오지 못했습니다.")
      );
  }, [keyword, page, size]);

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setKeyword(keywordInput.trim());
  }

  function resetSearch() {
    setKeywordInput("");
    setKeyword("");
    setPage(1);
  }

  return (
    <main className="content-page">
      <section className="content-header">
        <div>
          <p className="eyebrow">Board</p>
          <h1>게시글 목록</h1>
        </div>
        <Link className="primary-link" href="/posts/new">
          글쓰기
        </Link>
      </section>

      <form className="filter-bar" onSubmit={handleSearch}>
        <label>
          검색
          <input
            placeholder="제목, 내용, 작성자"
            value={keywordInput}
            onChange={(event) => setKeywordInput(event.target.value)}
          />
        </label>
        <button className="primary-button" type="submit">
          검색
        </button>
        <button className="secondary-button" type="button" onClick={resetSearch}>
          초기화
        </button>
      </form>

      {error ? <p className="form-error">{error}</p> : null}
      {!data ? (
        <p>게시글을 불러오는 중입니다.</p>
      ) : (
        <>
          <div className="table-wrap">
            <table className="post-table">
              <thead>
                <tr>
                  <th>번호</th>
                  <th>제목</th>
                  <th>작성자</th>
                  <th>조회수</th>
                  <th>작성일</th>
                </tr>
              </thead>
              <tbody>
                {data.items.length === 0 ? (
                  <tr>
                    <td colSpan={5}>게시글이 없습니다.</td>
                  </tr>
                ) : (
                  data.items.map((post) => (
                    <tr key={post.postId}>
                      <td>{post.postId}</td>
                      <td>
                        <Link href={`/posts/${post.postId}`}>{post.title}</Link>
                      </td>
                      <td>{post.authorName}</td>
                      <td>{post.viewCount}</td>
                      <td>{formatDateTime(post.createdAt)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <Pagination
            page={data.page}
            size={data.size}
            totalCount={data.totalCount}
            onPageChange={setPage}
            onSizeChange={(nextSize) => {
              setSize(nextSize);
              setPage(1);
            }}
          />
        </>
      )}
    </main>
  );
}

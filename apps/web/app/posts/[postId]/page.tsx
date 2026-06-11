"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "../../../src/context/auth-context";
import { formatDateTime } from "../../../src/lib/format";
import { deletePost, getPost, type PostDetail } from "../../../src/lib/posts-api";

export default function PostDetailPage() {
  /** 게시글 상세를 조회하고 작성자/admin에게 수정·삭제 버튼을 보여줍니다. */

  const params = useParams<{ postId: string }>();
  const router = useRouter();
  const { user } = useAuth();
  const postId = Number(params.postId);
  const [post, setPost] = useState<PostDetail | null>(null);
  const [error, setError] = useState("");
  const loadedPostIdRef = useRef<number | null>(null);

  const canMutate = useMemo(() => {
    if (!user || !post) {
      return false;
    }

    return user.userId === post.authorId || user.roles.includes("admin");
  }, [post, user]);

  useEffect(() => {
    if (Number.isFinite(postId) === false || loadedPostIdRef.current === postId) {
      return;
    }

    loadedPostIdRef.current = postId;
    setError("");
    getPost(postId)
      .then(setPost)
      .catch((caughtError) => {
        loadedPostIdRef.current = null;
        setError(caughtError instanceof Error ? caughtError.message : "게시글을 불러오지 못했습니다.");
      });
  }, [postId]);

  async function handleDelete() {
    /** 사용자 확인 후 게시글 삭제 API를 호출하고 목록으로 이동합니다. */

    if (!post || !window.confirm("게시글을 삭제할까요?")) {
      return;
    }

    await deletePost(post.postId);
    router.push("/posts");
  }

  return (
    <main className="content-page narrow">
      <Link className="back-link" href="/posts">
        목록으로
      </Link>
      {error ? <p className="form-error">{error}</p> : null}
      {!post ? (
        <p>게시글을 불러오는 중입니다.</p>
      ) : (
        <article className="post-detail">
          <div className="content-header">
            <div>
              <p className="eyebrow">Board</p>
              <h1>{post.title}</h1>
            </div>
            {canMutate ? (
              <div className="button-row">
                <Link className="secondary-link" href={`/posts/${post.postId}/edit`}>
                  수정
                </Link>
                <button className="danger-button" type="button" onClick={() => void handleDelete()}>
                  삭제
                </button>
              </div>
            ) : null}
          </div>
          <dl className="post-meta">
            <div>
              <dt>게시판</dt>
              <dd>{post.boardTypeName}</dd>
            </div>
            <div>
              <dt>작성자</dt>
              <dd>{post.authorName}</dd>
            </div>
            <div>
              <dt>작성일</dt>
              <dd>{formatDateTime(post.createdAt)}</dd>
            </div>
            <div>
              <dt>수정일</dt>
              <dd>{formatDateTime(post.updatedAt)}</dd>
            </div>
            <div>
              <dt>조회수</dt>
              <dd>{post.viewCount}</dd>
            </div>
          </dl>
          <div className="post-content">{post.content}</div>
        </article>
      )}
    </main>
  );
}

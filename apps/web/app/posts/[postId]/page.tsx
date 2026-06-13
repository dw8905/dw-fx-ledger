"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "../../../src/context/auth-context";
import { formatDateTime } from "../../../src/lib/format";
import {
  createPostComment,
  deletePost,
  deletePostComment,
  getPost,
  listPostComments,
  type PostComment,
  type PostDetail
} from "../../../src/lib/posts-api";

export default function PostDetailPage() {
  /** 게시글 상세를 조회하고 작성자/admin에게 수정·삭제 버튼을 보여줍니다. */

  const params = useParams<{ postId: string }>();
  const router = useRouter();
  const { status, user } = useAuth();
  const postId = Number(params.postId);
  const [post, setPost] = useState<PostDetail | null>(null);
  const [comments, setComments] = useState<PostComment[]>([]);
  const [commentInput, setCommentInput] = useState("");
  const [isSubmittingComment, setIsSubmittingComment] = useState(false);
  const [error, setError] = useState("");
  const [commentError, setCommentError] = useState("");
  const loadedPostIdRef = useRef<number | null>(null);

  const canMutate = useMemo(() => {
    if (!user || !post) {
      return false;
    }

    return user.userId === post.authorId || user.roles.includes("admin");
  }, [post, user]);

  const loadComments = useCallback(async () => {
    /** 댓글 목록만 다시 불러와 상세 조회수 증가와 분리합니다. */

    if (Number.isFinite(postId) === false) {
      return;
    }

    setCommentError("");
    try {
      setComments(await listPostComments(postId));
    } catch (caughtError) {
      setCommentError(caughtError instanceof Error ? caughtError.message : "댓글을 불러오지 못했습니다.");
    }
  }, [postId]);

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

  useEffect(() => {
    void loadComments();
  }, [loadComments]);

  async function handleDelete() {
    /** 사용자 확인 후 게시글 삭제 API를 호출하고 목록으로 이동합니다. */

    if (!post || !window.confirm("게시글을 삭제할까요?")) {
      return;
    }

    await deletePost(post.postId);
    router.push("/posts");
  }

  async function handleCommentSubmit(event: FormEvent<HTMLFormElement>) {
    /** 댓글 내용을 검증한 뒤 생성하고 목록을 갱신합니다. */

    event.preventDefault();
    const content = commentInput.trim();
    if (!content) {
      setCommentError("댓글 내용을 입력해주세요.");
      return;
    }

    setIsSubmittingComment(true);
    setCommentError("");
    try {
      await createPostComment(postId, content);
      setCommentInput("");
      await loadComments();
    } catch (caughtError) {
      setCommentError(caughtError instanceof Error ? caughtError.message : "댓글 작성에 실패했습니다.");
    } finally {
      setIsSubmittingComment(false);
    }
  }

  async function handleCommentDelete(commentId: number) {
    /** 댓글 삭제 확인 후 목록을 갱신합니다. */

    if (!window.confirm("댓글을 삭제할까요?")) {
      return;
    }

    setCommentError("");
    try {
      await deletePostComment(postId, commentId);
      await loadComments();
    } catch (caughtError) {
      setCommentError(caughtError instanceof Error ? caughtError.message : "댓글 삭제에 실패했습니다.");
    }
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
          <div className="content-header content-header-actions">
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
          <section className="comments-section">
            <div className="comments-header">
              <h2>댓글</h2>
              <span>{comments.length}</span>
            </div>

            {commentError ? <p className="form-error">{commentError}</p> : null}
            <div className="comment-list">
              {comments.length === 0 ? (
                <p className="empty-state">아직 댓글이 없습니다.</p>
              ) : (
                comments.map((comment) => {
                  const canDeleteComment = Boolean(
                    user && (user.userId === comment.authorId || user.roles.includes("admin"))
                  );

                  return (
                    <article className="comment-item" key={comment.commentId}>
                      <div className="comment-meta">
                        <strong>{comment.authorName}</strong>
                        <span>{formatDateTime(comment.createdAt)}</span>
                      </div>
                      <p>{comment.content}</p>
                      {canDeleteComment ? (
                        <button
                          className="comment-delete-button"
                          type="button"
                          onClick={() => void handleCommentDelete(comment.commentId)}
                        >
                          삭제
                        </button>
                      ) : null}
                    </article>
                  );
                })
              )}
            </div>

            {status === "authenticated" ? (
              <form className="comment-form" onSubmit={handleCommentSubmit}>
                <label>
                  댓글 작성
                  <textarea
                    maxLength={2000}
                    placeholder="댓글을 입력하세요."
                    value={commentInput}
                    onChange={(event) => setCommentInput(event.target.value)}
                  />
                </label>
                <button className="primary-button" disabled={isSubmittingComment} type="submit">
                  {isSubmittingComment ? "저장 중" : "댓글 등록"}
                </button>
              </form>
            ) : (
              <p className="comment-login">
                댓글을 작성하려면 <Link href="/login">로그인</Link>이 필요합니다.
              </p>
            )}
          </section>
        </article>
      )}
    </main>
  );
}

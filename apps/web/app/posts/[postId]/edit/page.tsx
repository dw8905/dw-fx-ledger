"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AuthGuard } from "../../../../src/components/auth-guard";
import { PostForm } from "../../../../src/components/post-form";
import { useAuth } from "../../../../src/context/auth-context";
import { getPost, updatePost, type PostDetail } from "../../../../src/lib/posts-api";

function EditPostContent() {
  /** 수정 대상 게시글을 불러온 뒤 작성자/admin 권한을 확인합니다. */

  const params = useParams<{ postId: string }>();
  const router = useRouter();
  const { user } = useAuth();
  const postId = Number(params.postId);
  const [post, setPost] = useState<PostDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getPost(postId)
      .then((loadedPost) => {
        if (
          user &&
          loadedPost.authorId !== user.userId &&
          !user.roles.includes("admin")
        ) {
          setError("수정 권한이 없습니다.");
          return;
        }

        setPost(loadedPost);
      })
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "게시글을 불러오지 못했습니다.")
      );
  }, [postId, user]);

  if (error) {
    return (
      <main className="content-page narrow">
        <p className="form-error">{error}</p>
      </main>
    );
  }

  if (!post) {
    return <main className="content-page narrow">게시글을 불러오는 중입니다.</main>;
  }

  return (
    <main className="content-page narrow">
      <p className="eyebrow">Board</p>
      <h1>게시글 수정</h1>
      <PostForm
        initialTitle={post.title}
        initialContent={post.content}
        submitLabel="수정"
        onSubmit={async (input) => {
          const updatedPost = await updatePost(post.postId, input);
          router.push(`/posts/${updatedPost.postId}`);
        }}
      />
    </main>
  );
}

export default function EditPostPage() {
  /** 게시글 수정 화면 전체를 인증 가드로 보호합니다. */

  return (
    <AuthGuard>
      <EditPostContent />
    </AuthGuard>
  );
}

"use client";

import { useRouter } from "next/navigation";
import { AuthGuard } from "../../../src/components/auth-guard";
import { PostForm } from "../../../src/components/post-form";
import { createPost } from "../../../src/lib/posts-api";

export default function NewPostPage() {
  const router = useRouter();

  return (
    <AuthGuard>
      <main className="content-page narrow">
        <p className="eyebrow">Board</p>
        <h1>게시글 작성</h1>
        <PostForm
          submitLabel="저장"
          onSubmit={async (input) => {
            await createPost(input);
            router.push("/posts");
          }}
        />
      </main>
    </AuthGuard>
  );
}

"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AuthGuard } from "../../../src/components/auth-guard";
import { PostForm } from "../../../src/components/post-form";
import { createPost, listBoardTypes, type BoardType } from "../../../src/lib/posts-api";

export default function NewPostPage() {
  /** 게시글 작성 폼을 보여주고 저장 성공 시 목록으로 이동합니다. */

  const router = useRouter();
  const [boardTypes, setBoardTypes] = useState<BoardType[]>([]);

  useEffect(() => {
    listBoardTypes().then(setBoardTypes).catch(() => setBoardTypes([]));
  }, []);

  return (
    <AuthGuard>
      <main className="content-page narrow">
        <p className="eyebrow">Board</p>
        <h1>게시글 작성</h1>
        <PostForm
          boardTypes={boardTypes}
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

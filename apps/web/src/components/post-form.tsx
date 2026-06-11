"use client";

import { FormEvent, useState } from "react";

import type { BoardType, PostInput } from "../lib/posts-api";

type PostFormProps = {
  /** 게시글 생성/수정 화면이 공통으로 쓰는 제목/본문 폼 입력값입니다. */
  initialTitle?: string;
  initialContent?: string;
  initialBoardTypeCode?: string;
  boardTypes?: BoardType[];
  submitLabel: string;
  onSubmit: (input: PostInput) => Promise<void>;
};

export function PostForm({
  initialTitle = "",
  initialContent = "",
  initialBoardTypeCode = "general",
  boardTypes = [],
  submitLabel,
  onSubmit
}: PostFormProps) {
  /** 게시글 생성과 수정을 하나의 폼으로 처리하고 저장 실패 메시지를 표시합니다. */

  const [title, setTitle] = useState(initialTitle);
  const [content, setContent] = useState(initialContent);
  const [boardTypeCode, setBoardTypeCode] = useState(initialBoardTypeCode);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    /** 기본 form submit을 막고 부모가 넘긴 저장 함수를 호출합니다. */

    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await onSubmit({ title, content, boardTypeCode });
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "저장에 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="post-form" onSubmit={handleSubmit}>
      <label>
        게시판
        <select value={boardTypeCode} onChange={(event) => setBoardTypeCode(event.target.value)}>
          {(boardTypes.length > 0 ? boardTypes : [{ code: "general", name: "일반 게시판" }]).map((boardType) => (
            <option key={boardType.code} value={boardType.code}>
              {boardType.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        제목
        <input
          maxLength={200}
          required
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
      </label>
      <label>
        내용
        <textarea required value={content} onChange={(event) => setContent(event.target.value)} />
      </label>
      {error ? <p className="form-error">{error}</p> : null}
      <button className="primary-button" disabled={isSubmitting} type="submit">
        {isSubmitting ? "저장 중" : submitLabel}
      </button>
    </form>
  );
}

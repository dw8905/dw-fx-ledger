"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "../../src/context/auth-context";

export default function RegisterPage() {
  /** 회원가입 폼을 렌더링하고 로그인된 사용자는 홈으로 돌려보냅니다. */

  const router = useRouter();
  const { register, status } = useAuth();
  const [email, setEmail] = useState("");
  const [loginId, setLoginId] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (status === "authenticated") {
      router.replace("/");
    }
  }, [router, status]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    /** 비밀번호 확인을 먼저 검증한 뒤 회원가입 API를 호출합니다. */

    event.preventDefault();
    setError("");

    if (password !== passwordConfirm) {
      setError("비밀번호 확인이 일치하지 않습니다.");
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        email,
        loginId,
        displayName,
        password
      });
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "회원가입에 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel">
        <p className="eyebrow">Register</p>
        <h1>회원가입</h1>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            이메일
            <input
              autoComplete="email"
              required
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label>
            login_id
            <input
              autoComplete="username"
              required
              value={loginId}
              onChange={(event) => setLoginId(event.target.value)}
            />
          </label>
          <label>
            display_name
            <input
              autoComplete="name"
              required
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
            />
          </label>
          <label>
            비밀번호
            <input
              autoComplete="new-password"
              minLength={8}
              required
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          <label>
            비밀번호 확인
            <input
              autoComplete="new-password"
              minLength={8}
              required
              type="password"
              value={passwordConfirm}
              onChange={(event) => setPasswordConfirm(event.target.value)}
            />
          </label>
          {error ? <p className="form-error">{error}</p> : null}
          <button className="primary-button" disabled={isSubmitting} type="submit">
            {isSubmitting ? "가입 중" : "회원가입"}
          </button>
        </form>
        <p className="auth-link">
          이미 계정이 있으면 <Link href="/login">로그인</Link>
        </p>
      </section>
    </main>
  );
}

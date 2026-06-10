"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "../../src/context/auth-context";

export default function LoginPage() {
  /** 관리자 로그인 폼을 렌더링하고 admin 사용자는 관리자 홈으로 이동시킵니다. */

  const router = useRouter();
  const { login, status, user } = useAuth();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (status === "authenticated" && user?.roles.includes("admin")) {
      router.replace("/admin/users");
    }
  }, [router, status, user]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    /** 관리자 로그인 제출 시 AuthProvider의 login 액션을 호출합니다. */

    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await login(identifier, password);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "로그인에 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel">
        <p className="eyebrow">Admin Login</p>
        <h1>관리자 로그인</h1>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            이메일 또는 login_id
            <input
              autoComplete="username"
              required
              value={identifier}
              onChange={(event) => setIdentifier(event.target.value)}
            />
          </label>
          <label>
            비밀번호
            <input
              autoComplete="current-password"
              required
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {error ? <p className="form-error">{error}</p> : null}
          <button className="primary-button" disabled={isSubmitting} type="submit">
            {isSubmitting ? "로그인 중" : "로그인"}
          </button>
        </form>
      </section>
    </main>
  );
}

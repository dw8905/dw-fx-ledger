"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { useAuth } from "../context/auth-context";

export function AdminGuard({ children }: { children: ReactNode }) {
  /** 로그인 여부와 admin role을 모두 확인해 관리자 화면 접근을 제한합니다. */

  const router = useRouter();
  const { status, user } = useAuth();

  useEffect(() => {
    if (status === "anonymous") {
      router.replace("/login");
    }
  }, [router, status]);

  if (status === "loading") {
    return <main className="content-page">인증 상태를 확인하는 중입니다.</main>;
  }

  if (status === "anonymous") {
    return <main className="content-page">로그인 페이지로 이동하는 중입니다.</main>;
  }

  if (!user?.roles.includes("admin")) {
    return (
      <main className="content-page narrow">
        <p className="eyebrow">Access denied</p>
        <h1>관리자 권한이 필요합니다.</h1>
      </main>
    );
  }

  return children;
}

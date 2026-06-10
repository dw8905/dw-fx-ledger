"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { useAuth } from "../context/auth-context";

export function AuthGuard({ children }: { children: ReactNode }) {
  /** 인증이 필요한 화면에서 anonymous 상태면 로그인 페이지로 보내는 클라이언트 가드입니다. */

  const router = useRouter();
  const { status } = useAuth();

  useEffect(() => {
    if (status === "anonymous") {
      router.replace("/login");
    }
  }, [router, status]);

  if (status === "loading") {
    return <main className="page">인증 상태를 확인하는 중입니다.</main>;
  }

  if (status === "anonymous") {
    return <main className="page">로그인 페이지로 이동하는 중입니다.</main>;
  }

  return children;
}

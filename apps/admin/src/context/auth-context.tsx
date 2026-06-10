"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode
} from "react";
import * as authApi from "../lib/auth-api";

/** 관리자 앱 인증 상태를 로딩, 로그인 완료, 비로그인으로 구분합니다. */
type AuthStatus = "loading" | "authenticated" | "anonymous";

type AuthContextValue = {
  /** 관리자 앱 전체에서 공유하는 인증 상태와 로그인/로그아웃 액션입니다. */
  status: AuthStatus;
  user: authApi.User | null;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  reloadUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  /** 앱 시작 시 현재 쿠키 인증 상태를 확인하고 관리자 화면의 인증 액션을 제공합니다. */

  const router = useRouter();
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<authApi.User | null>(null);

  const reloadUser = useCallback(async () => {
    /** 새로고침 또는 진입 시 /auth/me로 사용자와 role 정보를 다시 조회합니다. */

    try {
      const currentUser = await authApi.getMe({ redirectOnAuthFailure: false });
      setUser(currentUser);
      setStatus("authenticated");
    } catch {
      setUser(null);
      setStatus("anonymous");
    }
  }, []);

  useEffect(() => {
    void reloadUser();
  }, [reloadUser]);

  const login = useCallback(
    async (identifier: string, password: string) => {
      const result = await authApi.login(identifier, password);
      setUser(result.user);
      setStatus("authenticated");
      router.push("/admin/users");
    },
    [router]
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Local logout should still complete if the server token is already invalid.
    }

    setUser(null);
    setStatus("anonymous");
    router.push("/login");
  }, [router]);

  const value = useMemo(
    () => ({
      status,
      user,
      login,
      logout,
      reloadUser
    }),
    [status, user, login, logout, reloadUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  /** AuthProvider 내부에서만 관리자 인증 컨텍스트를 쓰도록 보장합니다. */

  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}

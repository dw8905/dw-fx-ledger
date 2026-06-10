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

/** 웹 앱 인증 상태를 로딩, 로그인 완료, 비로그인으로 구분합니다. */
type AuthStatus = "loading" | "authenticated" | "anonymous";

type AuthContextValue = {
  /** 앱 전체에서 공유하는 로그인 상태, 사용자 정보, 인증 액션 모음입니다. */
  status: AuthStatus;
  user: authApi.User | null;
  login: (identifier: string, password: string) => Promise<void>;
  register: (input: {
    email: string;
    loginId: string;
    displayName: string;
    password: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  reloadUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  /** 앱 시작 시 쿠키 인증 상태를 확인하고 로그인/회원가입/로그아웃 액션을 제공합니다. */

  const router = useRouter();
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<authApi.User | null>(null);

  const applyAuthResult = useCallback((result: authApi.AuthResult) => {
    /** 로그인/회원가입 성공 결과를 전역 인증 상태에 반영합니다. */

    setUser(result.user);
    setStatus("authenticated");
  }, []);

  const reloadUser = useCallback(async () => {
    /** 새로고침 시 서버의 /auth/me로 현재 쿠키 인증 상태를 다시 확인합니다. */

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
      applyAuthResult(result);
      router.push("/");
    },
    [applyAuthResult, router]
  );

  const register = useCallback(
    async (input: {
      email: string;
      loginId: string;
      displayName: string;
      password: string;
    }) => {
      const result = await authApi.register(input);
      applyAuthResult(result);
      router.push("/");
    },
    [applyAuthResult, router]
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
      register,
      logout,
      reloadUser
    }),
    [status, user, login, register, logout, reloadUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  /** AuthProvider 내부에서만 인증 상태에 접근하도록 보장하는 커스텀 훅입니다. */

  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}

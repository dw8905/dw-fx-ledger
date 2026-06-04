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

type AuthStatus = "loading" | "authenticated" | "anonymous";

type AuthContextValue = {
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
  const router = useRouter();
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<authApi.User | null>(null);

  const applyAuthResult = useCallback((result: authApi.AuthResult) => {
    setUser(result.user);
    setStatus("authenticated");
  }, []);

  const reloadUser = useCallback(async () => {
    try {
      const currentUser = await authApi.getMe();
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
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}

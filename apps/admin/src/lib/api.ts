const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/backend";

type ApiOptions = RequestInit & {
  /** 인증 재발급을 건너뛰어야 할 때 사용하는 옵션입니다. */
  skipRefresh?: boolean;
  redirectOnAuthFailure?: boolean;
};

function toUrl(path: string) {
  /** 상대 API 경로를 관리자 앱의 API base URL 기준으로 변환합니다. */

  if (path.startsWith("http")) {
    return path;
  }

  return `${API_BASE_URL}${path}`;
}

function redirectToLogin() {
  /** 브라우저 환경에서 인증 실패 시 관리자 로그인 화면으로 이동합니다. */

  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

async function refreshAccessToken() {
  /** HttpOnly refresh 쿠키로 access token 쿠키 재발급을 요청합니다. */

  const response = await fetch(toUrl("/auth/refresh"), {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json"
    }
  });

  return response.ok;
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  /** 관리자 앱 공통 fetch 래퍼로 쿠키 인증, 토큰 재발급, 에러 메시지를 처리합니다. */

  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(toUrl(path), {
    ...options,
    credentials: "include",
    headers
  });

  if (response.status === 401 && !options.skipRefresh) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      return apiFetch<T>(path, { ...options, skipRefresh: true });
    }

    if (options.redirectOnAuthFailure ?? true) {
      redirectToLogin();
    }
  }

  if (!response.ok) {
    let message = "Request failed";
    try {
      const errorBody = (await response.json()) as { detail?: string };
      message = errorBody.detail ?? message;
    } catch {
      // Preserve the default message for non-JSON errors.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

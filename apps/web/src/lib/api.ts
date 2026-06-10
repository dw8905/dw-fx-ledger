const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/backend";

type ApiOptions = RequestInit & {
  /** 토큰 재발급을 건너뛰어야 하는 공개/인증 API에서 사용합니다. */
  skipRefresh?: boolean;
  redirectOnAuthFailure?: boolean;
};

function toUrl(path: string) {
  /** 상대 API 경로를 Next 프록시 또는 실제 API 서버 기준 URL로 변환합니다. */

  if (path.startsWith("http")) {
    return path;
  }

  return `${API_BASE_URL}${path}`;
}

function redirectToLogin() {
  /** 브라우저에서 인증 실패가 확정되면 로그인 페이지로 이동합니다. */

  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

async function refreshAccessToken() {
  /** HttpOnly refresh 쿠키를 사용해 access token 쿠키를 재발급합니다. */

  const response = await fetch(toUrl("/auth/refresh"), {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json"
    }
  });

  if (!response.ok) {
    return false;
  }

  return true;
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  /** fetch 공통 래퍼로 쿠키 인증, 401 재발급, 에러 메시지 추출을 한 곳에서 처리합니다. */

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
      // Keep the default message when the response is not JSON.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

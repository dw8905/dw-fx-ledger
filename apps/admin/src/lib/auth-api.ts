import { apiFetch } from "./api";

export type User = {
  /** 관리자 앱 전역 인증 상태에서 쓰는 camelCase 사용자 모델입니다. */
  userId: number;
  email: string;
  loginId: string | null;
  displayName: string;
  userStatus: string;
  defaultAllocationStrategy: string;
  roles: string[];
};

type BackendUser = {
  /** FastAPI 인증 API가 내려주는 snake_case 사용자 응답 원본입니다. */
  user_id: number;
  email: string;
  login_id: string | null;
  display_name: string;
  user_status: string;
  default_allocation_strategy: string;
  roles: string[];
};

type BackendAuthResult = {
  /** 로그인 성공 시 백엔드가 내려주는 원본 인증 응답입니다. */
  user: BackendUser;
};

function mapUser(user: BackendUser): User {
  /** 백엔드 사용자 응답을 관리자 프론트에서 쓰는 camelCase 모델로 바꿉니다. */

  return {
    userId: user.user_id,
    email: user.email,
    loginId: user.login_id,
    displayName: user.display_name,
    userStatus: user.user_status,
    defaultAllocationStrategy: user.default_allocation_strategy,
    roles: user.roles
  };
}

export async function login(identifier: string, password: string) {
  /** 관리자 로그인 화면에서 이메일/login_id와 비밀번호로 로그인합니다. */

  const result = await apiFetch<BackendAuthResult>("/auth/login", {
    method: "POST",
    skipRefresh: true,
    body: JSON.stringify({ identifier, password })
  });

  return { user: mapUser(result.user) };
}

export async function getMe(options: { redirectOnAuthFailure?: boolean } = {}) {
  /** 현재 인증 쿠키로 로그인 사용자 정보를 조회합니다. */

  const result = await apiFetch<BackendUser>("/auth/me", {
    redirectOnAuthFailure: options.redirectOnAuthFailure
  });
  return mapUser(result);
}

export async function logout() {
  /** 서버에 로그아웃을 요청해 refresh token과 인증 쿠키를 정리합니다. */

  return apiFetch<{ message: string }>("/auth/logout", {
    method: "POST"
  });
}

import { apiFetch } from "./api";

export type User = {
  /** 프론트 전역 인증 상태에서 쓰는 camelCase 사용자 모델입니다. */
  userId: number;
  email: string;
  loginId: string | null;
  displayName: string;
  userStatus: string;
  defaultAllocationStrategy: string;
  roles: string[];
};

export type AuthResult = {
  /** 로그인/회원가입 성공 후 AuthProvider가 저장할 인증 결과입니다. */
  user: User;
};

type BackendUser = {
  /** FastAPI가 내려주는 snake_case 사용자 응답 원본입니다. */
  user_id: number;
  email: string;
  login_id: string | null;
  display_name: string;
  user_status: string;
  default_allocation_strategy: string;
  roles: string[];
};

type BackendAuthResult = {
  /** 백엔드 인증 API가 내려주는 원본 응답 형태입니다. */
  user: BackendUser;
};

function mapUser(user: BackendUser): User {
  /** 백엔드 snake_case 사용자 필드를 프론트 camelCase 모델로 변환합니다. */

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

function mapAuthResult(result: BackendAuthResult): AuthResult {
  /** 백엔드 인증 응답을 AuthProvider가 쓰기 쉬운 형태로 변환합니다. */

  return {
    user: mapUser(result.user)
  };
}

export async function login(identifier: string, password: string) {
  /** 이메일 또는 login_id와 비밀번호로 로그인합니다. */

  const result = await apiFetch<BackendAuthResult>("/auth/login", {
    method: "POST",
    skipRefresh: true,
    body: JSON.stringify({ identifier, password })
  });

  return mapAuthResult(result);
}

export async function register(input: {
  email: string;
  loginId: string;
  displayName: string;
  password: string;
}) {
  /** 회원가입 후 서버가 내려주는 인증 쿠키와 사용자 정보를 받습니다. */

  const result = await apiFetch<BackendAuthResult>("/auth/register", {
    method: "POST",
    skipRefresh: true,
    body: JSON.stringify({
      email: input.email,
      login_id: input.loginId,
      display_name: input.displayName,
      password: input.password
    })
  });

  return mapAuthResult(result);
}

export async function getMe(options: { redirectOnAuthFailure?: boolean } = {}) {
  /** 현재 쿠키 인증 상태로 로그인 사용자 정보를 조회합니다. */

  const result = await apiFetch<BackendUser>("/auth/me", {
    redirectOnAuthFailure: options.redirectOnAuthFailure
  });
  return mapUser(result);
}

export async function logout() {
  /** refresh token을 폐기하고 서버가 인증 쿠키를 삭제하도록 요청합니다. */

  return apiFetch<{ message: string }>("/auth/logout", {
    method: "POST"
  });
}

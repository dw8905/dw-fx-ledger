import { apiFetch } from "./api";

export type User = {
  userId: number;
  email: string;
  loginId: string | null;
  displayName: string;
  userStatus: string;
  defaultAllocationStrategy: string;
  roles: string[];
};

export type AuthResult = {
  user: User;
};

type BackendUser = {
  user_id: number;
  email: string;
  login_id: string | null;
  display_name: string;
  user_status: string;
  default_allocation_strategy: string;
  roles: string[];
};

type BackendAuthResult = {
  user: BackendUser;
};

function mapUser(user: BackendUser): User {
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
  return {
    user: mapUser(result.user)
  };
}

export async function login(identifier: string, password: string) {
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
  const result = await apiFetch<BackendUser>("/auth/me", {
    redirectOnAuthFailure: options.redirectOnAuthFailure
  });
  return mapUser(result);
}

export async function logout() {
  return apiFetch<{ message: string }>("/auth/logout", {
    method: "POST"
  });
}

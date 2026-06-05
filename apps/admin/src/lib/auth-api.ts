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

export async function login(identifier: string, password: string) {
  const result = await apiFetch<BackendAuthResult>("/auth/login", {
    method: "POST",
    skipRefresh: true,
    body: JSON.stringify({ identifier, password })
  });

  return { user: mapUser(result.user) };
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

import { apiFetch } from "./api";

export type User = { username: string };

export function login(username: string, password: string) {
  return apiFetch<User>("/api/auth/login", {
    method: "POST",
    json: { username, password },
  });
}

export function logout() {
  return apiFetch("/api/auth/logout", { method: "POST" });
}

export function fetchMe() {
  return apiFetch<User>("/api/auth/me");
}

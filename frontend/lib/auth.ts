export type UserRole =
  | "platform_admin"
  | "client_admin"
  | "client_member";

export interface AuthClient {
  id: number;
  name: string;
}

export interface AuthUser {
  id: number;
  email: string;
  role: UserRole;
  client_profile_id: number | null;
  is_active: boolean;
  client: AuthClient | null;
}

const TOKEN_KEY = "finguard_access_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.setItem(TOKEN_KEY, token);
}

export function removeAccessToken(): void {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.removeItem(TOKEN_KEY);
}

export function isPlatformAdmin(user: AuthUser): boolean {
  return user.role === "platform_admin";
}

export function isClientUser(user: AuthUser): boolean {
  return (
    user.role === "client_admin" ||
    user.role === "client_member"
  );
}
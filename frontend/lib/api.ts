import {
  getAccessToken,
  removeAccessToken,
} from "@/lib/auth";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(
    message: string,
    status: number,
    data: unknown,
  ) {
    super(message);

    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getAccessToken();

  console.log("[FinGuard apiFetch]", {
    path,
    tokenExists: Boolean(token),
    tokenLength: token?.length ?? 0,
  });

  const headers =
    new Headers(options.headers);

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`,
    );
  }

  console.log("[FinGuard headers]", {
    path,
    hasAuthorization:
      headers.has("Authorization"),
  });

  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers,
    },
  );

  let data: unknown = null;

  const contentType =
    response.headers.get("content-type") ?? "";

  if (
    contentType.includes("application/json")
  ) {
    data = await response.json();
  }

  if (!response.ok) {
    if (response.status === 401) {
      removeAccessToken();
    }

    let message = "Request failed.";

    if (
      data &&
      typeof data === "object" &&
      "detail" in data &&
      typeof (
        data as {
          detail?: unknown;
        }
      ).detail === "string"
    ) {
      message = (
        data as {
          detail: string;
        }
      ).detail;
    }

    throw new ApiError(
      message,
      response.status,
      data,
    );
  }

  return data as T;
}
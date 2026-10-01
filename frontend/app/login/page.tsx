"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import { useRouter } from "next/navigation";

import {
  AuthUser,
  getAccessToken,
  setAccessToken,
} from "@/lib/auth";

import {
  API_BASE_URL,
} from "@/lib/api";


interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;

  user: AuthUser;
}


export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");


  useEffect(() => {
    const token = getAccessToken();

    if (token) {
      router.replace("/dashboard");
    }
  }, [router]);


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/auth/login`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            email,
            password,
          }),
        },
      );

      const data =
        (await response.json()) as
          | LoginResponse
          | {
              detail?: string;
            };

      if (!response.ok) {
        throw new Error(
          "detail" in data &&
          typeof data.detail === "string"
            ? data.detail
            : "Login failed.",
        );
      }

      if (
        !("access_token" in data) ||
        !("user" in data)
      ) {
        throw new Error(
          "Invalid login response.",
        );
      }

      setAccessToken(
        data.access_token,
      );

      if (
        data.user.role ===
        "platform_admin"
      ) {
        router.replace(
          "/admin/dashboard",
        );

        return;
      }

      router.replace("/dashboard");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to login.",
      );
    } finally {
      setLoading(false);
    }
  }


  return (
    <main className="min-h-screen bg-slate-950 text-white flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="text-3xl font-bold tracking-tight">
            FinGuard
          </div>

          <p className="mt-2 text-sm text-slate-400">
            Financial Risk Intelligence
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-7 shadow-2xl">
          <div className="mb-6">
            <h1 className="text-2xl font-semibold">
              Sign in
            </h1>

            <p className="mt-1 text-sm text-slate-400">
              Access your secure
              FinGuard workspace.
            </p>
          </div>

          <form
            onSubmit={handleSubmit}
            className="space-y-5"
          >
            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-sm font-medium text-slate-300"
              >
                Email
              </label>

              <input
                id="email"
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(
                    event.target.value,
                  )
                }
                required
                autoComplete="email"
                placeholder="you@company.com"
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-2 block text-sm font-medium text-slate-300"
              >
                Password
              </label>

              <input
                id="password"
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(
                    event.target.value,
                  )
                }
                required
                autoComplete="current-password"
                placeholder="••••••••"
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
              />
            </div>

            {error && (
              <div className="rounded-xl border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-300">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-blue-600 px-4 py-3 font-medium transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading
                ? "Signing in..."
                : "Sign in"}
            </button>
          </form>

          <div className="mt-6 border-t border-slate-800 pt-5 text-center text-xs text-slate-500">
            Secure access to your
            financial intelligence
            workspace.
          </div>
        </div>
      </div>
    </main>
  );
}
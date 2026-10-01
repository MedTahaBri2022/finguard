"use client";

import {
  ReactNode,
  useEffect,
  useState,
} from "react";

import {
  usePathname,
  useRouter,
} from "next/navigation";

import {
  AuthUser,
  getAccessToken,
  isClientUser,
  isPlatformAdmin,
  removeAccessToken,
} from "@/lib/auth";

import {
  API_BASE_URL,
} from "@/lib/api";


interface AuthGuardProps {
  children: ReactNode;
  mode?: "client" | "admin";
}


export default function AuthGuard({
  children,
  mode = "client",
}: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();

  const [loading, setLoading] =
    useState(true);

  const [authorized, setAuthorized] =
    useState(false);


  useEffect(() => {
    async function checkAuth() {
      const token = getAccessToken();

      if (!token) {
        router.replace("/login");
        return;
      }

      try {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/auth/me`,
          {
            headers: {
              Authorization:
                `Bearer ${token}`,
            },
          },
        );

        if (!response.ok) {
          removeAccessToken();

          router.replace("/login");
          return;
        }

        const user =
          (await response.json()) as AuthUser;

        if (mode === "admin") {
          if (!isPlatformAdmin(user)) {
            if (isClientUser(user)) {
              router.replace(
                "/dashboard",
              );
            } else {
              router.replace(
                "/login",
              );
            }

            return;
          }
        }

        if (mode === "client") {
          if (!isClientUser(user)) {
            if (isPlatformAdmin(user)) {
              router.replace(
                "/admin/dashboard",
              );
            } else {
              router.replace(
                "/login",
              );
            }

            return;
          }
        }

        setAuthorized(true);
      } catch {
        removeAccessToken();
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    }

    checkAuth();
  }, [
    mode,
    pathname,
    router,
  ]);


  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 flex items-center justify-center text-white">
        <p className="text-slate-400">
          Checking authentication...
        </p>
      </main>
    );
  }


  if (!authorized) {
    return null;
  }


  return <>{children}</>;
}
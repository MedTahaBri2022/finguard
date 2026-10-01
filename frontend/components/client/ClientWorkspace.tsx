"use client";

import {
  ReactNode,
  useEffect,
  useState,
} from "react";

import { useRouter } from "next/navigation";

import ClientSidebar
  from "@/components/client/ClientSidebar";

import {
  AuthUser,
  removeAccessToken,
} from "@/lib/auth";

import {
  apiFetch,
} from "@/lib/api";


interface ClientWorkspaceProps {
  children: ReactNode;
}


export default function ClientWorkspace({
  children,
}: ClientWorkspaceProps) {
  const router = useRouter();

  const [user, setUser] =
    useState<AuthUser | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [sidebarOpen, setSidebarOpen] =
    useState(false);


  useEffect(() => {
    let active = true;

    async function loadCurrentUser() {
      try {
        const currentUser =
          await apiFetch<AuthUser>(
            "/api/v1/auth/me",
          );

        if (!active) {
          return;
        }

        setUser(currentUser);
      } catch {
        if (!active) {
          return;
        }

        removeAccessToken();
        router.replace("/login");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadCurrentUser();

    return () => {
      active = false;
    };
  }, [router]);


  function handleLogout() {
    removeAccessToken();

    router.replace("/login");
    router.refresh();
  }


  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
        <div className="text-center">
          <p className="text-lg font-medium">
            FinGuard
          </p>

          <p className="mt-2 text-sm text-slate-400">
            Loading workspace...
          </p>
        </div>
      </main>
    );
  }


  if (!user) {
    return null;
  }


  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <ClientSidebar
        user={user}
        isOpen={sidebarOpen}
        onClose={() =>
          setSidebarOpen(false)
        }
        onLogout={handleLogout}
      />

      <div className="min-h-screen lg:pl-72">
        <header
          className="
            sticky top-0 z-20
            flex h-16 items-center
            justify-between
            border-b border-slate-800
            bg-slate-950/95
            px-4 backdrop-blur
            sm:px-6
          "
        >
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() =>
                setSidebarOpen(true)
              }
              className="
                rounded-lg
                border border-slate-800
                px-3 py-2
                text-sm text-slate-300
                hover:bg-slate-900
                lg:hidden
              "
            >
              Menu
            </button>

            <div>
              <p className="text-sm font-medium text-white">
                {user.client?.name ??
                  "Client Workspace"}
              </p>

              <p className="hidden text-xs text-slate-500 sm:block">
                Secure financial monitoring workspace
              </p>
            </div>
          </div>

          <div className="text-right">
            <p className="hidden text-sm text-slate-300 md:block">
              {user.email}
            </p>

            <p className="text-xs text-slate-500">
              {user.role}
            </p>
          </div>
        </header>

        <main className="p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
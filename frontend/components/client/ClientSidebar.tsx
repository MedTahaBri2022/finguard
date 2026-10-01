"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import type { AuthUser } from "@/lib/auth";


interface ClientSidebarProps {
  user: AuthUser;
  isOpen: boolean;
  onClose: () => void;
  onLogout: () => void;
}


const navigationItems = [
  {
    label: "Dashboard",
    href: "/dashboard",
  },
  {
    label: "Analyze",
    href: "/analysis",
  },
  {
    label: "History",
    href: "/history",
  },
  {
    label: "Alerts",
    href: "/alerts",
  },
  {
    label: "Reports",
    href: "/reports",
  },
  {
    label: "Settings",
    href: "/settings",
  },
];


export default function ClientSidebar({
  user,
  isOpen,
  onClose,
  onLogout,
}: ClientSidebarProps) {
  const pathname = usePathname();

  const companyName =
    user.client?.name ?? "FinGuard Client";

  return (
    <>
      {isOpen && (
        <button
          type="button"
          aria-label="Close sidebar"
          onClick={onClose}
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
        />
      )}

      <aside
        className={`
          fixed left-0 top-0 z-40 h-screen w-72
          border-r border-slate-800
          bg-slate-950
          transition-transform duration-200
          lg:translate-x-0
          ${
            isOpen
              ? "translate-x-0"
              : "-translate-x-full"
          }
        `}
      >
        <div className="flex h-full flex-col">
          <div className="border-b border-slate-800 px-6 py-6">
            <Link
              href="/dashboard"
              className="text-2xl font-bold text-white"
              onClick={onClose}
            >
              FinGuard
            </Link>

            <p className="mt-1 text-xs text-slate-500">
              Financial Risk Intelligence
            </p>
          </div>

          <div className="border-b border-slate-800 px-6 py-5">
            <p className="text-sm font-semibold text-white">
              {companyName}
            </p>

            <p className="mt-1 break-all text-xs text-slate-400">
              {user.email}
            </p>

            <div className="mt-3 inline-flex rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-300">
              {user.role}
            </div>
          </div>

          <nav className="flex-1 space-y-1 overflow-y-auto px-4 py-5">
            {navigationItems.map((item) => {
              const active =
                pathname === item.href ||
                (
                  item.href !== "/dashboard" &&
                  pathname.startsWith(
                    `${item.href}/`,
                  )
                );

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onClose}
                  className={`
                    block rounded-xl px-4 py-3
                    text-sm font-medium
                    transition
                    ${
                      active
                        ? "bg-blue-600 text-white"
                        : "text-slate-400 hover:bg-slate-900 hover:text-white"
                    }
                  `}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="border-t border-slate-800 p-4">
            <button
              type="button"
              onClick={onLogout}
              className="
                w-full rounded-xl
                border border-slate-700
                px-4 py-3
                text-left text-sm font-medium
                text-slate-300
                transition
                hover:border-red-800
                hover:bg-red-950/30
                hover:text-red-300
              "
            >
              Logout
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
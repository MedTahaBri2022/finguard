"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import Link from "next/link";

import {
  apiFetch,
} from "@/lib/api";

import type {
  AuthUser,
} from "@/lib/auth";


interface ClientProfile {
  id: number;
  name: string;
  business_type: string | null;
  base_currency: string;
  risk_tolerance: string;
  baseline_ready: boolean;
  minimum_history_rows: number;
  is_active: boolean;
  analysis_count?: number;
  baseline_count?: number;
}


interface ClientsResponse {
  total: number;
  clients: ClientProfile[];
}


export default function AdminDashboardPage() {
  const [
    user,
    setUser,
  ] =
    useState<AuthUser | null>(null);

  const [
    clients,
    setClients,
  ] =
    useState<ClientProfile[]>([]);

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    error,
    setError,
  ] =
    useState<string | null>(null);


  useEffect(() => {
    let active = true;


    async function loadDashboard() {
      try {
        setLoading(true);
        setError(null);


        const [
          currentUser,
          clientsResponse,
        ] =
          await Promise.all([
            apiFetch<AuthUser>(
              "/api/v1/auth/me",
            ),

            apiFetch<ClientsResponse>(
              "/api/v1/clients?active_only=false",
            ),
          ]);


        if (!active) {
          return;
        }


        setUser(
          currentUser,
        );

        setClients(
          Array.isArray(
            clientsResponse.clients,
          )
            ? clientsResponse.clients
            : [],
        );
      } catch (err) {
        if (!active) {
          return;
        }


        if (
          err instanceof Error
        ) {
          setError(
            err.message,
          );
        } else {
          setError(
            "Unable to load admin dashboard.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }


    loadDashboard();


    return () => {
      active = false;
    };
  }, []);


  const activeClients =
    useMemo(
      () =>
        clients.filter(
          (client) =>
            client.is_active,
        ).length,
      [clients],
    );


  const readyBaselines =
    useMemo(
      () =>
        clients.filter(
          (client) =>
            client.baseline_ready,
        ).length,
      [clients],
    );


  const totalAnalyses =
    useMemo(
      () =>
        clients.reduce(
          (
            total,
            client,
          ) =>
            total +
            (
              client.analysis_count ??
              0
            ),
          0,
        ),
      [clients],
    );


  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 p-8 text-white">
        <p className="text-slate-400">
          Loading FinGuard administration...
        </p>
      </main>
    );
  }


  return (
    <div className="space-y-8">
      {/* HEADER */}

      <section
        className="
          flex
          flex-col
          gap-5
          lg:flex-row
          lg:items-end
          lg:justify-between
        "
      >
        <div>
          <p
            className="
              text-sm
              font-medium
              text-purple-400
            "
          >
            FinGuard Platform Administration
          </p>

          <h1
            className="
              mt-1
              text-3xl
              font-bold
              text-white
            "
          >
            Admin Dashboard
          </h1>

          <p
            className="
              mt-2
              max-w-2xl
              text-slate-400
            "
          >
            Manage client organizations,
            baselines and FinGuard platform
            configuration.
          </p>
        </div>


        <Link
          href="/admin/clients"
          className="
            inline-flex
            items-center
            justify-center
            rounded-xl
            bg-purple-600
            px-5
            py-3
            text-sm
            font-semibold
            text-white
            transition
            hover:bg-purple-500
          "
        >
          Manage Clients
        </Link>
      </section>


      {/* ERROR */}

      {error && (
        <section
          className="
            rounded-2xl
            border
            border-red-900/60
            bg-red-950/20
            p-5
          "
        >
          <p
            className="
              font-semibold
              text-red-300
            "
          >
            Admin Error
          </p>

          <p
            className="
              mt-2
              text-sm
              text-red-300
            "
          >
            {error}
          </p>
        </section>
      )}


      {/* KPI */}

      <section
        className="
          grid
          gap-4
          sm:grid-cols-2
          xl:grid-cols-4
        "
      >
        <div
          className="
            rounded-2xl
            border
            border-slate-800
            bg-slate-900
            p-6
          "
        >
          <p
            className="
              text-sm
              text-slate-400
            "
          >
            Total Clients
          </p>

          <p
            className="
              mt-2
              text-4xl
              font-bold
              text-white
            "
          >
            {clients.length}
          </p>
        </div>


        <div
          className="
            rounded-2xl
            border
            border-slate-800
            bg-slate-900
            p-6
          "
        >
          <p
            className="
              text-sm
              text-slate-400
            "
          >
            Active Clients
          </p>

          <p
            className="
              mt-2
              text-4xl
              font-bold
              text-white
            "
          >
            {activeClients}
          </p>
        </div>


        <div
          className="
            rounded-2xl
            border
            border-slate-800
            bg-slate-900
            p-6
          "
        >
          <p
            className="
              text-sm
              text-slate-400
            "
          >
            Ready Baselines
          </p>

          <p
            className="
              mt-2
              text-4xl
              font-bold
              text-white
            "
          >
            {readyBaselines}
          </p>
        </div>


        <div
          className="
            rounded-2xl
            border
            border-slate-800
            bg-slate-900
            p-6
          "
        >
          <p
            className="
              text-sm
              text-slate-400
            "
          >
            Total Analyses
          </p>

          <p
            className="
              mt-2
              text-4xl
              font-bold
              text-white
            "
          >
            {totalAnalyses}
          </p>
        </div>
      </section>


      {/* ADMIN ACCOUNT */}

      <section
        className="
          rounded-2xl
          border
          border-slate-800
          bg-slate-900
          p-6
        "
      >
        <h2
          className="
            text-lg
            font-semibold
            text-white
          "
        >
          Platform Administrator
        </h2>

        <div
          className="
            mt-5
            grid
            gap-5
            sm:grid-cols-3
          "
        >
          <div>
            <p
              className="
                text-xs
                uppercase
                tracking-wide
                text-slate-500
              "
            >
              Email
            </p>

            <p
              className="
                mt-1
                text-sm
                font-medium
                text-white
              "
            >
              {user?.email ??
                "N/A"}
            </p>
          </div>


          <div>
            <p
              className="
                text-xs
                uppercase
                tracking-wide
                text-slate-500
              "
            >
              Role
            </p>

            <p
              className="
                mt-1
                text-sm
                font-medium
                text-purple-300
              "
            >
              {user?.role ??
                "N/A"}
            </p>
          </div>


          <div>
            <p
              className="
                text-xs
                uppercase
                tracking-wide
                text-slate-500
              "
            >
              Client Tenant
            </p>

            <p
              className="
                mt-1
                text-sm
                font-medium
                text-white
              "
            >
              {user?.client_profile_id ===
              null
                ? "Platform-wide"
                : `Client #${user?.client_profile_id}`}
            </p>
          </div>
        </div>
      </section>


      {/* CLIENTS */}

      <section>
        <div
          className="
            flex
            items-end
            justify-between
          "
        >
          <div>
            <h2
              className="
                text-xl
                font-semibold
                text-white
              "
            >
              Client Organizations
            </h2>

            <p
              className="
                mt-1
                text-sm
                text-slate-400
              "
            >
              Current FinGuard tenants.
            </p>
          </div>


          <Link
            href="/admin/clients"
            className="
              text-sm
              font-medium
              text-purple-400
              hover:text-purple-300
            "
          >
            View all
          </Link>
        </div>


        <div
          className="
            mt-5
            overflow-hidden
            rounded-2xl
            border
            border-slate-800
            bg-slate-900
          "
        >
          {clients.length === 0 ? (
            <div
              className="
                p-8
                text-center
                text-slate-400
              "
            >
              No clients available.
            </div>
          ) : (
            <div
              className="
                divide-y
                divide-slate-800
              "
            >
              {clients
                .slice(0, 5)
                .map(
                  (client) => (
                    <div
                      key={
                        client.id
                      }
                      className="
                        flex
                        flex-col
                        gap-4
                        p-5
                        sm:flex-row
                        sm:items-center
                        sm:justify-between
                      "
                    >
                      <div>
                        <div
                          className="
                            flex
                            flex-wrap
                            items-center
                            gap-3
                          "
                        >
                          <h3
                            className="
                              font-semibold
                              text-white
                            "
                          >
                            {client.name}
                          </h3>

                          <span
                            className={`
                              rounded-full
                              border
                              px-2.5
                              py-1
                              text-xs
                              ${
                                client.is_active
                                  ? `
                                    border-emerald-900
                                    bg-emerald-950/40
                                    text-emerald-300
                                  `
                                  : `
                                    border-red-900
                                    bg-red-950/40
                                    text-red-300
                                  `
                              }
                            `}
                          >
                            {client.is_active
                              ? "Active"
                              : "Inactive"}
                          </span>
                        </div>

                        <p
                          className="
                            mt-2
                            text-sm
                            text-slate-400
                          "
                        >
                          {client.business_type ??
                            "Business type not configured"}
                          {" · "}
                          {client.base_currency}
                        </p>
                      </div>


                      <Link
                        href={`/admin/clients/${client.id}`}
                        className="
                          rounded-xl
                          border
                          border-slate-700
                          px-4
                          py-2
                          text-center
                          text-sm
                          font-medium
                          text-slate-300
                          transition
                          hover:bg-slate-800
                        "
                      >
                        Manage
                      </Link>
                    </div>
                  ),
                )}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
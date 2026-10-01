"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  apiFetch,
} from "@/lib/api";


interface ClientProfileResponse {
  id: number;
  name: string;
  business_type: string | null;
  base_currency: string;
  risk_tolerance: string;
  baseline_ready: boolean;
  minimum_history_rows: number;
  analysis_count: number;
  baseline_count: number;
}


interface AnalysisItem {
  id: number;
  filename: string;
  rows: number;
  columns: number;
  risk_score: number;
  risk_level: string;
  total_findings: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  money_at_risk: number;
  created_at: string;
}


interface HistoryResponse {
  analyses?: AnalysisItem[];
  items?: AnalysisItem[];
  history?: AnalysisItem[];
}


export default function DashboardPage() {
  const [client, setClient] =
    useState<ClientProfileResponse | null>(null);

  const [analyses, setAnalyses] =
    useState<AnalysisItem[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);


  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      try {
        setLoading(true);
        setError(null);

        const [
          clientData,
          historyData,
        ] = await Promise.all([
          apiFetch<ClientProfileResponse>(
            "/api/v1/clients/me",
          ),

          apiFetch<
            AnalysisItem[] | HistoryResponse
          >(
            "/api/v1/history/",
          ),
        ]);


        if (!active) {
          return;
        }


        let normalizedAnalyses:
          AnalysisItem[] = [];


        if (Array.isArray(historyData)) {
          normalizedAnalyses =
            historyData;
        } else if (
          Array.isArray(
            historyData.analyses,
          )
        ) {
          normalizedAnalyses =
            historyData.analyses;
        } else if (
          Array.isArray(
            historyData.items,
          )
        ) {
          normalizedAnalyses =
            historyData.items;
        } else if (
          Array.isArray(
            historyData.history,
          )
        ) {
          normalizedAnalyses =
            historyData.history;
        }


        setClient(clientData);

        setAnalyses(
          normalizedAnalyses,
        );
      } catch (err) {
        if (!active) {
          return;
        }

        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError(
            "Unable to load dashboard data.",
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


  const latestAnalysis =
    useMemo(() => {
      if (
        !Array.isArray(analyses) ||
        analyses.length === 0
      ) {
        return null;
      }

      return [...analyses].sort(
        (a, b) =>
          new Date(
            b.created_at,
          ).getTime() -
          new Date(
            a.created_at,
          ).getTime(),
      )[0];
    }, [analyses]);


  function formatMoney(
    value: number,
  ) {
    const currency =
      client?.base_currency ??
      "MAD";

    try {
      return new Intl.NumberFormat(
        "fr-MA",
        {
          style: "currency",
          currency,
          maximumFractionDigits: 2,
        },
      ).format(value);
    } catch {
      return `${value.toFixed(
        2,
      )} ${currency}`;
    }
  }


  function formatDate(
    value: string,
  ) {
    const date =
      new Date(value);

    if (
      Number.isNaN(
        date.getTime(),
      )
    ) {
      return value;
    }

    return date.toLocaleString();
  }


  if (loading) {
    return (
      <div>
        <div className="mb-8">
          <p className="text-sm font-medium text-blue-400">
            Client Workspace
          </p>

          <h1 className="mt-1 text-3xl font-bold">
            Dashboard
          </h1>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <p className="text-sm text-slate-400">
            Loading financial intelligence...
          </p>
        </div>
      </div>
    );
  }


  if (error) {
    return (
      <div>
        <div className="mb-8">
          <p className="text-sm font-medium text-blue-400">
            Client Workspace
          </p>

          <h1 className="mt-1 text-3xl font-bold">
            Dashboard
          </h1>
        </div>

        <div className="rounded-2xl border border-red-900/60 bg-red-950/20 p-5">
          <p className="font-medium text-red-300">
            Unable to load dashboard
          </p>

          <p className="mt-2 text-sm text-red-300/80">
            {error}
          </p>
        </div>
      </div>
    );
  }


  return (
    <div>
      <div className="mb-8">
        <p className="text-sm font-medium text-blue-400">
          Client Workspace
        </p>

        <h1 className="mt-1 text-3xl font-bold">
          {client?.name ??
            "Dashboard"}
        </h1>

        <p className="mt-2 text-slate-400">
          Financial risk overview and
          recent FinGuard activity.
        </p>
      </div>


      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <p className="text-sm text-slate-400">
            Latest Risk Score
          </p>

          <p className="mt-3 text-3xl font-bold">
            {latestAnalysis
              ? latestAnalysis.risk_score.toFixed(
                  2,
                )
              : "--"}
          </p>

          <p className="mt-2 text-xs text-slate-500">
            {latestAnalysis
              ? latestAnalysis.risk_level
              : "No analysis yet"}
          </p>
        </div>


        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <p className="text-sm text-slate-400">
            Money At Risk
          </p>

          <p className="mt-3 text-2xl font-bold">
            {latestAnalysis
              ? formatMoney(
                  latestAnalysis.money_at_risk,
                )
              : "--"}
          </p>

          <p className="mt-2 text-xs text-slate-500">
            Latest analysis
          </p>
        </div>


        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <p className="text-sm text-slate-400">
            Findings
          </p>

          <p className="mt-3 text-3xl font-bold">
            {latestAnalysis
              ? latestAnalysis.total_findings
              : 0}
          </p>

          <p className="mt-2 text-xs text-slate-500">
            High risk:{" "}
            {latestAnalysis?.high_risk ??
              0}
          </p>
        </div>


        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <p className="text-sm text-slate-400">
            Analyses
          </p>

          <p className="mt-3 text-3xl font-bold">
            {client?.analysis_count ??
              analyses.length}
          </p>

          <p className="mt-2 text-xs text-slate-500">
            Total company analyses
          </p>
        </div>
      </div>


      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-lg font-semibold">
            Company Profile
          </h2>

          <p className="mt-1 text-sm text-slate-400">
            Current FinGuard client
            configuration.
          </p>


          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between gap-4 border-b border-slate-800 pb-3">
              <span className="text-sm text-slate-400">
                Business Type
              </span>

              <span className="text-right text-sm font-medium">
                {client?.business_type ??
                  "Not configured"}
              </span>
            </div>


            <div className="flex items-center justify-between gap-4 border-b border-slate-800 pb-3">
              <span className="text-sm text-slate-400">
                Base Currency
              </span>

              <span className="text-sm font-medium">
                {client?.base_currency ??
                  "--"}
              </span>
            </div>


            <div className="flex items-center justify-between gap-4 border-b border-slate-800 pb-3">
              <span className="text-sm text-slate-400">
                Risk Tolerance
              </span>

              <span className="text-sm font-medium capitalize">
                {client?.risk_tolerance ??
                  "--"}
              </span>
            </div>


            <div className="flex items-center justify-between gap-4">
              <span className="text-sm text-slate-400">
                Client ID
              </span>

              <span className="text-sm font-medium">
                {client?.id ??
                  "--"}
              </span>
            </div>
          </div>
        </div>


        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold">
                Risk Baseline
              </h2>

              <p className="mt-1 text-sm text-slate-400">
                Historical company reference
                used by FinGuard.
              </p>
            </div>


            <span
              className={`
                rounded-full
                border
                px-3
                py-1
                text-xs
                font-medium
                ${
                  client?.baseline_ready
                    ? "border-emerald-900 bg-emerald-950/40 text-emerald-300"
                    : "border-amber-900 bg-amber-950/40 text-amber-300"
                }
              `}
            >
              {client?.baseline_ready
                ? "Ready"
                : "Not Ready"}
            </span>
          </div>


          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between gap-4 border-b border-slate-800 pb-3">
              <span className="text-sm text-slate-400">
                Baseline Status
              </span>

              <span className="text-sm font-medium">
                {client?.baseline_ready
                  ? "Operational"
                  : "Pending"}
              </span>
            </div>


            <div className="flex items-center justify-between gap-4 border-b border-slate-800 pb-3">
              <span className="text-sm text-slate-400">
                Baseline Versions
              </span>

              <span className="text-sm font-medium">
                {client?.baseline_count ??
                  0}
              </span>
            </div>


            <div className="flex items-center justify-between gap-4">
              <span className="text-sm text-slate-400">
                Minimum History Rows
              </span>

              <span className="text-sm font-medium">
                {client?.minimum_history_rows ??
                  "--"}
              </span>
            </div>
          </div>
        </div>
      </div>


      <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <div>
          <h2 className="text-lg font-semibold">
            Latest Analysis
          </h2>

          <p className="mt-1 text-sm text-slate-400">
            Most recent company risk scan.
          </p>
        </div>


        {latestAnalysis ? (
          <>
            <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  File
                </p>

                <p className="mt-2 break-all text-sm font-medium">
                  {latestAnalysis.filename}
                </p>
              </div>


              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  Risk Level
                </p>

                <p className="mt-2 text-sm font-medium">
                  {latestAnalysis.risk_level}
                </p>
              </div>


              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  Rows
                </p>

                <p className="mt-2 text-sm font-medium">
                  {latestAnalysis.rows}
                </p>
              </div>


              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  Date
                </p>

                <p className="mt-2 text-sm font-medium">
                  {formatDate(
                    latestAnalysis.created_at,
                  )}
                </p>
              </div>
            </div>


            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                <p className="text-xs text-slate-500">
                  High
                </p>

                <p className="mt-2 text-xl font-semibold">
                  {latestAnalysis.high_risk}
                </p>
              </div>


              <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                <p className="text-xs text-slate-500">
                  Medium
                </p>

                <p className="mt-2 text-xl font-semibold">
                  {latestAnalysis.medium_risk}
                </p>
              </div>


              <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                <p className="text-xs text-slate-500">
                  Low
                </p>

                <p className="mt-2 text-xl font-semibold">
                  {latestAnalysis.low_risk}
                </p>
              </div>
            </div>
          </>
        ) : (
          <p className="mt-6 text-sm text-slate-400">
            No analysis has been created yet.
          </p>
        )}
      </div>
    </div>
  );
}
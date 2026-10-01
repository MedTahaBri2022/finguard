"use client";

import { useEffect, useMemo, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

type Analysis = {
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
  ai_summary?: string | null;
  created_at?: string | null;
};

type Alert = {
  id: number;
  title: string;
  alert_type: string;
  severity: string;
  message: string;
  amount_at_risk?: number | null;
  transaction_id?: string | null;
  is_read: boolean;
  created_at?: string | null;
};

export default function DashboardPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    setLoading(true);
    setError("");

    try {
      const [historyResponse, alertsResponse] = await Promise.all([
        fetch(`${API_URL}/api/v1/history`, {
          cache: "no-store",
        }),
        fetch(`${API_URL}/api/v1/alerts/`, {
          cache: "no-store",
        }),
      ]);

      const historyData = await historyResponse.json();
      const alertsData = await alertsResponse.json();

      if (!historyResponse.ok) {
        throw new Error(
          historyData.detail || "Unable to load analysis history."
        );
      }

      if (!alertsResponse.ok) {
        throw new Error(
          alertsData.detail || "Unable to load alerts."
        );
      }

      setAnalyses(historyData.analyses || []);
      setAlerts(alertsData.alerts || []);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to connect to FinGuard backend."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const stats = useMemo(() => {
    const totalMoneyAtRisk = analyses.reduce(
      (sum, analysis) => sum + Number(analysis.money_at_risk || 0),
      0
    );

    const totalFindings = analyses.reduce(
      (sum, analysis) => sum + Number(analysis.total_findings || 0),
      0
    );

    const highRiskAnalyses = analyses.filter(
      (analysis) => analysis.risk_level?.toLowerCase() === "high"
    ).length;

    const unreadAlerts = alerts.filter(
      (alert) => !alert.is_read
    ).length;

    return {
      totalAnalyses: analyses.length,
      totalMoneyAtRisk,
      totalFindings,
      highRiskAnalyses,
      unreadAlerts,
    };
  }, [analyses, alerts]);

  const recentAnalyses = analyses.slice(0, 5);
  const recentAlerts = alerts.slice(0, 5);

  function formatMoney(value: number) {
    return `${Number(value || 0).toLocaleString("fr-FR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })} DH`;
  }

  function formatDate(date?: string | null) {
    if (!date) return "—";

    const parsedDate = new Date(date);

    if (Number.isNaN(parsedDate.getTime())) {
      return date;
    }

    return parsedDate.toLocaleString();
  }

  function getRiskStyle(level: string) {
    const normalized = level?.toLowerCase();

    if (normalized === "high") {
      return "border-red-500/20 bg-red-500/10 text-red-400";
    }

    if (normalized === "medium") {
      return "border-yellow-500/20 bg-yellow-500/10 text-yellow-400";
    }

    return "border-green-500/20 bg-green-500/10 text-green-400";
  }

  return (
    <main className="min-h-screen bg-[#070b14] text-white">
      <Navbar />

      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="mb-8">
          <p className="text-sm text-blue-400">
            AI Financial Intelligence
          </p>

          <h2 className="mt-2 text-4xl font-bold">
            FinGuard Dashboard
          </h2>

          <p className="mt-3 max-w-2xl text-slate-400">
            Monitor financial risks, detect anomalies and identify
            potential business losses.
          </p>
        </div>

        {error && (
          <div className="mb-8 rounded-2xl border border-red-500/20 bg-red-500/10 p-5">
            <p className="font-semibold text-red-400">
              Dashboard Error
            </p>

            <p className="mt-2 text-sm text-slate-400">
              {error}
            </p>
          </div>
        )}

        <section className="mb-8 grid gap-4 md:grid-cols-3">
          <a
            href="/analysis"
            className="rounded-2xl border border-blue-500/20 bg-blue-500/5 p-6 transition hover:bg-blue-500/10"
          >
            <p className="text-sm text-blue-400">Start</p>

            <h3 className="mt-1 text-xl font-bold">
              New Analysis
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              Upload CSV or Excel data and detect financial risks.
            </p>
          </a>

          <a
            href="/history"
            className="rounded-2xl border border-white/10 bg-[#0d1424] p-6 transition hover:bg-[#111a2d]"
          >
            <p className="text-sm text-slate-500">Review</p>

            <h3 className="mt-1 text-xl font-bold">
              Analysis History
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              Review previous reports and financial exposure.
            </p>
          </a>

          <a
            href="/alerts"
            className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6 transition hover:bg-red-500/10"
          >
            <p className="text-sm text-red-400">Monitor</p>

            <h3 className="mt-1 text-xl font-bold">
              Alert Center
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              Investigate detected financial anomalies.
            </p>
          </a>
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <StatCard
            title="Total Analyses"
            value={stats.totalAnalyses.toLocaleString()}
          />

          <StatCard
            title="Money At Risk"
            value={formatMoney(stats.totalMoneyAtRisk)}
            danger
          />

          <StatCard
            title="Total Findings"
            value={stats.totalFindings.toLocaleString()}
          />

          <StatCard
            title="High Risk"
            value={stats.highRiskAnalyses.toLocaleString()}
            danger
          />

          <StatCard
            title="Unread Alerts"
            value={stats.unreadAlerts.toLocaleString()}
            danger
          />
        </section>

        <section className="mt-8 overflow-hidden rounded-2xl border border-white/10 bg-[#0d1424]">
          <div className="flex items-center justify-between border-b border-white/10 p-6">
            <div>
              <h3 className="text-xl font-bold">
                Recent Analyses
              </h3>

              <p className="mt-1 text-sm text-slate-500">
                Latest FinGuard financial reports.
              </p>
            </div>

            <a
              href="/history"
              className="text-sm font-semibold text-blue-400"
            >
              View All →
            </a>
          </div>

          {loading ? (
            <Loading text="Loading analyses..." />
          ) : recentAnalyses.length === 0 ? (
            <EmptyState text="No analyses available yet." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-[#0b1020] text-left text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-6 py-4">File</th>
                    <th className="px-6 py-4">Risk</th>
                    <th className="px-6 py-4">Score</th>
                    <th className="px-6 py-4">Findings</th>
                    <th className="px-6 py-4">Money At Risk</th>
                    <th className="px-6 py-4">Action</th>
                  </tr>
                </thead>

                <tbody>
                  {recentAnalyses.map((analysis) => (
                    <tr
                      key={analysis.id}
                      className="border-t border-white/5"
                    >
                      <td className="px-6 py-5">
                        <p className="font-semibold">
                          {analysis.filename}
                        </p>

                        <p className="mt-1 text-xs text-slate-600">
                          {analysis.rows.toLocaleString()} rows •{" "}
                          {analysis.columns} columns
                        </p>
                      </td>

                      <td className="px-6 py-5">
                        <span
                          className={`rounded-full border px-3 py-1 text-xs font-semibold ${getRiskStyle(
                            analysis.risk_level
                          )}`}
                        >
                          {analysis.risk_level.toUpperCase()}
                        </span>
                      </td>

                      <td className="px-6 py-5 font-bold">
                        {analysis.risk_score}/100
                      </td>

                      <td className="px-6 py-5">
                        {analysis.total_findings}
                      </td>

                      <td className="px-6 py-5 font-semibold text-red-400">
                        {formatMoney(analysis.money_at_risk)}
                      </td>

                      <td className="px-6 py-5">
                        <a
                          href={`/analysis/${analysis.id}`}
                          className="rounded-lg border border-slate-700 px-4 py-2 text-xs font-semibold"
                        >
                          View Details
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="mt-8 overflow-hidden rounded-2xl border border-white/10 bg-[#0d1424]">
          <div className="flex items-center justify-between border-b border-white/10 p-6">
            <div>
              <h3 className="text-xl font-bold">
                Recent Alerts
              </h3>

              <p className="mt-1 text-sm text-slate-500">
                Latest financial anomalies detected.
              </p>
            </div>

            <a
              href="/alerts"
              className="text-sm font-semibold text-blue-400"
            >
              View All →
            </a>
          </div>

          {loading ? (
            <Loading text="Loading alerts..." />
          ) : recentAlerts.length === 0 ? (
            <EmptyState text="No alerts detected." />
          ) : (
            <div className="divide-y divide-white/5">
              {recentAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className="flex flex-col justify-between gap-4 p-6 md:flex-row"
                >
                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <span
                        className={`rounded-full border px-3 py-1 text-xs font-semibold ${getRiskStyle(
                          alert.severity
                        )}`}
                      >
                        {alert.severity.toUpperCase()}
                      </span>

                      <span className="text-xs text-slate-600">
                        {alert.alert_type}
                      </span>

                      {!alert.is_read && (
                        <span className="text-xs text-blue-400">
                          UNREAD
                        </span>
                      )}
                    </div>

                    <h4 className="mt-3 font-semibold">
                      {alert.title}
                    </h4>

                    <p className="mt-2 text-sm text-slate-400">
                      {alert.message}
                    </p>
                  </div>

                  <div className="shrink-0 md:text-right">
                    {alert.amount_at_risk != null && (
                      <p className="font-bold text-red-400">
                        {formatMoney(alert.amount_at_risk)}
                      </p>
                    )}

                    <p className="mt-2 text-xs text-slate-600">
                      {formatDate(alert.created_at)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

function Navbar() {
  return (
    <nav className="border-b border-white/10 bg-[#0b1020]">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
        <a href="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 font-bold">
            FG
          </div>

          <div>
            <h1 className="font-bold">FinGuard</h1>

            <p className="text-xs text-slate-500">
              Financial Intelligence
            </p>
          </div>
        </a>

        <div className="flex items-center gap-3">
          <a
            href="/analysis"
            className="text-sm text-slate-300"
          >
            Analysis
          </a>

          <a
            href="/history"
            className="text-sm text-slate-300"
          >
            History
          </a>

          <a
            href="/alerts"
            className="text-sm text-slate-300"
          >
            Alerts
          </a>
        </div>
      </div>
    </nav>
  );
}

function StatCard({
  title,
  value,
  danger = false,
}: {
  title: string;
  value: string;
  danger?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-[#0d1424] p-6">
      <p className="text-sm text-slate-500">
        {title}
      </p>

      <p
        className={`mt-3 text-2xl font-bold ${
          danger ? "text-red-400" : "text-white"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function Loading({
  text,
}: {
  text: string;
}) {
  return (
    <div className="p-10 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}

function EmptyState({
  text,
}: {
  text: string;
}) {
  return (
    <div className="p-10 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}
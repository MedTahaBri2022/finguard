"use client";

import Link from "next/link";
import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  apiFetch,
} from "@/lib/api";


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


function normalizeHistory(
  data: AnalysisItem[] | HistoryResponse,
): AnalysisItem[] {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data.analyses)) {
    return data.analyses;
  }

  if (Array.isArray(data.items)) {
    return data.items;
  }

  if (Array.isArray(data.history)) {
    return data.history;
  }

  return [];
}


function riskBadgeClass(
  riskLevel: string,
): string {
  const value =
    riskLevel.toUpperCase();

  if (value === "HIGH") {
    return "border-red-900 bg-red-950/40 text-red-300";
  }

  if (value === "MEDIUM") {
    return "border-amber-900 bg-amber-950/40 text-amber-300";
  }

  return "border-emerald-900 bg-emerald-950/40 text-emerald-300";
}


export default function HistoryPage() {
  const [analyses, setAnalyses] =
    useState<AnalysisItem[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const [search, setSearch] =
    useState("");


  useEffect(() => {
    let active = true;

    async function loadHistory() {
      try {
        setLoading(true);
        setError(null);

        const data =
          await apiFetch<
            AnalysisItem[] | HistoryResponse
          >(
            "/api/v1/history/",
          );

        if (!active) {
          return;
        }

        setAnalyses(
          normalizeHistory(data),
        );
      } catch (err) {
        if (!active) {
          return;
        }

        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError(
            "Unable to load analysis history.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadHistory();

    return () => {
      active = false;
    };
  }, []);


  const filteredAnalyses =
    useMemo(() => {
      const query =
        search.trim().toLowerCase();

      if (!query) {
        return analyses;
      }

      return analyses.filter(
        (analysis) =>
          analysis.filename
            .toLowerCase()
            .includes(query) ||
          analysis.risk_level
            .toLowerCase()
            .includes(query) ||
          String(analysis.id).includes(
            query,
          ),
      );
    }, [
      analyses,
      search,
    ]);


  function formatMoney(
    value: number,
  ) {
    return new Intl.NumberFormat(
      "fr-MA",
      {
        style: "currency",
        currency: "MAD",
        maximumFractionDigits: 2,
      },
    ).format(value);
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

    return date.toLocaleString(
      "fr-MA",
    );
  }


  if (loading) {
    return (
      <div>
        <h1 className="text-3xl font-bold">
          History
        </h1>

        <p className="mt-2 text-slate-400">
          Loading company analyses...
        </p>
      </div>
    );
  }


  if (error) {
    return (
      <div>
        <h1 className="text-3xl font-bold">
          History
        </h1>

        <div className="mt-6 rounded-2xl border border-red-900/60 bg-red-950/20 p-5">
          <p className="font-medium text-red-300">
            Unable to load history
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
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-blue-400">
            Client Workspace
          </p>

          <h1 className="mt-1 text-3xl font-bold">
            Analysis History
          </h1>

          <p className="mt-2 text-slate-400">
            Review previous financial risk
            analyses for your company.
          </p>
        </div>

        <Link
          href="/analysis"
          className="
            inline-flex items-center
            justify-center
            rounded-xl
            bg-blue-600
            px-5 py-3
            text-sm font-semibold
            text-white
            transition
            hover:bg-blue-500
          "
        >
          New Analysis
        </Link>
      </div>


      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Total Analyses
          </p>

          <p className="mt-2 text-3xl font-bold">
            {analyses.length}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            High Risk
          </p>

          <p className="mt-2 text-3xl font-bold">
            {
              analyses.filter(
                (item) =>
                  item.risk_level
                    .toUpperCase() ===
                  "HIGH",
              ).length
            }
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Medium Risk
          </p>

          <p className="mt-2 text-3xl font-bold">
            {
              analyses.filter(
                (item) =>
                  item.risk_level
                    .toUpperCase() ===
                  "MEDIUM",
              ).length
            }
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Money At Risk
          </p>

          <p className="mt-2 text-xl font-bold">
            {formatMoney(
              analyses.reduce(
                (sum, item) =>
                  sum +
                  (
                    item.money_at_risk ??
                    0
                  ),
                0,
              ),
            )}
          </p>
        </div>
      </div>


      <div className="mt-8">
        <input
          type="text"
          value={search}
          onChange={(event) =>
            setSearch(
              event.target.value,
            )
          }
          placeholder="Search by file, ID or risk level..."
          className="
            w-full max-w-md
            rounded-xl
            border border-slate-800
            bg-slate-900
            px-4 py-3
            text-sm text-white
            outline-none
            placeholder:text-slate-500
            focus:border-blue-600
          "
        />
      </div>


      <div className="mt-6 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
        {filteredAnalyses.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-slate-400">
              No analyses found.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="border-b border-slate-800 bg-slate-950/40">
                <tr>
                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    ID
                  </th>

                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    File
                  </th>

                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Risk
                  </th>

                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Findings
                  </th>

                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Money At Risk
                  </th>

                  <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Date
                  </th>

                  <th className="px-5 py-4 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Action
                  </th>
                </tr>
              </thead>

              <tbody>
                {filteredAnalyses.map(
                  (analysis) => (
                    <tr
                      key={analysis.id}
                      className="border-b border-slate-800/70 last:border-b-0 hover:bg-slate-800/30"
                    >
                      <td className="px-5 py-4 text-sm text-slate-400">
                        #{analysis.id}
                      </td>

                      <td className="max-w-xs px-5 py-4">
                        <p className="truncate text-sm font-medium text-white">
                          {
                            analysis.filename
                          }
                        </p>

                        <p className="mt-1 text-xs text-slate-500">
                          {analysis.rows} rows
                          {" • "}
                          {analysis.columns} columns
                        </p>
                      </td>

                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <span
                            className={`
                              rounded-full
                              border
                              px-3 py-1
                              text-xs font-medium
                              ${riskBadgeClass(
                                analysis.risk_level,
                              )}
                            `}
                          >
                            {
                              analysis.risk_level
                            }
                          </span>

                          <span className="text-sm font-semibold">
                            {
                              analysis.risk_score
                            }
                          </span>
                        </div>
                      </td>

                      <td className="px-5 py-4 text-sm">
                        {
                          analysis.total_findings
                        }
                      </td>

                      <td className="px-5 py-4 text-sm font-medium">
                        {formatMoney(
                          analysis.money_at_risk ??
                            0,
                        )}
                      </td>

                      <td className="px-5 py-4 text-sm text-slate-400">
                        {formatDate(
                          analysis.created_at,
                        )}
                      </td>

                      <td className="px-5 py-4 text-right">
                        <Link
                          href={`/analysis/${analysis.id}`}
                          className="text-sm font-medium text-blue-400 hover:text-blue-300"
                        >
                          View details
                        </Link>
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
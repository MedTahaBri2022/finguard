"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import Link from "next/link";

import {
  API_BASE_URL,
  apiFetch,
} from "@/lib/api";

import {
  getAccessToken,
} from "@/lib/auth";


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
  created_at: string | null;
}


interface HistoryResponse {
  success: boolean;
  count: number;
  analyses: AnalysisItem[];
}


function riskClass(
  riskLevel: string,
): string {
  const level =
    riskLevel.toUpperCase();

  if (level === "HIGH") {
    return (
      "border-red-900 " +
      "bg-red-950/40 " +
      "text-red-300"
    );
  }

  if (level === "MEDIUM") {
    return (
      "border-amber-900 " +
      "bg-amber-950/40 " +
      "text-amber-300"
    );
  }

  return (
    "border-emerald-900 " +
    "bg-emerald-950/40 " +
    "text-emerald-300"
  );
}


export default function ReportsPage() {
  const [
    analyses,
    setAnalyses,
  ] =
    useState<AnalysisItem[]>([]);

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

  const [
    downloadingId,
    setDownloadingId,
  ] =
    useState<number | null>(null);

  const [
    search,
    setSearch,
  ] =
    useState("");


  useEffect(() => {
    let active = true;

    async function loadReports() {
      try {
        setLoading(true);
        setError(null);

        const response =
          await apiFetch<HistoryResponse>(
            "/api/v1/history",
          );

        if (!active) {
          return;
        }

        setAnalyses(
          Array.isArray(
            response.analyses,
          )
            ? response.analyses
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
            "Unable to load reports.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadReports();

    return () => {
      active = false;
    };
  }, []);


  const filteredAnalyses =
    useMemo(() => {
      const value =
        search
          .trim()
          .toLowerCase();

      if (!value) {
        return analyses;
      }

      return analyses.filter(
        (analysis) =>
          analysis.filename
            .toLowerCase()
            .includes(value) ||
          analysis.risk_level
            .toLowerCase()
            .includes(value) ||
          String(
            analysis.id,
          ).includes(value),
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
    value: string | null,
  ) {
    if (!value) {
      return "N/A";
    }

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


  function getFilenameFromHeader(
    contentDisposition: string | null,
    analysisId: number,
  ) {
    if (!contentDisposition) {
      return (
        `finguard_analysis_` +
        `${analysisId}.pdf`
      );
    }

    const match =
      contentDisposition.match(
        /filename="?([^"]+)"?/i,
      );

    if (
      match &&
      match[1]
    ) {
      return match[1];
    }

    return (
      `finguard_analysis_` +
      `${analysisId}.pdf`
    );
  }


  async function handleDownload(
    analysis: AnalysisItem,
  ) {
    try {
      setDownloadingId(
        analysis.id,
      );

      setError(null);

      const token =
        getAccessToken();

      if (!token) {
        throw new Error(
          "Authentication required.",
        );
      }

      const response =
        await fetch(
          `${API_BASE_URL}/api/v1/reports/${analysis.id}/pdf`,
          {
            method: "GET",

            headers: {
              Authorization:
                `Bearer ${token}`,
            },
          },
        );


      if (!response.ok) {
        let message =
          "Unable to download report.";

        const contentType =
          response.headers.get(
            "content-type",
          ) ?? "";

        if (
          contentType.includes(
            "application/json",
          )
        ) {
          const data =
            await response.json();

          if (
            data &&
            typeof data ===
              "object" &&
            "detail" in data &&
            typeof (
              data as {
                detail?: unknown;
              }
            ).detail === "string"
          ) {
            message =
              (
                data as {
                  detail: string;
                }
              ).detail;
          }
        }

        throw new Error(
          message,
        );
      }


      const blob =
        await response.blob();

      const contentType =
        response.headers.get(
          "content-type",
        ) ?? "";

      if (
        !contentType.includes(
          "application/pdf",
        )
      ) {
        throw new Error(
          "The server did not return a valid PDF report.",
        );
      }


      const filename =
        getFilenameFromHeader(
          response.headers.get(
            "content-disposition",
          ),
          analysis.id,
        );


      const objectUrl =
        URL.createObjectURL(
          blob,
        );

      const link =
        document.createElement(
          "a",
        );

      link.href =
        objectUrl;

      link.download =
        filename;

      document.body.appendChild(
        link,
      );

      link.click();

      link.remove();

      URL.revokeObjectURL(
        objectUrl,
      );
    } catch (err) {
      if (
        err instanceof Error
      ) {
        setError(
          err.message,
        );
      } else {
        setError(
          "Unable to download report.",
        );
      }
    } finally {
      setDownloadingId(
        null,
      );
    }
  }


  const totalMoneyAtRisk =
    useMemo(
      () =>
        analyses.reduce(
          (
            total,
            analysis,
          ) =>
            total +
            (
              analysis.money_at_risk ??
              0
            ),
          0,
        ),
      [analyses],
    );


  const highRiskReports =
    useMemo(
      () =>
        analyses.filter(
          (analysis) =>
            analysis.risk_level
              .toUpperCase() ===
            "HIGH",
        ).length,
      [analyses],
    );


  if (loading) {
    return (
      <div>
        <h1 className="text-3xl font-bold text-white">
          Reports
        </h1>

        <p className="mt-3 text-slate-400">
          Loading company reports...
        </p>
      </div>
    );
  }


  return (
    <div className="space-y-8">
      {/* HEADER */}
      <section className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-medium text-blue-400">
            Client Workspace
          </p>

          <h1 className="mt-1 text-3xl font-bold text-white">
            Reports
          </h1>

          <p className="mt-2 max-w-2xl text-slate-400">
            View your company analyses and
            download secure FinGuard PDF
            financial intelligence reports.
          </p>
        </div>


        <Link
          href="/analysis"
          className="
            inline-flex
            items-center
            justify-center
            rounded-xl
            bg-blue-600
            px-5
            py-3
            text-sm
            font-semibold
            text-white
            transition
            hover:bg-blue-500
          "
        >
          New Analysis
        </Link>
      </section>


      {/* ERROR */}
      {error && (
        <section className="rounded-2xl border border-red-900/60 bg-red-950/20 p-5">
          <p className="font-semibold text-red-300">
            Reports Error
          </p>

          <p className="mt-2 text-sm text-red-300">
            {error}
          </p>
        </section>
      )}


      {/* KPI */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Available Reports
          </p>

          <p className="mt-2 text-3xl font-bold text-white">
            {analyses.length}
          </p>
        </div>


        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            High Risk Reports
          </p>

          <p className="mt-2 text-3xl font-bold text-white">
            {highRiskReports}
          </p>
        </div>


        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Total Findings
          </p>

          <p className="mt-2 text-3xl font-bold text-white">
            {analyses.reduce(
              (
                total,
                analysis,
              ) =>
                total +
                (
                  analysis.total_findings ??
                  0
                ),
              0,
            )}
          </p>
        </div>


        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Total Money At Risk
          </p>

          <p className="mt-2 text-xl font-bold text-white">
            {formatMoney(
              totalMoneyAtRisk,
            )}
          </p>
        </div>
      </section>


      {/* SEARCH */}
      <section>
        <input
          type="text"
          value={search}
          onChange={(event) =>
            setSearch(
              event.target.value,
            )
          }
          placeholder="Search by file, risk level or analysis ID..."
          className="
            w-full
            rounded-xl
            border
            border-slate-700
            bg-slate-900
            px-4
            py-3
            text-sm
            text-white
            outline-none
            transition
            placeholder:text-slate-500
            focus:border-blue-500
          "
        />
      </section>


      {/* REPORTS */}
      <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
        {filteredAnalyses.length === 0 ? (
          <div className="p-10 text-center">
            <p className="text-slate-400">
              No reports found.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {filteredAnalyses.map(
              (analysis) => (
                <article
                  key={analysis.id}
                  className="p-5 transition hover:bg-slate-800/30"
                >
                  <div className="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-3">
                        <span
                          className={`
                            rounded-full
                            border
                            px-3
                            py-1
                            text-xs
                            font-semibold
                            ${riskClass(
                              analysis.risk_level,
                            )}
                          `}
                        >
                          {analysis.risk_level}
                        </span>

                        <span className="text-xs text-slate-500">
                          Analysis #{analysis.id}
                        </span>
                      </div>


                      <h2 className="mt-3 truncate text-base font-semibold text-white">
                        {analysis.filename}
                      </h2>


                      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                        <div>
                          <p className="text-xs uppercase tracking-wide text-slate-500">
                            Risk Score
                          </p>

                          <p className="mt-1 text-sm font-medium text-white">
                            {analysis.risk_score.toFixed(
                              2,
                            )}
                          </p>
                        </div>


                        <div>
                          <p className="text-xs uppercase tracking-wide text-slate-500">
                            Findings
                          </p>

                          <p className="mt-1 text-sm font-medium text-white">
                            {analysis.total_findings}
                          </p>
                        </div>


                        <div>
                          <p className="text-xs uppercase tracking-wide text-slate-500">
                            Money At Risk
                          </p>

                          <p className="mt-1 text-sm font-medium text-white">
                            {formatMoney(
                              analysis.money_at_risk,
                            )}
                          </p>
                        </div>


                        <div>
                          <p className="text-xs uppercase tracking-wide text-slate-500">
                            Created
                          </p>

                          <p className="mt-1 text-sm text-slate-300">
                            {formatDate(
                              analysis.created_at,
                            )}
                          </p>
                        </div>
                      </div>
                    </div>


                    <div className="flex shrink-0 flex-wrap gap-3">
                      <Link
                        href={`/analysis/${analysis.id}`}
                        className="
                          rounded-xl
                          border
                          border-slate-700
                          px-4
                          py-2
                          text-sm
                          font-medium
                          text-slate-300
                          transition
                          hover:bg-slate-800
                        "
                      >
                        View Analysis
                      </Link>


                      <button
                        type="button"
                        onClick={() =>
                          handleDownload(
                            analysis,
                          )
                        }
                        disabled={
                          downloadingId ===
                          analysis.id
                        }
                        className="
                          rounded-xl
                          bg-blue-600
                          px-4
                          py-2
                          text-sm
                          font-semibold
                          text-white
                          transition
                          hover:bg-blue-500
                          disabled:cursor-not-allowed
                          disabled:opacity-50
                        "
                      >
                        {downloadingId ===
                        analysis.id
                          ? "Downloading..."
                          : "Download PDF"}
                      </button>
                    </div>
                  </div>
                </article>
              ),
            )}
          </div>
        )}
      </section>


      {/* SECURITY INFO */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="font-semibold text-white">
          Secure Tenant Reports
        </h2>

        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Every PDF request is authenticated
          with your FinGuard access token.
          The backend verifies that the
          requested analysis belongs to your
          company before generating the report.
        </p>
      </section>
    </div>
  );
}
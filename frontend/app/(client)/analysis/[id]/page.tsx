"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import Link from "next/link";
import { useParams } from "next/navigation";

import { apiFetch } from "@/lib/api";


interface Finding {
  id: number;
  type: string;
  severity: string;
  title: string;
  message: string;
  amount_at_risk: number;
  transaction_id: string | null;
  created_at: string | null;
}


interface Analysis {
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
  ai_summary: string | null;
  created_at: string | null;
  findings: Finding[];
}


interface AnalysisResponse {
  success: boolean;
  analysis: Analysis;
}


function riskBadgeClass(
  level: string,
): string {
  const value =
    level.toUpperCase();

  if (value === "HIGH") {
    return "border-red-900 bg-red-950/40 text-red-300";
  }

  if (value === "MEDIUM") {
    return "border-amber-900 bg-amber-950/40 text-amber-300";
  }

  return "border-emerald-900 bg-emerald-950/40 text-emerald-300";
}


function severityBadgeClass(
  severity: string,
): string {
  const value =
    severity.toUpperCase();

  if (value === "HIGH") {
    return "border-red-900 bg-red-950/40 text-red-300";
  }

  if (value === "MEDIUM") {
    return "border-amber-900 bg-amber-950/40 text-amber-300";
  }

  return "border-slate-700 bg-slate-800 text-slate-300";
}


export default function AnalysisDetailsPage() {
  const params = useParams();

  const analysisId =
    Number(params.id);

  const [
    analysis,
    setAnalysis,
  ] =
    useState<Analysis | null>(
      null,
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  useEffect(() => {
    let active = true;

    async function loadAnalysis() {
      if (
        !Number.isFinite(
          analysisId,
        ) ||
        analysisId <= 0
      ) {
        setError(
          "Invalid analysis ID.",
        );

        setLoading(false);

        return;
      }

      try {
        setLoading(true);
        setError(null);

        const response =
          await apiFetch<AnalysisResponse>(
            `/api/v1/history/${analysisId}`,
          );

        if (!active) {
          return;
        }

        setAnalysis(
          response.analysis,
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
            "Unable to load analysis.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadAnalysis();

    return () => {
      active = false;
    };
  }, [analysisId]);


  const totalFindingsAmount =
    useMemo(() => {
      if (!analysis) {
        return 0;
      }

      return analysis.findings.reduce(
        (
          total,
          finding,
        ) =>
          total +
          (
            finding.amount_at_risk ??
            0
          ),
        0,
      );
    }, [analysis]);


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


  if (loading) {
    return (
      <div>
        <h1 className="text-3xl font-bold text-white">
          Analysis Results
        </h1>

        <p className="mt-3 text-slate-400">
          Loading analysis...
        </p>
      </div>
    );
  }


  if (
    error ||
    !analysis
  ) {
    return (
      <div className="space-y-6">
        <div className="rounded-2xl border border-red-900/60 bg-red-950/20 p-6">
          <h1 className="text-xl font-semibold text-red-300">
            Unable to load analysis
          </h1>

          <p className="mt-2 text-sm text-red-300">
            {error ??
              "Analysis not found."}
          </p>
        </div>

        <Link
          href="/history"
          className="inline-flex rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800"
        >
          Back to History
        </Link>
      </div>
    );
  }


  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-sm font-medium text-blue-400">
            Analysis #{analysis.id}
          </p>

          <h1 className="mt-1 text-3xl font-bold text-white">
            Analysis Results
          </h1>

          <p className="mt-2 text-slate-400">
            {analysis.filename}
          </p>

          <p className="mt-1 text-sm text-slate-500">
            {formatDate(
              analysis.created_at,
            )}
          </p>
        </div>


        <div className="flex flex-wrap gap-3">
          <Link
            href="/analysis"
            className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"
          >
            New Analysis
          </Link>

          <Link
            href="/history"
            className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800"
          >
            History
          </Link>
        </div>
      </div>


      {/* MAIN KPI */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <p className="text-sm text-slate-400">
            Risk Score
          </p>

          <p className="mt-2 text-4xl font-bold text-white">
            {analysis.risk_score.toFixed(
              2,
            )}
          </p>

          <span
            className={`
              mt-4
              inline-flex
              rounded-full
              border
              px-3
              py-1
              text-xs
              font-semibold
              ${riskBadgeClass(
                analysis.risk_level,
              )}
            `}
          >
            {analysis.risk_level}
          </span>
        </div>


        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <p className="text-sm text-slate-400">
            Money At Risk
          </p>

          <p className="mt-2 text-2xl font-bold text-white">
            {formatMoney(
              analysis.money_at_risk,
            )}
          </p>
        </div>


        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <p className="text-sm text-slate-400">
            Total Findings
          </p>

          <p className="mt-2 text-4xl font-bold text-white">
            {analysis.total_findings}
          </p>
        </div>


        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <p className="text-sm text-slate-400">
            Dataset
          </p>

          <p className="mt-2 text-xl font-semibold text-white">
            {analysis.rows.toLocaleString()}
          </p>

          <p className="mt-1 text-sm text-slate-500">
            rows · {analysis.columns} columns
          </p>
        </div>
      </div>


      {/* RISK BREAKDOWN */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-xl font-semibold text-white">
          Risk Breakdown
        </h2>

        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-5">
            <p className="text-sm text-red-300">
              High Risk
            </p>

            <p className="mt-2 text-3xl font-bold text-white">
              {analysis.high_risk}
            </p>
          </div>


          <div className="rounded-xl border border-amber-900/50 bg-amber-950/20 p-5">
            <p className="text-sm text-amber-300">
              Medium Risk
            </p>

            <p className="mt-2 text-3xl font-bold text-white">
              {analysis.medium_risk}
            </p>
          </div>


          <div className="rounded-xl border border-slate-700 bg-slate-950/40 p-5">
            <p className="text-sm text-slate-300">
              Low Risk
            </p>

            <p className="mt-2 text-3xl font-bold text-white">
              {analysis.low_risk}
            </p>
          </div>
        </div>
      </section>


      {/* AI SUMMARY */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="text-xl font-semibold text-white">
          AI Executive Summary
        </h2>

        {analysis.ai_summary ? (
          <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-300">
            {analysis.ai_summary}
          </p>
        ) : (
          <p className="mt-4 text-sm text-slate-500">
            No AI summary available.
          </p>
        )}
      </section>


      {/* FINDINGS */}
      <section>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white">
              Findings
            </h2>

            <p className="mt-1 text-sm text-slate-400">
              Detected financial risks and suspicious activity.
            </p>
          </div>

          <p className="text-sm text-slate-400">
            Findings exposure:{" "}
            <span className="font-semibold text-white">
              {formatMoney(
                totalFindingsAmount,
              )}
            </span>
          </p>
        </div>


        <div className="mt-5 space-y-4">
          {analysis.findings.length === 0 ? (
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center">
              <p className="text-slate-400">
                No financial findings were detected.
              </p>
            </div>
          ) : (
            analysis.findings.map(
              (finding) => (
                <article
                  key={finding.id}
                  className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
                >
                  <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
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
                            ${severityBadgeClass(
                              finding.severity,
                            )}
                          `}
                        >
                          {finding.severity}
                        </span>

                        <span className="text-xs text-slate-500">
                          {finding.type}
                        </span>
                      </div>


                      <h3 className="mt-4 text-base font-semibold text-white">
                        {finding.title}
                      </h3>

                      <p className="mt-2 text-sm leading-6 text-slate-400">
                        {finding.message}
                      </p>


                      <div className="mt-5 grid gap-4 sm:grid-cols-3">
                        <div>
                          <p className="text-xs uppercase tracking-wide text-slate-500">
                            Transaction
                          </p>

                          <p className="mt-1 break-all text-sm text-slate-300">
                            {finding.transaction_id ??
                              "N/A"}
                          </p>
                        </div>


                        <div>
                          <p className="text-xs uppercase tracking-wide text-slate-500">
                            Amount At Risk
                          </p>

                          <p className="mt-1 text-sm font-medium text-white">
                            {formatMoney(
                              finding.amount_at_risk,
                            )}
                          </p>
                        </div>


                        <div>
                          <p className="text-xs uppercase tracking-wide text-slate-500">
                            Created
                          </p>

                          <p className="mt-1 text-sm text-slate-300">
                            {formatDate(
                              finding.created_at,
                            )}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </article>
              ),
            )
          )}
        </div>
      </section>


      {/* BOTTOM ACTIONS */}
      <div className="flex flex-wrap gap-3 border-t border-slate-800 pt-6">
        <Link
          href="/analysis"
          className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-500"
        >
          Run New Analysis
        </Link>

        <Link
          href="/history"
          className="rounded-xl border border-slate-700 px-5 py-3 text-sm font-medium text-slate-300 hover:bg-slate-800"
        >
          Back to History
        </Link>
      </div>
    </div>
  );
}
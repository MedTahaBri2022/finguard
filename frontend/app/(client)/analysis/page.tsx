"use client";

import {
  ChangeEvent,
  DragEvent,
  useRef,
  useState,
} from "react";

import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";


interface AnalysisResponse {
  analysis_id: number;
  risk_score?: number;
  risk_level?: string;
  total_findings?: number;
  high_risk?: number;
  medium_risk?: number;
  low_risk?: number;
  money_at_risk?: number;
}


const ALLOWED_EXTENSIONS = [
  ".csv",
  ".xlsx",
  ".xls",
];


export default function AnalysisPage() {
  const router = useRouter();

  const inputRef =
    useRef<HTMLInputElement | null>(null);

  const [file, setFile] =
    useState<File | null>(null);

  const [dragActive, setDragActive] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");


  function validateFile(
    selectedFile: File,
  ): string | null {
    const fileName =
      selectedFile.name.toLowerCase();

    const validExtension =
      ALLOWED_EXTENSIONS.some(
        (extension) =>
          fileName.endsWith(extension),
      );

    if (!validExtension) {
      return (
        "Unsupported file format. " +
        "Please upload CSV, XLSX or XLS."
      );
    }

    if (selectedFile.size === 0) {
      return "The selected file is empty.";
    }

    return null;
  }


  function selectFile(
    selectedFile: File,
  ) {
    const validationError =
      validateFile(selectedFile);

    if (validationError) {
      setFile(null);
      setSuccess("");
      setError(validationError);
      return;
    }

    setFile(selectedFile);
    setError("");
    setSuccess("");
  }


  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const selectedFile =
      event.target.files?.[0];

    if (!selectedFile) {
      return;
    }

    selectFile(selectedFile);
  }


  function handleDragOver(
    event: DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();

    if (!loading) {
      setDragActive(true);
    }
  }


  function handleDragLeave(
    event: DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();
    setDragActive(false);
  }


  function handleDrop(
    event: DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();
    setDragActive(false);

    if (loading) {
      return;
    }

    const selectedFile =
      event.dataTransfer.files?.[0];

    if (!selectedFile) {
      return;
    }

    selectFile(selectedFile);
  }


  function handleBrowse() {
    if (loading) {
      return;
    }

    inputRef.current?.click();
  }


  function removeFile() {
    if (loading) {
      return;
    }

    setFile(null);
    setError("");
    setSuccess("");

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }


  function formatFileSize(
    bytes: number,
  ): string {
    if (bytes < 1024) {
      return `${bytes} B`;
    }

    const kb = bytes / 1024;

    if (kb < 1024) {
      return `${kb.toFixed(1)} KB`;
    }

    const mb = kb / 1024;

    return `${mb.toFixed(1)} MB`;
  }


  async function handleAnalyze() {
    if (!file) {
      setError(
        "Please select a CSV or Excel file.",
      );
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const formData =
        new FormData();

      /*
       * IMPORTANT:
       *
       * We send ONLY the file.
       *
       * No client_profile_id.
       * No client_id.
       * No tenant_id.
       *
       * The backend determines the company
       * from the authenticated JWT user.
       */
      formData.append(
        "file",
        file,
      );

      /*
       * apiFetch automatically adds:
       *
       * Authorization: Bearer <JWT>
       *
       * Do NOT replace this with a direct
       * fetch() call.
       */
      const data =
        await apiFetch<AnalysisResponse>(
          "/api/v1/analysis/analyze",
          {
            method: "POST",
            body: formData,
          },
        );

      if (!data.analysis_id) {
        throw new Error(
          "Analysis completed but no analysis ID was returned.",
        );
      }

      setSuccess(
        "Analysis completed successfully.",
      );

      router.push(
        `/analysis/${data.analysis_id}`,
      );
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(
          "An unexpected error occurred while analyzing the file.",
        );
      }
    } finally {
      setLoading(false);
    }
  }


  return (
    <div className="space-y-8">
      {/* Header */}
      <section>
        <p className="text-sm font-medium text-blue-400">
          FinGuard Financial Intelligence
        </p>

        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
          New Analysis
        </h1>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
          Upload a financial dataset to detect
          potential financial risks, anomalies,
          suspicious transactions and business
          losses.
        </p>
      </section>


      {/* Upload Card */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6 md:p-8">
        <div>
          <h2 className="text-xl font-semibold text-white">
            Upload Dataset
          </h2>

          <p className="mt-2 text-sm text-slate-400">
            Supported formats: CSV, XLSX, XLS
          </p>
        </div>


        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileChange}
          disabled={loading}
          className="hidden"
        />


        <div
          role="button"
          tabIndex={0}
          onClick={handleBrowse}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onKeyDown={(event) => {
            if (
              event.key === "Enter" ||
              event.key === " "
            ) {
              handleBrowse();
            }
          }}
          className={`
            mt-8
            flex
            min-h-[240px]
            cursor-pointer
            flex-col
            items-center
            justify-center
            rounded-2xl
            border-2
            border-dashed
            px-6
            text-center
            transition
            ${
              dragActive
                ? "border-blue-500 bg-blue-950/30"
                : "border-slate-700 bg-slate-950/40 hover:border-slate-600"
            }
            ${
              loading
                ? "cursor-not-allowed opacity-60"
                : ""
            }
          `}
        >
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-800 text-3xl">
            📊
          </div>


          {file ? (
            <>
              <p className="mt-5 max-w-full truncate text-base font-semibold text-white">
                {file.name}
              </p>

              <p className="mt-2 text-sm text-blue-400">
                Click here to browse files
              </p>

              <p className="mt-3 text-xs text-slate-500">
                {formatFileSize(
                  file.size,
                )}
              </p>
            </>
          ) : (
            <>
              <p className="mt-5 text-base font-semibold text-white">
                Choose your financial dataset
              </p>

              <p className="mt-2 text-sm text-slate-400">
                Click here to browse files
              </p>

              <p className="mt-3 text-xs text-slate-500">
                or drag and drop your file here
              </p>
            </>
          )}
        </div>


        {/* Selected file */}
        {file && (
          <div className="mt-5 flex flex-col gap-4 rounded-xl border border-slate-800 bg-slate-950/60 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Selected Dataset
              </p>

              <p className="mt-1 truncate text-sm font-medium text-white">
                {file.name}
              </p>

              <p className="mt-1 text-xs text-slate-500">
                {formatFileSize(
                  file.size,
                )}
              </p>
            </div>

            <button
              type="button"
              onClick={removeFile}
              disabled={loading}
              className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Remove
            </button>
          </div>
        )}


        {/* Error */}
        {error && (
          <div className="mt-6 rounded-xl border border-red-900/70 bg-red-950/30 p-5">
            <p className="font-semibold text-red-400">
              Analysis Error
            </p>

            <p className="mt-2 text-sm text-red-300">
              {error}
            </p>
          </div>
        )}


        {/* Success */}
        {success && (
          <div className="mt-6 rounded-xl border border-emerald-900/70 bg-emerald-950/30 p-5">
            <p className="font-semibold text-emerald-400">
              Analysis Complete
            </p>

            <p className="mt-2 text-sm text-emerald-300">
              {success}
            </p>
          </div>
        )}


        {/* Analyze button */}
        <button
          type="button"
          onClick={handleAnalyze}
          disabled={!file || loading}
          className="
            mt-6
            flex
            w-full
            items-center
            justify-center
            rounded-xl
            bg-blue-600
            px-6
            py-4
            text-base
            font-semibold
            text-white
            transition
            hover:bg-blue-500
            disabled:cursor-not-allowed
            disabled:bg-slate-700
            disabled:text-slate-400
          "
        >
          {loading
            ? "Analyzing..."
            : "Start Analysis"}
        </button>
      </section>


      {/* Features */}
      <section className="grid gap-5 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h3 className="text-lg font-semibold text-white">
            Risk Detection
          </h3>

          <p className="mt-3 text-sm leading-6 text-slate-400">
            Detect unusual and potentially risky
            financial transactions.
          </p>
        </div>


        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h3 className="text-lg font-semibold text-white">
            AI Intelligence
          </h3>

          <p className="mt-3 text-sm leading-6 text-slate-400">
            Generate an AI-powered executive
            summary of detected risks.
          </p>
        </div>


        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h3 className="text-lg font-semibold text-white">
            Financial Impact
          </h3>

          <p className="mt-3 text-sm leading-6 text-slate-400">
            Estimate the amount of money
            potentially exposed to risk.
          </p>
        </div>
      </section>


      {/* Security */}
      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <div className="flex gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-950 text-blue-400">
            🔒
          </div>

          <div>
            <h3 className="font-semibold text-white">
              Secure Client Analysis
            </h3>

            <p className="mt-2 text-sm leading-6 text-slate-400">
              Your analysis is automatically
              associated with your authenticated
              company workspace. FinGuard does
              not accept a client identifier from
              this upload page.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
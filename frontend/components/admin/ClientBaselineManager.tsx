"use client";

import {
  ChangeEvent,
  DragEvent,
  useRef,
  useState,
} from "react";

import {
  API_BASE_URL,
} from "@/lib/api";

import {
  getAccessToken,
} from "@/lib/auth";


interface ClientBaselineManagerProps {
  clientId: string;
  clientName: string;
  baselineReady: boolean;
  minimumHistoryRows: number;

  onBaselineCreated?: (
    result: BaselineResponse,
  ) => void;
}


interface BaselineResponse {
  message: string;

  client: {
    id: number;
    name: string;
    baseline_ready: boolean;
    minimum_history_rows: number;
  };

  baseline: {
    id: number;
    version: number;
    sample_size: number;
    is_active: boolean;
    created_at: string;
  };

  schema: {
    mapping_mode: string;
    mapping:
      Record<string, string>;
    warnings: unknown[];
  };

  data_cleaning: {
    original_rows:
      | number
      | null;

    cleaned_rows:
      | number
      | null;

    removed_rows:
      | number
      | null;

    normalization_coverage:
      | number
      | null;

    currency_conflicts:
      | number
      | null;

    unknown_currency_rows:
      | number
      | null;

    fx_unavailable_rows:
      | number
      | null;

    missing_fx_date_rows:
      | number
      | null;
  };

  readiness:
    Record<string, unknown>;

  statistics: {
    amount:
      | Record<string, unknown>
      | null;

    operational:
      | Record<string, unknown>
      | null;

    category_count: number;
    entity_count: number;
    transaction_type_count: number;
  };
}


function formatPercentage(
  value:
    | number
    | null,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "N/A";
  }

  return `${(
    value * 100
  ).toFixed(2)}%`;
}


export default function ClientBaselineManager({
  clientId,
  clientName,
  baselineReady,
  minimumHistoryRows,
  onBaselineCreated,
}: ClientBaselineManagerProps) {
  const inputRef =
    useRef<HTMLInputElement | null>(
      null,
    );


  const [
    file,
    setFile,
  ] =
    useState<File | null>(
      null,
    );


  const [
    dragging,
    setDragging,
  ] =
    useState(false);


  const [
    uploading,
    setUploading,
  ] =
    useState(false);


  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  const [
    result,
    setResult,
  ] =
    useState<BaselineResponse | null>(
      null,
    );


  function validateFile(
    selectedFile: File,
  ): boolean {
    const name =
      selectedFile.name
        .toLowerCase();

    const valid =
      name.endsWith(".csv") ||
      name.endsWith(".xlsx") ||
      name.endsWith(".xls");

    if (!valid) {
      setError(
        "Only CSV, XLSX and XLS files are supported.",
      );

      return false;
    }

    return true;
  }


  function selectFile(
    selectedFile: File,
  ) {
    if (
      !validateFile(
        selectedFile,
      )
    ) {
      setFile(null);
      return;
    }

    setFile(
      selectedFile,
    );

    setError(null);
    setResult(null);
  }


  function handleFileInput(
    event:
      ChangeEvent<HTMLInputElement>,
  ) {
    const selectedFile =
      event.target.files?.[0];

    if (!selectedFile) {
      return;
    }

    selectFile(
      selectedFile,
    );
  }


  function handleDragOver(
    event:
      DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();

    setDragging(true);
  }


  function handleDragLeave(
    event:
      DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();

    setDragging(false);
  }


  function handleDrop(
    event:
      DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();

    setDragging(false);

    const selectedFile =
      event.dataTransfer
        .files?.[0];

    if (!selectedFile) {
      return;
    }

    selectFile(
      selectedFile,
    );
  }


  async function buildBaseline() {
    if (!file) {
      setError(
        "Select a historical CSV or Excel file first.",
      );

      return;
    }


    const token =
      getAccessToken();

    if (!token) {
      setError(
        "Authentication token is missing.",
      );

      return;
    }


    try {
      setUploading(true);
      setError(null);
      setResult(null);


      const formData =
        new FormData();

      formData.append(
        "file",
        file,
      );


      const response =
        await fetch(
          `${API_BASE_URL}/api/v1/clients/${clientId}/baseline`,
          {
            method: "POST",

            headers: {
              Authorization:
                `Bearer ${token}`,
            },

            body:
              formData,
          },
        );


      let data:
        | BaselineResponse
        | {
            detail?: unknown;
          }
        | null = null;


      try {
        data =
          await response.json();
      } catch {
        data = null;
      }


      if (!response.ok) {
        let message =
          "Unable to build client baseline.";


        if (
          data &&
          typeof data ===
            "object" &&
          "detail" in data
        ) {
          const detail =
            data.detail;


          if (
            typeof detail ===
              "string"
          ) {
            message =
              detail;
          } else if (
            detail &&
            typeof detail ===
              "object"
          ) {
            message =
              JSON.stringify(
                detail,
              );
          }
        }


        throw new Error(
          message,
        );
      }


      const baselineResult =
        data as BaselineResponse;


      setResult(
        baselineResult,
      );


      onBaselineCreated?.(
        baselineResult,
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
          "Unable to build client baseline.",
        );
      }
    } finally {
      setUploading(false);
    }
  }


  return (
    <section
      className="
        rounded-2xl
        border
        border-slate-800
        bg-slate-900
        p-6
      "
    >
      <div
        className="
          flex
          flex-col
          gap-5
          lg:flex-row
          lg:items-start
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
            Data Onboarding
          </p>

          <h2
            className="
              mt-1
              text-xl
              font-semibold
              text-white
            "
          >
            Historical Baseline
          </h2>

          <p
            className="
              mt-2
              max-w-3xl
              text-sm
              leading-6
              text-slate-400
            "
          >
            Upload historical
            transaction data for
            {` ${clientName} `}
            so FinGuard can learn
            the company&apos;s normal
            financial behavior.
          </p>
        </div>


        <span
          className={`
            w-fit
            rounded-full
            border
            px-3
            py-1.5
            text-xs
            font-semibold
            ${
              baselineReady
                ? `
                  border-emerald-900
                  bg-emerald-950/40
                  text-emerald-300
                `
                : `
                  border-amber-900
                  bg-amber-950/40
                  text-amber-300
                `
            }
          `}
        >
          {baselineReady
            ? "Baseline Ready"
            : "Baseline Not Ready"}
        </span>
      </div>


      <div
        className="
          mt-6
          rounded-xl
          border
          border-blue-900/50
          bg-blue-950/10
          p-4
        "
      >
        <p
          className="
            text-sm
            text-slate-400
          "
        >
          Minimum recommended
          historical rows:
          {" "}

          <span
            className="
              font-semibold
              text-white
            "
          >
            {minimumHistoryRows}
          </span>
        </p>

        <p
          className="
            mt-2
            text-xs
            text-slate-500
          "
        >
          The uploaded file should
          follow the client&apos;s
          configured Schema Mapping.
        </p>
      </div>


      {error && (
        <div
          className="
            mt-5
            rounded-xl
            border
            border-red-900/60
            bg-red-950/20
            p-4
            text-sm
            text-red-300
          "
        >
          {error}
        </div>
      )}


      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xlsx,.xls"
        onChange={
          handleFileInput
        }
        className="hidden"
      />


      <div
        onDragOver={
          handleDragOver
        }
        onDragLeave={
          handleDragLeave
        }
        onDrop={
          handleDrop
        }
        onClick={() => {
          if (!uploading) {
            inputRef
              .current
              ?.click();
          }
        }}
        className={`
          mt-6
          cursor-pointer
          rounded-2xl
          border-2
          border-dashed
          p-8
          text-center
          transition
          ${
            dragging
              ? `
                border-purple-500
                bg-purple-950/20
              `
              : `
                border-slate-700
                bg-slate-950/40
                hover:border-slate-600
              `
          }
        `}
      >
        <p
          className="
            font-medium
            text-white
          "
        >
          {file
            ? file.name
            : "Drop historical dataset here"}
        </p>


        <p
          className="
            mt-2
            text-sm
            text-slate-500
          "
        >
          {file
            ? `${(
                file.size /
                1024 /
                1024
              ).toFixed(2)} MB`
            : "CSV, XLSX or XLS"}
        </p>


        <p
          className="
            mt-3
            text-xs
            text-purple-400
          "
        >
          Click to browse
        </p>
      </div>


      <div
        className="
          mt-5
          flex
          justify-end
        "
      >
        <button
          type="button"
          onClick={() => {
            void buildBaseline();
          }}
          disabled={
            uploading ||
            !file
          }
          className="
            rounded-xl
            bg-purple-600
            px-5
            py-3
            text-sm
            font-semibold
            text-white
            transition
            hover:bg-purple-500
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >
          {uploading
            ? "Building Baseline..."
            : baselineReady
              ? "Build New Baseline Version"
              : "Build Historical Baseline"}
        </button>
      </div>


      {result && (
        <div
          className="
            mt-8
            space-y-6
            border-t
            border-slate-800
            pt-6
          "
        >
          <div
            className="
              rounded-xl
              border
              border-emerald-900/60
              bg-emerald-950/20
              p-4
            "
          >
            <p
              className="
                font-semibold
                text-emerald-300
              "
            >
              {result.message}
            </p>

            <p
              className="
                mt-1
                text-sm
                text-slate-400
              "
            >
              Baseline version{" "}
              {result.baseline.version}
              {" "}created successfully.
            </p>
          </div>


          <div
            className="
              grid
              gap-4
              sm:grid-cols-2
              xl:grid-cols-4
            "
          >
            <div
              className="
                rounded-xl
                border
                border-slate-800
                bg-slate-950/50
                p-4
              "
            >
              <p
                className="
                  text-xs
                  uppercase
                  text-slate-500
                "
              >
                Version
              </p>

              <p
                className="
                  mt-2
                  text-2xl
                  font-bold
                  text-white
                "
              >
                {result.baseline.version}
              </p>
            </div>


            <div
              className="
                rounded-xl
                border
                border-slate-800
                bg-slate-950/50
                p-4
              "
            >
              <p
                className="
                  text-xs
                  uppercase
                  text-slate-500
                "
              >
                Sample Size
              </p>

              <p
                className="
                  mt-2
                  text-2xl
                  font-bold
                  text-white
                "
              >
                {result.baseline.sample_size}
              </p>
            </div>


            <div
              className="
                rounded-xl
                border
                border-slate-800
                bg-slate-950/50
                p-4
              "
            >
              <p
                className="
                  text-xs
                  uppercase
                  text-slate-500
                "
              >
                Mapping Mode
              </p>

              <p
                className="
                  mt-2
                  text-sm
                  font-semibold
                  text-purple-300
                "
              >
                {result.schema.mapping_mode}
              </p>
            </div>


            <div
              className="
                rounded-xl
                border
                border-slate-800
                bg-slate-950/50
                p-4
              "
            >
              <p
                className="
                  text-xs
                  uppercase
                  text-slate-500
                "
              >
                Readiness
              </p>

              <p
                className={`
                  mt-2
                  text-sm
                  font-semibold
                  ${
                    result.client
                      .baseline_ready
                      ? "text-emerald-300"
                      : "text-amber-300"
                  }
                `}
              >
                {result.client
                  .baseline_ready
                  ? "Ready"
                  : "Not Ready"}
              </p>
            </div>
          </div>


          <div
            className="
              rounded-xl
              border
              border-slate-800
              bg-slate-950/40
              p-5
            "
          >
            <h3
              className="
                font-semibold
                text-white
              "
            >
              Data Cleaning
            </h3>


            <div
              className="
                mt-5
                grid
                gap-4
                sm:grid-cols-2
                lg:grid-cols-4
              "
            >
              <div>
                <p
                  className="
                    text-xs
                    text-slate-500
                  "
                >
                  Original Rows
                </p>

                <p
                  className="
                    mt-1
                    text-sm
                    font-medium
                    text-white
                  "
                >
                  {result.data_cleaning
                    .original_rows ??
                    "N/A"}
                </p>
              </div>


              <div>
                <p
                  className="
                    text-xs
                    text-slate-500
                  "
                >
                  Cleaned Rows
                </p>

                <p
                  className="
                    mt-1
                    text-sm
                    font-medium
                    text-white
                  "
                >
                  {result.data_cleaning
                    .cleaned_rows ??
                    "N/A"}
                </p>
              </div>


              <div>
                <p
                  className="
                    text-xs
                    text-slate-500
                  "
                >
                  Removed Rows
                </p>

                <p
                  className="
                    mt-1
                    text-sm
                    font-medium
                    text-white
                  "
                >
                  {result.data_cleaning
                    .removed_rows ??
                    "N/A"}
                </p>
              </div>


              <div>
                <p
                  className="
                    text-xs
                    text-slate-500
                  "
                >
                  Normalization
                </p>

                <p
                  className="
                    mt-1
                    text-sm
                    font-medium
                    text-white
                  "
                >
                  {formatPercentage(
                    result
                      .data_cleaning
                      .normalization_coverage,
                  )}
                </p>
              </div>
            </div>
          </div>


          <div
            className="
              rounded-xl
              border
              border-slate-800
              bg-slate-950/40
              p-5
            "
          >
            <h3
              className="
                font-semibold
                text-white
              "
            >
              Learned Context
            </h3>


            <div
              className="
                mt-5
                grid
                gap-4
                sm:grid-cols-3
              "
            >
              <div>
                <p
                  className="
                    text-xs
                    text-slate-500
                  "
                >
                  Categories
                </p>

                <p
                  className="
                    mt-1
                    text-2xl
                    font-bold
                    text-white
                  "
                >
                  {result.statistics
                    .category_count}
                </p>
              </div>


              <div>
                <p
                  className="
                    text-xs
                    text-slate-500
                  "
                >
                  Entities
                </p>

                <p
                  className="
                    mt-1
                    text-2xl
                    font-bold
                    text-white
                  "
                >
                  {result.statistics
                    .entity_count}
                </p>
              </div>


              <div>
                <p
                  className="
                    text-xs
                    text-slate-500
                  "
                >
                  Transaction Types
                </p>

                <p
                  className="
                    mt-1
                    text-2xl
                    font-bold
                    text-white
                  "
                >
                  {result.statistics
                    .transaction_type_count}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
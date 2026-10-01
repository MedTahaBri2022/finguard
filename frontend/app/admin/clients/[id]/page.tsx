"use client";

import {
  FormEvent,
  useCallback,
  useEffect,
  useState,
} from "react";

import Link from "next/link";

import {
  useParams,
} from "next/navigation";

import {
  apiFetch,
} from "@/lib/api";

import ClientSchemaMapping
  from "@/components/admin/ClientSchemaMapping";

import ClientBaselineManager
  from "@/components/admin/ClientBaselineManager";

import ClientUsersManager 
  from "@/components/admin/ClientUsersManager";


interface ClientProfile {
  id: number;
  name: string;

  business_type:
    | string
    | null;

  base_currency: string;

  risk_tolerance: string;

  column_mapping:
    | Record<string, string>
    | null;

  business_rules?:
    | Record<string, unknown>
    | null;

  failure_rate_warning:
    | number
    | null;

  refund_rate_warning:
    | number
    | null;

  high_amount_multiplier:
    | number
    | null;

  baseline_ready: boolean;

  minimum_history_rows: number;

  is_active: boolean;

  analysis_count?: number;

  baseline_count?: number;

  created_at?:
    | string
    | null;

  updated_at?:
    | string
    | null;
}


interface UpdateClientResponse {
  message: string;

  client: ClientProfile;
}


interface ClientForm {
  name: string;

  business_type: string;

  base_currency: string;

  risk_tolerance: string;

  failure_rate_warning: string;

  refund_rate_warning: string;

  high_amount_multiplier: string;

  minimum_history_rows: string;
}


function numberToInput(
  value:
    | number
    | null
    | undefined,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "";
  }

  return String(value);
}


function parseOptionalNumber(
  value: string,
): number | null {
  const cleaned =
    value.trim();

  if (!cleaned) {
    return null;
  }

  const parsed =
    Number(cleaned);

  if (
    !Number.isFinite(
      parsed,
    )
  ) {
    return null;
  }

  return parsed;
}


function formatDate(
  value:
    | string
    | null
    | undefined,
): string {
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


export default function ManageClientPage() {
  const params =
    useParams();


  const clientId =
    Array.isArray(
      params.id,
    )
      ? params.id[0]
      : String(
          params.id ?? "",
        );


  const [
    client,
    setClient,
  ] =
    useState<ClientProfile | null>(
      null,
    );


  const [
    form,
    setForm,
  ] =
    useState<ClientForm | null>(
      null,
    );


  const [
    loading,
    setLoading,
  ] =
    useState(true);


  const [
    saving,
    setSaving,
  ] =
    useState(false);


  const [
    changingStatus,
    setChangingStatus,
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
    success,
    setSuccess,
  ] =
    useState<string | null>(
      null,
    );


  const populateForm =
    useCallback(
      (
        data:
          ClientProfile,
      ) => {
        setForm({
          name:
            data.name ?? "",

          business_type:
            data.business_type ??
            "",

          base_currency:
            data.base_currency ??
            "MAD",

          risk_tolerance:
            data.risk_tolerance ??
            "conservative",

          failure_rate_warning:
            numberToInput(
              data.failure_rate_warning,
            ),

          refund_rate_warning:
            numberToInput(
              data.refund_rate_warning,
            ),

          high_amount_multiplier:
            numberToInput(
              data.high_amount_multiplier,
            ),

          minimum_history_rows:
            String(
              data.minimum_history_rows ??
                100,
            ),
        });
      },
      [],
    );


  const loadClient =
    useCallback(
      async (
        showLoader:
          boolean = true,
      ) => {
        if (!clientId) {
          setError(
            "Invalid client ID.",
          );

          setLoading(
            false,
          );

          return;
        }


        try {
          if (showLoader) {
            setLoading(
              true,
            );
          }

          setError(
            null,
          );


          const data =
            await apiFetch<ClientProfile>(
              `/api/v1/clients/${clientId}`,
            );


          setClient(
            data,
          );

          populateForm(
            data,
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
              "Unable to load client.",
            );
          }
        } finally {
          if (showLoader) {
            setLoading(
              false,
            );
          }
        }
      },
      [
        clientId,
        populateForm,
      ],
    );


  useEffect(() => {
    void loadClient();
  }, [loadClient]);


  function updateForm(
    field:
      keyof ClientForm,

    value:
      string,
  ) {
    setForm(
      (current) => {
        if (!current) {
          return current;
        }

        return {
          ...current,

          [field]:
            value,
        };
      },
    );


    setError(
      null,
    );

    setSuccess(
      null,
    );
  }


  async function handleSave(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();


    if (!form) {
      return;
    }


    const name =
      form.name
        .trim();


    const businessType =
      form.business_type
        .trim();


    const currency =
      form.base_currency
        .trim()
        .toUpperCase();


    const minimumRows =
      Number(
        form.minimum_history_rows,
      );


    const failureWarning =
      parseOptionalNumber(
        form.failure_rate_warning,
      );


    const refundWarning =
      parseOptionalNumber(
        form.refund_rate_warning,
      );


    const amountMultiplier =
      parseOptionalNumber(
        form.high_amount_multiplier,
      );


    if (!name) {
      setError(
        "Company name is required.",
      );

      return;
    }


    if (!currency) {
      setError(
        "Base currency is required.",
      );

      return;
    }


    if (
      !Number.isInteger(
        minimumRows,
      ) ||
      minimumRows <= 0
    ) {
      setError(
        "Minimum history rows must be a positive integer.",
      );

      return;
    }


    if (
      failureWarning !== null &&
      (
        failureWarning < 0 ||
        failureWarning > 1
      )
    ) {
      setError(
        "Failure rate warning must be between 0 and 1.",
      );

      return;
    }


    if (
      refundWarning !== null &&
      (
        refundWarning < 0 ||
        refundWarning > 1
      )
    ) {
      setError(
        "Refund rate warning must be between 0 and 1.",
      );

      return;
    }


    if (
      amountMultiplier !== null &&
      amountMultiplier < 0
    ) {
      setError(
        "High amount multiplier must be positive.",
      );

      return;
    }


    try {
      setSaving(
        true,
      );

      setError(
        null,
      );

      setSuccess(
        null,
      );


      const response =
        await apiFetch<UpdateClientResponse>(
          `/api/v1/clients/${clientId}`,
          {
            method:
              "PATCH",

            body:
              JSON.stringify({
                name,

                business_type:
                  businessType ||
                  null,

                base_currency:
                  currency,

                risk_tolerance:
                  form.risk_tolerance,

                failure_rate_warning:
                  failureWarning,

                refund_rate_warning:
                  refundWarning,

                high_amount_multiplier:
                  amountMultiplier,

                minimum_history_rows:
                  minimumRows,
              }),
          },
        );


      setClient(
        (current) => ({
          ...(current ??
            response.client),

          ...response.client,
        }),
      );


      populateForm(
        response.client,
      );


      setSuccess(
        "Client configuration saved successfully.",
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
          "Unable to update client.",
        );
      }
    } finally {
      setSaving(
        false,
      );
    }
  }


  async function handleStatusChange() {
    if (!client) {
      return;
    }


    const newStatus =
      !client.is_active;


    try {
      setChangingStatus(
        true,
      );

      setError(
        null,
      );

      setSuccess(
        null,
      );


      const response =
        await apiFetch<UpdateClientResponse>(
          `/api/v1/clients/${clientId}`,
          {
            method:
              "PATCH",

            body:
              JSON.stringify({
                is_active:
                  newStatus,
              }),
          },
        );


      setClient(
        (current) => {
          if (!current) {
            return response.client;
          }

          return {
            ...current,

            ...response.client,
          };
        },
      );


      setSuccess(
        newStatus
          ? "Client activated successfully."
          : "Client deactivated successfully.",
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
          "Unable to change client status.",
        );
      }
    } finally {
      setChangingStatus(
        false,
      );
    }
  }


  if (loading) {
    return (
      <div
        className="
          py-12
          text-slate-400
        "
      >
        Loading client...
      </div>
    );
  }


  if (
    !client ||
    !form
  ) {
    return (
      <div
        className="
          space-y-5
        "
      >
        <Link
          href="/admin/clients"
          className="
            text-sm
            font-medium
            text-purple-400
            hover:text-purple-300
          "
        >
          ← Back to Clients
        </Link>


        <div
          className="
            rounded-2xl
            border
            border-red-900/60
            bg-red-950/20
            p-6
            text-red-300
          "
        >
          {error ??
            "Client not found."}
        </div>
      </div>
    );
  }


  return (
    <div
      className="
        space-y-8
      "
    >

      {/* HEADER */}

      <section>
        <Link
          href="/admin/clients"
          className="
            text-sm
            font-medium
            text-purple-400
            transition
            hover:text-purple-300
          "
        >
          ← Back to Clients
        </Link>


        <div
          className="
            mt-5
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
              FinGuard Administration
            </p>


            <h1
              className="
                mt-1
                text-3xl
                font-bold
                text-white
              "
            >
              {client.name}
            </h1>


            <p
              className="
                mt-2
                text-slate-400
              "
            >
              Client #
              {client.id}
              {" · "}
              Configure company,
              risk engine,
              financial schema
              and historical
              baseline.
            </p>
          </div>


          <span
            className={`
              w-fit
              rounded-full
              border
              px-4
              py-2
              text-sm
              font-semibold
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
      </section>


      {/* FEEDBACK */}

      {error && (
        <div
          className="
            rounded-2xl
            border
            border-red-900/60
            bg-red-950/20
            p-5
            text-sm
            text-red-300
          "
        >
          {error}
        </div>
      )}


      {success && (
        <div
          className="
            rounded-2xl
            border
            border-emerald-900/60
            bg-emerald-950/20
            p-5
            text-sm
            text-emerald-300
          "
        >
          {success}
        </div>
      )}


      {/* OVERVIEW */}

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
            p-5
          "
        >
          <p
            className="
              text-sm
              text-slate-400
            "
          >
            Analyses
          </p>

          <p
            className="
              mt-2
              text-3xl
              font-bold
              text-white
            "
          >
            {client.analysis_count ??
              0}
          </p>
        </div>


        <div
          className="
            rounded-2xl
            border
            border-slate-800
            bg-slate-900
            p-5
          "
        >
          <p
            className="
              text-sm
              text-slate-400
            "
          >
            Baselines
          </p>

          <p
            className="
              mt-2
              text-3xl
              font-bold
              text-white
            "
          >
            {client.baseline_count ??
              0}
          </p>
        </div>


        <div
          className="
            rounded-2xl
            border
            border-slate-800
            bg-slate-900
            p-5
          "
        >
          <p
            className="
              text-sm
              text-slate-400
            "
          >
            Baseline Status
          </p>

          <p
            className={`
              mt-2
              text-lg
              font-semibold
              ${
                client.baseline_ready
                  ? "text-emerald-300"
                  : "text-amber-300"
              }
            `}
          >
            {client.baseline_ready
              ? "Ready"
              : "Not Ready"}
          </p>
        </div>


        <div
          className="
            rounded-2xl
            border
            border-slate-800
            bg-slate-900
            p-5
          "
        >
          <p
            className="
              text-sm
              text-slate-400
            "
          >
            Base Currency
          </p>

          <p
            className="
              mt-2
              text-3xl
              font-bold
              text-white
            "
          >
            {client.base_currency}
          </p>
        </div>

      </section>


      {/* CONFIGURATION FORM */}

      <form
        onSubmit={
          handleSave
        }
        className="
          space-y-8
        "
      >

        {/* COMPANY PROFILE */}

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
              text-xl
              font-semibold
              text-white
            "
          >
            Company Profile
          </h2>


          <p
            className="
              mt-1
              text-sm
              text-slate-400
            "
          >
            Core information for
            this FinGuard tenant.
          </p>


          <div
            className="
              mt-6
              grid
              gap-5
              md:grid-cols-2
            "
          >

            <div>
              <label
                className="
                  mb-2
                  block
                  text-sm
                  text-slate-300
                "
              >
                Company Name
              </label>

              <input
                type="text"
                value={
                  form.name
                }
                onChange={(event) => {
                  updateForm(
                    "name",
                    event.target.value,
                  );
                }}
                className="
                  w-full
                  rounded-xl
                  border
                  border-slate-700
                  bg-slate-950
                  px-4
                  py-3
                  text-white
                  outline-none
                  focus:border-purple-500
                "
              />
            </div>


            <div>
              <label
                className="
                  mb-2
                  block
                  text-sm
                  text-slate-300
                "
              >
                Business Type
              </label>

              <input
                type="text"
                value={
                  form.business_type
                }
                onChange={(event) => {
                  updateForm(
                    "business_type",
                    event.target.value,
                  );
                }}
                placeholder="industrial_services"
                className="
                  w-full
                  rounded-xl
                  border
                  border-slate-700
                  bg-slate-950
                  px-4
                  py-3
                  text-white
                  outline-none
                  placeholder:text-slate-600
                  focus:border-purple-500
                "
              />
            </div>


            <div>
              <label
                className="
                  mb-2
                  block
                  text-sm
                  text-slate-300
                "
              >
                Base Currency
              </label>

              <input
                type="text"
                value={
                  form.base_currency
                }
                onChange={(event) => {
                  updateForm(
                    "base_currency",
                    event.target.value,
                  );
                }}
                maxLength={10}
                className="
                  w-full
                  rounded-xl
                  border
                  border-slate-700
                  bg-slate-950
                  px-4
                  py-3
                  uppercase
                  text-white
                  outline-none
                  focus:border-purple-500
                "
              />
            </div>


            <div>
              <label
                className="
                  mb-2
                  block
                  text-sm
                  text-slate-300
                "
              >
                Risk Tolerance
              </label>

              <select
                value={
                  form.risk_tolerance
                }
                onChange={(event) => {
                  updateForm(
                    "risk_tolerance",
                    event.target.value,
                  );
                }}
                className="
                  w-full
                  rounded-xl
                  border
                  border-slate-700
                  bg-slate-950
                  px-4
                  py-3
                  text-white
                  outline-none
                  focus:border-purple-500
                "
              >
                <option
                  value="conservative"
                >
                  Conservative
                </option>

                <option
                  value="balanced"
                >
                  Balanced
                </option>

                <option
                  value="aggressive"
                >
                  Aggressive
                </option>
              </select>
            </div>

          </div>
        </section>


        {/* RISK CONFIGURATION */}

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
              text-xl
              font-semibold
              text-white
            "
          >
            Risk Configuration
          </h2>


          <p
            className="
              mt-1
              text-sm
              text-slate-400
            "
          >
            Financial risk
            parameters configured
            for this organization.
          </p>


          <div
            className="
              mt-6
              grid
              gap-5
              md:grid-cols-2
              xl:grid-cols-4
            "
          >

            <div>
              <label
                className="
                  mb-2
                  block
                  text-sm
                  text-slate-300
                "
              >
                Failure Rate Warning
              </label>

              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={
                  form.failure_rate_warning
                }
                onChange={(event) => {
                  updateForm(
                    "failure_rate_warning",
                    event.target.value,
                  );
                }}
                className="
                  w-full
                  rounded-xl
                  border
                  border-slate-700
                  bg-slate-950
                  px-4
                  py-3
                  text-white
                  outline-none
                  focus:border-purple-500
                "
              />

              <p
                className="
                  mt-2
                  text-xs
                  text-slate-500
                "
              >
                0.05 = 5%
              </p>
            </div>


            <div>
              <label
                className="
                  mb-2
                  block
                  text-sm
                  text-slate-300
                "
              >
                Refund Rate Warning
              </label>

              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={
                  form.refund_rate_warning
                }
                onChange={(event) => {
                  updateForm(
                    "refund_rate_warning",
                    event.target.value,
                  );
                }}
                className="
                  w-full
                  rounded-xl
                  border
                  border-slate-700
                  bg-slate-950
                  px-4
                  py-3
                  text-white
                  outline-none
                  focus:border-purple-500
                "
              />

              <p
                className="
                  mt-2
                  text-xs
                  text-slate-500
                "
              >
                0.08 = 8%
              </p>
            </div>


            <div>
              <label
                className="
                  mb-2
                  block
                  text-sm
                  text-slate-300
                "
              >
                High Amount Multiplier
              </label>

              <input
                type="number"
                min="0"
                step="0.1"
                value={
                  form.high_amount_multiplier
                }
                onChange={(event) => {
                  updateForm(
                    "high_amount_multiplier",
                    event.target.value,
                  );
                }}
                className="
                  w-full
                  rounded-xl
                  border
                  border-slate-700
                  bg-slate-950
                  px-4
                  py-3
                  text-white
                  outline-none
                  focus:border-purple-500
                "
              />
            </div>


            <div>
              <label
                className="
                  mb-2
                  block
                  text-sm
                  text-slate-300
                "
              >
                Minimum History Rows
              </label>

              <input
                type="number"
                min="1"
                step="1"
                value={
                  form.minimum_history_rows
                }
                onChange={(event) => {
                  updateForm(
                    "minimum_history_rows",
                    event.target.value,
                  );
                }}
                className="
                  w-full
                  rounded-xl
                  border
                  border-slate-700
                  bg-slate-950
                  px-4
                  py-3
                  text-white
                  outline-none
                  focus:border-purple-500
                "
              />
            </div>

          </div>
        </section>


        {/* SAVE CONFIG */}

        <div
          className="
            flex
            justify-end
          "
        >
          <button
            type="submit"
            disabled={
              saving
            }
            className="
              rounded-xl
              bg-purple-600
              px-6
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
            {saving
              ? "Saving..."
              : "Save Configuration"}
          </button>
        </div>

      </form>


      {/* SCHEMA MAPPING */}

      <ClientSchemaMapping
        clientId={
          clientId
        }
        initialMapping={
          client.column_mapping
        }
        onSaved={(
          mapping:
            Record<string, string>,
        ) => {
          setClient(
            (current) => {
              if (!current) {
                return current;
              }

              return {
                ...current,

                column_mapping:
                  mapping,
              };
            },
          );
        }}
      />


      {/* HISTORICAL BASELINE */}

      <ClientBaselineManager
        clientId={
          clientId
        }
        clientName={
          client.name
        }
        baselineReady={
          client.baseline_ready
        }
        minimumHistoryRows={
          client.minimum_history_rows
        }
        onBaselineCreated={() => {
          void loadClient(
            false,
          );
        }}
      />


      {/* USERS & ACCESS */}

      <ClientUsersManager
        clientId={
          clientId
        }
        clientName={
          client.name
        }
      />


      {/* ACTIVE / INACTIVE */}

      <section
        className={`
          rounded-2xl
          border
          p-6
          ${
            client.is_active
              ? `
                border-amber-900/60
                bg-amber-950/10
              `
              : `
                border-emerald-900/60
                bg-emerald-950/10
              `
          }
        `}
      >
        <div
          className="
            flex
            flex-col
            gap-5
            lg:flex-row
            lg:items-center
            lg:justify-between
          "
        >
          <div>
            <h2
              className="
                text-lg
                font-semibold
                text-white
              "
            >
              Client Access Status
            </h2>


            <p
              className="
                mt-2
                max-w-2xl
                text-sm
                text-slate-400
              "
            >
              {client.is_active
                ? "This organization is currently active in FinGuard."
                : "This organization is currently inactive. Client operations may be restricted."}
            </p>
          </div>


          <button
            type="button"
            onClick={() => {
              void handleStatusChange();
            }}
            disabled={
              changingStatus
            }
            className={`
              rounded-xl
              px-5
              py-3
              text-sm
              font-semibold
              transition
              disabled:cursor-not-allowed
              disabled:opacity-50
              ${
                client.is_active
                  ? `
                    bg-amber-600
                    text-white
                    hover:bg-amber-500
                  `
                  : `
                    bg-emerald-600
                    text-white
                    hover:bg-emerald-500
                  `
              }
            `}
          >
            {changingStatus
              ? "Updating..."
              : client.is_active
                ? "Deactivate Client"
                : "Activate Client"}
          </button>
        </div>
      </section>


      {/* METADATA */}

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
          Client Metadata
        </h2>


        <div
          className="
            mt-5
            grid
            gap-5
            sm:grid-cols-2
            lg:grid-cols-4
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
              Client ID
            </p>

            <p
              className="
                mt-1
                text-sm
                text-white
              "
            >
              #{client.id}
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
              Baseline Ready
            </p>

            <p
              className={`
                mt-1
                text-sm
                font-medium
                ${
                  client.baseline_ready
                    ? "text-emerald-300"
                    : "text-amber-300"
                }
              `}
            >
              {client.baseline_ready
                ? "Yes"
                : "No"}
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
              Created
            </p>

            <p
              className="
                mt-1
                text-sm
                text-white
              "
            >
              {formatDate(
                client.created_at,
              )}
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
              Updated
            </p>

            <p
              className="
                mt-1
                text-sm
                text-white
              "
            >
              {formatDate(
                client.updated_at,
              )}
            </p>
          </div>

        </div>
      </section>

    </div>
  );
}
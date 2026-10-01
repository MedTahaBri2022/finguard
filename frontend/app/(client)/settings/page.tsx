"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  apiFetch,
} from "@/lib/api";

import type {
  AuthUser,
} from "@/lib/auth";


interface ClientProfile {
  id: number;
  name: string;

  business_type:
    | string
    | null;

  base_currency: string;

  risk_tolerance: string;

  baseline_ready: boolean;

  minimum_history_rows: number;

  is_active: boolean;

  failure_rate_warning:
    | number
    | null;

  refund_rate_warning:
    | number
    | null;

  high_amount_multiplier:
    | number
    | null;

  analysis_count?: number;

  baseline_count?: number;

  created_at?:
    | string
    | null;

  updated_at?:
    | string
    | null;
}


function formatPercentage(
  value: number | null,
): string {
  if (value === null) {
    return "Not configured";
  }

  return `${(
    value * 100
  ).toFixed(2)}%`;
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


function formatRole(
  role: string,
): string {
  return role
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase(),
    );
}


function SettingRow({
  label,
  value,
  description,
}: {
  label: string;
  value: string;
  description?: string;
}) {
  return (
    <div
      className="
        flex
        flex-col
        gap-2
        border-b
        border-slate-800
        py-5
        last:border-b-0
        sm:flex-row
        sm:items-center
        sm:justify-between
        sm:gap-8
      "
    >
      <div>
        <p
          className="
            text-sm
            font-medium
            text-slate-200
          "
        >
          {label}
        </p>

        {description && (
          <p
            className="
              mt-1
              max-w-xl
              text-xs
              leading-5
              text-slate-500
            "
          >
            {description}
          </p>
        )}
      </div>

      <p
        className="
          shrink-0
          text-sm
          font-semibold
          text-white
        "
      >
        {value}
      </p>
    </div>
  );
}


export default function SettingsPage() {
  const [
    user,
    setUser,
  ] =
    useState<AuthUser | null>(
      null,
    );

  const [
    client,
    setClient,
  ] =
    useState<ClientProfile | null>(
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


    async function loadSettings() {
      try {
        setLoading(true);
        setError(null);


        const [
          currentUser,
          currentClient,
        ] =
          await Promise.all([
            apiFetch<AuthUser>(
              "/api/v1/auth/me",
            ),

            apiFetch<ClientProfile>(
              "/api/v1/clients/me",
            ),
          ]);


        if (!active) {
          return;
        }


        setUser(
          currentUser,
        );

        setClient(
          currentClient,
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
            "Unable to load company settings.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }


    loadSettings();


    return () => {
      active = false;
    };
  }, []);


  if (loading) {
    return (
      <div>
        <p
          className="
            text-sm
            font-medium
            text-blue-400
          "
        >
          Client Workspace
        </p>

        <h1
          className="
            mt-1
            text-3xl
            font-bold
            text-white
          "
        >
          Settings
        </h1>

        <p
          className="
            mt-3
            text-slate-400
          "
        >
          Loading company
          configuration...
        </p>
      </div>
    );
  }


  if (
    error ||
    !user ||
    !client
  ) {
    return (
      <div>
        <h1
          className="
            text-3xl
            font-bold
            text-white
          "
        >
          Settings
        </h1>

        <div
          className="
            mt-6
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
            Unable to load settings
          </p>

          <p
            className="
              mt-2
              text-sm
              text-red-300
            "
          >
            {error ??
              "Company information is unavailable."}
          </p>
        </div>
      </div>
    );
  }


  const baselineStatus =
    client.baseline_ready
      ? "Operational"
      : "Not Ready";


  return (
    <div className="space-y-8">

      {/* HEADER */}

      <section>
        <p
          className="
            text-sm
            font-medium
            text-blue-400
          "
        >
          Client Workspace
        </p>

        <h1
          className="
            mt-1
            text-3xl
            font-bold
            text-white
          "
        >
          Settings
        </h1>

        <p
          className="
            mt-2
            max-w-2xl
            text-slate-400
          "
        >
          View your company profile,
          FinGuard risk configuration,
          baseline status and account
          information.
        </p>
      </section>


      {/* COMPANY OVERVIEW */}

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
            sm:flex-row
            sm:items-center
            sm:justify-between
          "
        >
          <div>
            <p
              className="
                text-xs
                font-medium
                uppercase
                tracking-wider
                text-slate-500
              "
            >
              Company
            </p>

            <h2
              className="
                mt-2
                text-2xl
                font-bold
                text-white
              "
            >
              {client.name}
            </h2>

            <p
              className="
                mt-2
                text-sm
                text-slate-400
              "
            >
              FinGuard Client ID #
              {client.id}
            </p>
          </div>


          <span
            className={`
              inline-flex
              w-fit
              rounded-full
              border
              px-3
              py-1
              text-xs
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
        <div
          className="
            border-b
            border-slate-800
            pb-5
          "
        >
          <h2
            className="
              text-lg
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
            Business information used
            by FinGuard.
          </p>
        </div>


        <SettingRow
          label="Company Name"
          value={client.name}
        />

        <SettingRow
          label="Business Type"
          value={
            client.business_type ??
            "Not configured"
          }
        />

        <SettingRow
          label="Base Currency"
          value={
            client.base_currency
          }
          description="
            Currency used to normalize
            financial amounts and risk
            calculations.
          "
        />

        <SettingRow
          label="Risk Tolerance"
          value={
            client.risk_tolerance
          }
          description="
            Company-specific risk
            sensitivity used by
            FinGuard configuration.
          "
        />
      </section>


      {/* RISK ENGINE */}

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
            border-b
            border-slate-800
            pb-5
          "
        >
          <h2
            className="
              text-lg
              font-semibold
              text-white
            "
          >
            Risk Engine Configuration
          </h2>

          <p
            className="
              mt-1
              text-sm
              text-slate-400
            "
          >
            Detection parameters
            configured for your
            organization.
          </p>
        </div>


        <SettingRow
          label="Failure Rate Warning"
          value={
            formatPercentage(
              client.failure_rate_warning,
            )
          }
        />

        <SettingRow
          label="Refund Rate Warning"
          value={
            formatPercentage(
              client.refund_rate_warning,
            )
          }
        />

        <SettingRow
          label="High Amount Multiplier"
          value={
            client.high_amount_multiplier !==
            null
              ? `${client.high_amount_multiplier}×`
              : "Not configured"
          }
          description="
            Multiplier used as part of
            high-value transaction
            anomaly detection.
          "
        />
      </section>


      {/* BASELINE */}

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
            gap-4
            border-b
            border-slate-800
            pb-5
            sm:flex-row
            sm:items-center
            sm:justify-between
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
              Historical Baseline
            </h2>

            <p
              className="
                mt-1
                text-sm
                text-slate-400
              "
            >
              Historical behavior used
              to contextualize financial
              anomaly detection.
            </p>
          </div>


          <span
            className={`
              w-fit
              rounded-full
              border
              px-3
              py-1
              text-xs
              font-semibold
              ${
                client.baseline_ready
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
            {baselineStatus}
          </span>
        </div>


        <SettingRow
          label="Baseline Status"
          value={baselineStatus}
        />

        <SettingRow
          label="Baseline Versions"
          value={String(
            client.baseline_count ??
              0,
          )}
        />

        <SettingRow
          label="Minimum History Rows"
          value={String(
            client.minimum_history_rows,
          )}
          description="
            Minimum historical sample
            expected before the client
            baseline is considered
            usable.
          "
        />

        <SettingRow
          label="Analyses"
          value={String(
            client.analysis_count ??
              0,
          )}
        />
      </section>


      {/* ACCOUNT */}

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
            border-b
            border-slate-800
            pb-5
          "
        >
          <h2
            className="
              text-lg
              font-semibold
              text-white
            "
          >
            Account & Access
          </h2>

          <p
            className="
              mt-1
              text-sm
              text-slate-400
            "
          >
            Your authenticated
            FinGuard account.
          </p>
        </div>


        <SettingRow
          label="Email"
          value={user.email}
        />

        <SettingRow
          label="Role"
          value={
            formatRole(
              user.role,
            )
          }
        />

        <SettingRow
          label="Account Status"
          value={
            user.is_active
              ? "Active"
              : "Inactive"
          }
        />

        <SettingRow
          label="Tenant"
          value={
            user.client?.name ??
            client.name
          }
          description="
            Your account is restricted
            to this company workspace.
          "
        />
      </section>


      {/* METADATA */}

      {(client.created_at ||
        client.updated_at) && (
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
            Configuration Metadata
          </h2>


          <div className="mt-4">
            <SettingRow
              label="Created"
              value={
                formatDate(
                  client.created_at,
                )
              }
            />

            <SettingRow
              label="Last Updated"
              value={
                formatDate(
                  client.updated_at,
                )
              }
            />
          </div>
        </section>
      )}


      {/* SECURITY */}

      <section
        className="
          rounded-2xl
          border
          border-blue-900/50
          bg-blue-950/10
          p-6
        "
      >
        <h2
          className="
            font-semibold
            text-blue-300
          "
        >
          Tenant Security
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
          This workspace does not
          select a company from the
          browser. FinGuard determines
          your company from your
          authenticated account and
          restricts client data on the
          backend.
        </p>
      </section>

    </div>
  );
}
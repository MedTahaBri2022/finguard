"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  apiFetch,
} from "@/lib/api";


interface AlertItem {
  id: number;
  analysis_id: number | null;
  client_profile_id: number | null;
  title: string;
  alert_type: string;
  severity: string;
  message: string;
  amount_at_risk: number;
  transaction_id: string | null;
  is_read: boolean;
  created_at: string;
}


interface AlertsResponse {
  alerts?: AlertItem[];
  items?: AlertItem[];
}


function normalizeAlerts(
  data: AlertItem[] | AlertsResponse,
): AlertItem[] {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data.alerts)) {
    return data.alerts;
  }

  if (Array.isArray(data.items)) {
    return data.items;
  }

  return [];
}


function severityClass(
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

  return "border-emerald-900 bg-emerald-950/40 text-emerald-300";
}


export default function AlertsPage() {
  const [alerts, setAlerts] =
    useState<AlertItem[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const [
    updatingAlertId,
    setUpdatingAlertId,
  ] =
    useState<number | null>(null);

  const [
    markingAll,
    setMarkingAll,
  ] =
    useState(false);


  useEffect(() => {
    let active = true;

    async function loadAlerts() {
      try {
        setLoading(true);
        setError(null);

        const data =
          await apiFetch<
            AlertItem[] | AlertsResponse
          >(
            "/api/v1/alerts/",
          );

        if (!active) {
          return;
        }

        setAlerts(
          normalizeAlerts(data),
        );
      } catch (err) {
        if (!active) {
          return;
        }

        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError(
            "Unable to load alerts.",
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadAlerts();

    return () => {
      active = false;
    };
  }, []);


  const unreadCount =
    useMemo(
      () =>
        alerts.filter(
          (alert) =>
            !alert.is_read,
        ).length,
      [alerts],
    );


  const highCount =
    useMemo(
      () =>
        alerts.filter(
          (alert) =>
            alert.severity
              .toUpperCase() ===
            "HIGH",
        ).length,
      [alerts],
    );


  const mediumCount =
    useMemo(
      () =>
        alerts.filter(
          (alert) =>
            alert.severity
              .toUpperCase() ===
            "MEDIUM",
        ).length,
      [alerts],
    );


  const totalMoneyAtRisk =
    useMemo(
      () =>
        alerts.reduce(
          (sum, alert) =>
            sum +
            (
              alert.amount_at_risk ??
              0
            ),
          0,
        ),
      [alerts],
    );


  async function handleMarkAsRead(
    alertId: number,
  ) {
    try {
      setUpdatingAlertId(
        alertId,
      );

      const updatedAlert =
        await apiFetch<AlertItem>(
          `/api/v1/alerts/${alertId}/read`,
          {
            method: "PATCH",
          },
        );

      setAlerts(
        (current) =>
          current.map(
            (alert) =>
              alert.id === alertId
                ? {
                    ...alert,
                    ...updatedAlert,
                    is_read: true,
                  }
                : alert,
          ),
      );
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(
          "Unable to update alert.",
        );
      }
    } finally {
      setUpdatingAlertId(
        null,
      );
    }
  }


  async function handleMarkAllAsRead() {
    const unreadAlerts =
      alerts.filter(
        (alert) =>
          !alert.is_read,
      );

    if (
      unreadAlerts.length === 0
    ) {
      return;
    }

    try {
      setMarkingAll(true);
      setError(null);

      await Promise.all(
        unreadAlerts.map(
          (alert) =>
            apiFetch<AlertItem>(
              `/api/v1/alerts/${alert.id}/read`,
              {
                method: "PATCH",
              },
            ),
        ),
      );

      setAlerts(
        (current) =>
          current.map(
            (alert) => ({
              ...alert,
              is_read: true,
            }),
          ),
      );
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(
          "Unable to mark all alerts as read.",
        );
      }
    } finally {
      setMarkingAll(false);
    }
  }


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
          Alerts
        </h1>

        <p className="mt-2 text-slate-400">
          Loading company alerts...
        </p>
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
            Alerts
          </h1>

          <p className="mt-2 text-slate-400">
            Financial risk alerts detected
            for your company.
          </p>
        </div>


        <button
          type="button"
          onClick={
            handleMarkAllAsRead
          }
          disabled={
            markingAll ||
            unreadCount === 0
          }
          className="
            rounded-xl
            border border-slate-700
            px-5 py-3
            text-sm font-semibold
            text-slate-200
            transition
            hover:bg-slate-800
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >
          {markingAll
            ? "Updating..."
            : "Mark All as Read"}
        </button>
      </div>


      {error && (
        <div className="mt-6 rounded-2xl border border-red-900/60 bg-red-950/20 p-4">
          <p className="text-sm text-red-300">
            {error}
          </p>
        </div>
      )}


      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Total Alerts
          </p>

          <p className="mt-2 text-3xl font-bold">
            {alerts.length}
          </p>
        </div>


        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Unread
          </p>

          <p className="mt-2 text-3xl font-bold">
            {unreadCount}
          </p>
        </div>


        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            High Risk
          </p>

          <p className="mt-2 text-3xl font-bold">
            {highCount}
          </p>

          <p className="mt-1 text-xs text-slate-500">
            Medium: {mediumCount}
          </p>
        </div>


        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">
            Money At Risk
          </p>

          <p className="mt-2 text-xl font-bold">
            {formatMoney(
              totalMoneyAtRisk,
            )}
          </p>
        </div>
      </div>


      <div className="mt-8 space-y-4">
        {alerts.length === 0 ? (
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center">
            <p className="text-slate-400">
              No alerts found.
            </p>
          </div>
        ) : (
          alerts.map(
            (alert) => (
              <div
                key={alert.id}
                className={`
                  rounded-2xl
                  border
                  p-5
                  transition
                  ${
                    alert.is_read
                      ? "border-slate-800 bg-slate-900/70"
                      : "border-slate-700 bg-slate-900"
                  }
                `}
              >
                <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-3">
                      <span
                        className={`
                          rounded-full
                          border
                          px-3 py-1
                          text-xs font-medium
                          ${severityClass(
                            alert.severity,
                          )}
                        `}
                      >
                        {
                          alert.severity
                        }
                      </span>

                      {!alert.is_read && (
                        <span className="rounded-full border border-blue-900 bg-blue-950/40 px-3 py-1 text-xs font-medium text-blue-300">
                          Unread
                        </span>
                      )}

                      <span className="text-xs text-slate-500">
                        Alert #{alert.id}
                      </span>
                    </div>


                    <h2 className="mt-4 text-lg font-semibold text-white">
                      {alert.title}
                    </h2>

                    <p className="mt-2 text-sm leading-6 text-slate-400">
                      {alert.message}
                    </p>


                    <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                      <div>
                        <p className="text-xs uppercase tracking-wide text-slate-500">
                          Type
                        </p>

                        <p className="mt-1 text-sm font-medium">
                          {
                            alert.alert_type
                          }
                        </p>
                      </div>


                      <div>
                        <p className="text-xs uppercase tracking-wide text-slate-500">
                          Money At Risk
                        </p>

                        <p className="mt-1 text-sm font-medium">
                          {formatMoney(
                            alert.amount_at_risk ??
                              0,
                          )}
                        </p>
                      </div>


                      <div>
                        <p className="text-xs uppercase tracking-wide text-slate-500">
                          Transaction
                        </p>

                        <p className="mt-1 break-all text-sm font-medium">
                          {alert.transaction_id ??
                            "N/A"}
                        </p>
                      </div>


                      <div>
                        <p className="text-xs uppercase tracking-wide text-slate-500">
                          Created
                        </p>

                        <p className="mt-1 text-sm font-medium">
                          {formatDate(
                            alert.created_at,
                          )}
                        </p>
                      </div>
                    </div>
                  </div>


                  <div className="flex shrink-0 flex-col gap-3">
                    {alert.analysis_id && (
                      <a
                        href={`/analysis/${alert.analysis_id}`}
                        className="
                          rounded-xl
                          border border-slate-700
                          px-4 py-2
                          text-center text-sm
                          font-medium
                          text-slate-300
                          hover:bg-slate-800
                        "
                      >
                        View Analysis
                      </a>
                    )}

                    {!alert.is_read && (
                      <button
                        type="button"
                        disabled={
                          updatingAlertId ===
                          alert.id
                        }
                        onClick={() =>
                          handleMarkAsRead(
                            alert.id,
                          )
                        }
                        className="
                          rounded-xl
                          bg-blue-600
                          px-4 py-2
                          text-sm font-semibold
                          text-white
                          hover:bg-blue-500
                          disabled:cursor-not-allowed
                          disabled:opacity-50
                        "
                      >
                        {updatingAlertId ===
                        alert.id
                          ? "Updating..."
                          : "Mark as Read"}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ),
          )
        )}
      </div>
    </div>
  );
}
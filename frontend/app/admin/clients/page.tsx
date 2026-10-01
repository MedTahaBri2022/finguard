"use client";

import {
  FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";

import Link from "next/link";

import { apiFetch } from "@/lib/api";


interface ClientProfile {
  id: number;
  name: string;
  business_type: string | null;
  base_currency: string;
  risk_tolerance: string;

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

  created_at?:
    | string
    | null;

  updated_at?:
    | string
    | null;
}


interface ClientsResponse {
  total: number;
  clients: ClientProfile[];
}


interface CreateClientResponse {
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

  is_active: boolean;
}


const INITIAL_FORM: ClientForm = {
  name: "",
  business_type: "",
  base_currency: "MAD",
  risk_tolerance: "conservative",

  failure_rate_warning: "0.05",
  refund_rate_warning: "0.08",
  high_amount_multiplier: "3",

  minimum_history_rows: "100",

  is_active: true,
};


function formatDate(
  value:
    | string
    | null
    | undefined,
): string {
  if (!value) {
    return "N/A";
  }

  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return date.toLocaleDateString(
    "fr-MA",
  );
}


function formatBusinessType(
  value: string | null,
): string {
  if (!value) {
    return "Not configured";
  }

  return value
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase(),
    );
}


function parseOptionalNumber(
  value: string,
): number | null {
  const trimmed =
    value.trim();

  if (!trimmed) {
    return null;
  }

  const parsed =
    Number(trimmed);

  if (
    !Number.isFinite(parsed)
  ) {
    return null;
  }

  return parsed;
}


export default function AdminClientsPage() {
  const [
    clients,
    setClients,
  ] =
    useState<ClientProfile[]>(
      [],
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

  const [
    success,
    setSuccess,
  ] =
    useState<string | null>(
      null,
    );

  const [
    search,
    setSearch,
  ] =
    useState("");

  const [
    statusFilter,
    setStatusFilter,
  ] =
    useState("all");

  const [
    baselineFilter,
    setBaselineFilter,
  ] =
    useState("all");

  const [
    showCreate,
    setShowCreate,
  ] =
    useState(false);

  const [
    creating,
    setCreating,
  ] =
    useState(false);

  const [
    form,
    setForm,
  ] =
    useState<ClientForm>(
      INITIAL_FORM,
    );


  async function loadClients() {
    try {
      setLoading(true);
      setError(null);

      const response =
        await apiFetch<ClientsResponse>(
          "/api/v1/clients?active_only=false",
        );

      setClients(
        Array.isArray(
          response.clients,
        )
          ? response.clients
          : [],
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
          "Unable to load clients.",
        );
      }
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    void loadClients();
  }, []);


  const filteredClients =
    useMemo(() => {
      const query =
        search
          .trim()
          .toLowerCase();

      return clients.filter(
        (client) => {
          const matchesSearch =
            !query ||
            client.name
              .toLowerCase()
              .includes(query) ||
            (
              client.business_type ??
              ""
            )
              .toLowerCase()
              .includes(query) ||
            client.base_currency
              .toLowerCase()
              .includes(query) ||
            client.risk_tolerance
              .toLowerCase()
              .includes(query) ||
            String(
              client.id,
            ).includes(query);


          const matchesStatus =
            statusFilter ===
              "all" ||
            (
              statusFilter ===
                "active" &&
              client.is_active
            ) ||
            (
              statusFilter ===
                "inactive" &&
              !client.is_active
            );


          const matchesBaseline =
            baselineFilter ===
              "all" ||
            (
              baselineFilter ===
                "ready" &&
              client.baseline_ready
            ) ||
            (
              baselineFilter ===
                "not_ready" &&
              !client.baseline_ready
            );


          return (
            matchesSearch &&
            matchesStatus &&
            matchesBaseline
          );
        },
      );
    }, [
      clients,
      search,
      statusFilter,
      baselineFilter,
    ]);


  const activeClients =
    useMemo(
      () =>
        clients.filter(
          (client) =>
            client.is_active,
        ).length,
      [clients],
    );


  const inactiveClients =
    clients.length -
    activeClients;


  const readyBaselines =
    useMemo(
      () =>
        clients.filter(
          (client) =>
            client.baseline_ready,
        ).length,
      [clients],
    );


  function updateForm<
    K extends keyof ClientForm
  >(
    field: K,
    value: ClientForm[K],
  ) {
    setForm(
      (current) => ({
        ...current,
        [field]: value,
      }),
    );
  }


  function openCreateModal() {
    setForm({
      ...INITIAL_FORM,
    });

    setError(null);
    setSuccess(null);
    setShowCreate(true);
  }


  function closeCreateModal() {
    if (creating) {
      return;
    }

    setShowCreate(false);
  }


  async function handleCreateClient(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const name =
      form.name.trim();

    const currency =
      form.base_currency
        .trim()
        .toUpperCase();

    const minimumRows =
      Number(
        form.minimum_history_rows,
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


    try {
      setCreating(true);
      setError(null);
      setSuccess(null);


      const response =
        await apiFetch<CreateClientResponse>(
          "/api/v1/clients",
          {
            method: "POST",

            body: JSON.stringify({
              name,

              business_type:
                form.business_type
                  .trim() ||
                null,

              base_currency:
                currency,

              risk_tolerance:
                form.risk_tolerance,

              failure_rate_warning:
                parseOptionalNumber(
                  form.failure_rate_warning,
                ),

              refund_rate_warning:
                parseOptionalNumber(
                  form.refund_rate_warning,
                ),

              high_amount_multiplier:
                parseOptionalNumber(
                  form.high_amount_multiplier,
                ),

              minimum_history_rows:
                minimumRows,

              is_active:
                form.is_active,
            }),
          },
        );


      setClients(
        (current) => [
          ...current,
          response.client,
        ],
      );


      setSuccess(
        `${response.client.name} created successfully.`,
      );


      setForm({
        ...INITIAL_FORM,
      });

      setShowCreate(false);
    } catch (err) {
      if (
        err instanceof Error
      ) {
        setError(
          err.message,
        );
      } else {
        setError(
          "Unable to create client.",
        );
      }
    } finally {
      setCreating(false);
    }
  }


  return (
    <div className="space-y-8">

      {/* HEADER */}

      <section
        className="
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
            Clients
          </h1>

          <p
            className="
              mt-2
              max-w-2xl
              text-slate-400
            "
          >
            Manage FinGuard client
            organizations, risk
            configuration and
            historical baselines.
          </p>
        </div>


        <button
          type="button"
          onClick={
            openCreateModal
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
          "
        >
          + Create Client
        </button>
      </section>


      {/* FEEDBACK */}

      {error && (
        <section
          className="
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
            Error
          </p>

          <p
            className="
              mt-1
              text-sm
              text-red-300
            "
          >
            {error}
          </p>
        </section>
      )}


      {success && (
        <section
          className="
            rounded-2xl
            border
            border-emerald-900/60
            bg-emerald-950/20
            p-5
          "
        >
          <p
            className="
              text-sm
              font-medium
              text-emerald-300
            "
          >
            {success}
          </p>
        </section>
      )}


      {/* KPI */}

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
          <p className="text-sm text-slate-400">
            Total Clients
          </p>

          <p
            className="
              mt-2
              text-3xl
              font-bold
              text-white
            "
          >
            {clients.length}
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
          <p className="text-sm text-slate-400">
            Active
          </p>

          <p
            className="
              mt-2
              text-3xl
              font-bold
              text-emerald-300
            "
          >
            {activeClients}
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
          <p className="text-sm text-slate-400">
            Inactive
          </p>

          <p
            className="
              mt-2
              text-3xl
              font-bold
              text-slate-300
            "
          >
            {inactiveClients}
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
          <p className="text-sm text-slate-400">
            Ready Baselines
          </p>

          <p
            className="
              mt-2
              text-3xl
              font-bold
              text-blue-300
            "
          >
            {readyBaselines}
          </p>
        </div>
      </section>


      {/* SEARCH + FILTERS */}

      <section
        className="
          rounded-2xl
          border
          border-slate-800
          bg-slate-900
          p-5
        "
      >
        <div
          className="
            grid
            gap-4
            lg:grid-cols-[1fr_200px_220px]
          "
        >
          <input
            type="text"
            value={search}
            onChange={(event) => {
              setSearch(
                event.target.value,
              );
            }}
            placeholder="Search company, business type, currency or ID..."
            className="
              rounded-xl
              border
              border-slate-700
              bg-slate-950
              px-4
              py-3
              text-sm
              text-white
              outline-none
              placeholder:text-slate-500
              focus:border-purple-500
            "
          />


          <select
            value={
              statusFilter
            }
            onChange={(event) => {
              setStatusFilter(
                event.target.value,
              );
            }}
            className="
              rounded-xl
              border
              border-slate-700
              bg-slate-950
              px-4
              py-3
              text-sm
              text-white
              outline-none
              focus:border-purple-500
            "
          >
            <option value="all">
              All statuses
            </option>

            <option value="active">
              Active
            </option>

            <option value="inactive">
              Inactive
            </option>
          </select>


          <select
            value={
              baselineFilter
            }
            onChange={(event) => {
              setBaselineFilter(
                event.target.value,
              );
            }}
            className="
              rounded-xl
              border
              border-slate-700
              bg-slate-950
              px-4
              py-3
              text-sm
              text-white
              outline-none
              focus:border-purple-500
            "
          >
            <option value="all">
              All baselines
            </option>

            <option value="ready">
              Baseline Ready
            </option>

            <option value="not_ready">
              Baseline Not Ready
            </option>
          </select>
        </div>
      </section>


      {/* CLIENT LIST */}

      <section
        className="
          overflow-hidden
          rounded-2xl
          border
          border-slate-800
          bg-slate-900
        "
      >
        {loading ? (
          <div
            className="
              p-10
              text-center
              text-slate-400
            "
          >
            Loading clients...
          </div>
        ) : filteredClients.length ===
          0 ? (
          <div
            className="
              p-10
              text-center
              text-slate-400
            "
          >
            No clients match your filters.
          </div>
        ) : (
          <div
            className="
              divide-y
              divide-slate-800
            "
          >
            {filteredClients.map(
              (client) => (
                <article
                  key={
                    client.id
                  }
                  className="
                    p-5
                    transition
                    hover:bg-slate-800/30
                  "
                >
                  <div
                    className="
                      flex
                      flex-col
                      gap-6
                      xl:flex-row
                      xl:items-center
                      xl:justify-between
                    "
                  >
                    <div
                      className="
                        min-w-0
                        flex-1
                      "
                    >
                      <div
                        className="
                          flex
                          flex-wrap
                          items-center
                          gap-3
                        "
                      >
                        <h2
                          className="
                            text-lg
                            font-semibold
                            text-white
                          "
                        >
                          {client.name}
                        </h2>


                        <span
                          className={`
                            rounded-full
                            border
                            px-2.5
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


                        <span
                          className={`
                            rounded-full
                            border
                            px-2.5
                            py-1
                            text-xs
                            font-semibold
                            ${
                              client.baseline_ready
                                ? `
                                  border-blue-900
                                  bg-blue-950/40
                                  text-blue-300
                                `
                                : `
                                  border-amber-900
                                  bg-amber-950/40
                                  text-amber-300
                                `
                            }
                          `}
                        >
                          {client.baseline_ready
                            ? "Baseline Ready"
                            : "Baseline Not Ready"}
                        </span>
                      </div>


                      <div
                        className="
                          mt-5
                          grid
                          gap-4
                          sm:grid-cols-2
                          lg:grid-cols-5
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
                            Business
                          </p>

                          <p
                            className="
                              mt-1
                              text-sm
                              text-white
                            "
                          >
                            {formatBusinessType(
                              client.business_type,
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
                            Currency
                          </p>

                          <p
                            className="
                              mt-1
                              text-sm
                              text-white
                            "
                          >
                            {client.base_currency}
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
                            Risk Tolerance
                          </p>

                          <p
                            className="
                              mt-1
                              text-sm
                              capitalize
                              text-white
                            "
                          >
                            {client.risk_tolerance}
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
                      </div>
                    </div>


                    <Link
                      href={`/admin/clients/${client.id}`}
                      className="
                        shrink-0
                        rounded-xl
                        bg-purple-600
                        px-5
                        py-2.5
                        text-center
                        text-sm
                        font-semibold
                        text-white
                        transition
                        hover:bg-purple-500
                      "
                    >
                      Manage Client
                    </Link>
                  </div>
                </article>
              ),
            )}
          </div>
        )}
      </section>


      <p
        className="
          text-sm
          text-slate-500
        "
      >
        Showing{" "}
        {filteredClients.length}
        {" "}of{" "}
        {clients.length}
        {" "}clients.
      </p>


      {/* CREATE CLIENT MODAL */}

      {showCreate && (
        <div
          className="
            fixed
            inset-0
            z-50
            flex
            items-center
            justify-center
            bg-black/70
            p-4
          "
        >
          <div
            className="
              max-h-[90vh]
              w-full
              max-w-2xl
              overflow-y-auto
              rounded-2xl
              border
              border-slate-700
              bg-slate-900
              p-6
              shadow-2xl
            "
          >
            <div
              className="
                flex
                items-start
                justify-between
                gap-5
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

                <h2
                  className="
                    mt-1
                    text-2xl
                    font-bold
                    text-white
                  "
                >
                  Create Client
                </h2>

                <p
                  className="
                    mt-2
                    text-sm
                    text-slate-400
                  "
                >
                  Create a new isolated
                  FinGuard organization.
                </p>
              </div>


              <button
                type="button"
                onClick={
                  closeCreateModal
                }
                disabled={
                  creating
                }
                className="
                  rounded-lg
                  px-3
                  py-2
                  text-slate-400
                  transition
                  hover:bg-slate-800
                  hover:text-white
                  disabled:opacity-50
                "
              >
                ✕
              </button>
            </div>


            <form
              onSubmit={
                handleCreateClient
              }
              className="
                mt-7
                space-y-5
              "
            >
              <div>
                <label
                  className="
                    mb-2
                    block
                    text-sm
                    font-medium
                    text-slate-300
                  "
                >
                  Company Name *
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
                  placeholder="Example Company SA"
                  required
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
                    font-medium
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


              <div
                className="
                  grid
                  gap-4
                  sm:grid-cols-2
                "
              >
                <div>
                  <label
                    className="
                      mb-2
                      block
                      text-sm
                      font-medium
                      text-slate-300
                    "
                  >
                    Base Currency *
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
                    required
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
                      font-medium
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
                    <option value="conservative">
                      Conservative
                    </option>

                    <option value="balanced">
                      Balanced
                    </option>

                    <option value="aggressive">
                      Aggressive
                    </option>
                  </select>
                </div>
              </div>


              <div
                className="
                  grid
                  gap-4
                  sm:grid-cols-3
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
                    Failure Warning
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
                    Refund Warning
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
                    Amount Multiplier
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


              <label
                className="
                  flex
                  cursor-pointer
                  items-center
                  gap-3
                  rounded-xl
                  border
                  border-slate-800
                  bg-slate-950/60
                  p-4
                "
              >
                <input
                  type="checkbox"
                  checked={
                    form.is_active
                  }
                  onChange={(event) => {
                    updateForm(
                      "is_active",
                      event.target.checked,
                    );
                  }}
                  className="
                    h-4
                    w-4
                  "
                />

                <div>
                  <p
                    className="
                      text-sm
                      font-medium
                      text-white
                    "
                  >
                    Activate Client
                  </p>

                  <p
                    className="
                      mt-1
                      text-xs
                      text-slate-500
                    "
                  >
                    Enable this
                    organization in
                    FinGuard.
                  </p>
                </div>
              </label>


              <div
                className="
                  flex
                  justify-end
                  gap-3
                  border-t
                  border-slate-800
                  pt-5
                "
              >
                <button
                  type="button"
                  onClick={
                    closeCreateModal
                  }
                  disabled={
                    creating
                  }
                  className="
                    rounded-xl
                    border
                    border-slate-700
                    px-5
                    py-3
                    text-sm
                    text-slate-300
                    transition
                    hover:bg-slate-800
                    disabled:opacity-50
                  "
                >
                  Cancel
                </button>


                <button
                  type="submit"
                  disabled={
                    creating
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
                  {creating
                    ? "Creating..."
                    : "Create Client"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  apiFetch,
} from "@/lib/api";


interface MappingRow {
  id: number;
  source: string;
  canonical: string;
}


interface ClientSchemaMappingProps {
  clientId: string;

  initialMapping:
    | Record<string, string>
    | null
    | undefined;

  onSaved?: (
    mapping: Record<string, string>,
  ) => void;
}


interface UpdateClientResponse {
  message: string;

  client: {
    id: number;

    column_mapping:
      | Record<string, string>
      | null;
  };
}


const CANONICAL_FIELDS: string[] = [
  "transaction_id",
  "entity_id",
  "amount",
  "currency",
  "timestamp",
  "status",
  "transaction_type",
  "category",
  "balance",
  "merchant",
];


function createRowId(): number {
  return (
    Date.now() +
    Math.floor(
      Math.random() * 100000,
    )
  );
}


function mappingToRows(
  mapping:
    | Record<string, string>
    | null
    | undefined,
): MappingRow[] {
  if (!mapping) {
    return [];
  }

  return Object.entries(
    mapping,
  ).map(
    (
      [source, canonical],
      index,
    ) => ({
      id:
        Date.now() +
        index,

      source,

      canonical,
    }),
  );
}


export default function ClientSchemaMapping({
  clientId,
  initialMapping,
  onSaved,
}: ClientSchemaMappingProps) {
  const [
    rows,
    setRows,
  ] =
    useState<MappingRow[]>(
      [],
    );


  const [
    saving,
    setSaving,
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


  useEffect(() => {
    setRows(
      mappingToRows(
        initialMapping,
      ),
    );
  }, [initialMapping]);


  function addRow() {
    setRows(
      (current) => [
        ...current,

        {
          id:
            createRowId(),

          source: "",

          canonical: "",
        },
      ],
    );

    setError(null);
    setSuccess(null);
  }


  function updateRow(
    id: number,

    field:
      | "source"
      | "canonical",

    value: string,
  ) {
    setRows(
      (current) =>
        current.map(
          (row) => {
            if (
              row.id !== id
            ) {
              return row;
            }

            return {
              ...row,
              [field]:
                value,
            };
          },
        ),
    );

    setError(null);
    setSuccess(null);
  }


  function removeRow(
    id: number,
  ) {
    setRows(
      (current) =>
        current.filter(
          (row) =>
            row.id !== id,
        ),
    );

    setError(null);
    setSuccess(null);
  }


  function resetMapping() {
    setRows(
      mappingToRows(
        initialMapping,
      ),
    );

    setError(null);
    setSuccess(null);
  }


  function buildMapping():
    | Record<string, string>
    | null {
    const result:
      Record<string, string> =
      {};


    for (
      const row of rows
    ) {
      const source =
        row.source.trim();

      const canonical =
        row.canonical.trim();


      /*
       * Completely empty rows
       * are ignored.
       */
      if (
        !source &&
        !canonical
      ) {
        continue;
      }


      if (!source) {
        setError(
          "Every mapping row must have a source column.",
        );

        return null;
      }


      if (!canonical) {
        setError(
          `Select a FinGuard field for "${source}".`,
        );

        return null;
      }


      if (
        !CANONICAL_FIELDS.includes(
          canonical,
        )
      ) {
        setError(
          `Invalid FinGuard canonical field: ${canonical}`,
        );

        return null;
      }


      if (
        Object.prototype.hasOwnProperty.call(
          result,
          source,
        )
      ) {
        setError(
          `Source column "${source}" is duplicated.`,
        );

        return null;
      }


      result[source] =
        canonical;
    }


    /*
     * Prevent two source columns
     * from mapping to the same
     * canonical field.
     */

    const canonicalValues =
      Object.values(
        result,
      );


    const seen =
      new Set<string>();


    for (
      const canonical of canonicalValues
    ) {
      if (
        seen.has(
          canonical,
        )
      ) {
        setError(
          `FinGuard field "${canonical}" is mapped more than once.`,
        );

        return null;
      }

      seen.add(
        canonical,
      );
    }


    return result;
  }


  async function saveMapping() {
    const mapping =
      buildMapping();


    if (
      mapping === null
    ) {
      return;
    }


    if (
      Object.keys(
        mapping,
      ).length === 0
    ) {
      setError(
        "Add at least one column mapping before saving.",
      );

      return;
    }


    /*
     * Amount is fundamental for
     * FinGuard financial analysis.
     */

    if (
      !Object.values(
        mapping,
      ).includes(
        "amount",
      )
    ) {
      setError(
        'The mapping must include the FinGuard field "amount".',
      );

      return;
    }


    try {
      setSaving(true);

      setError(null);

      setSuccess(null);


      const response =
        await apiFetch<UpdateClientResponse>(
          `/api/v1/clients/${clientId}`,
          {
            method:
              "PATCH",

            body:
              JSON.stringify({
                column_mapping:
                  mapping,
              }),
          },
        );


      /*
       * Prefer the mapping returned
       * by the backend.
       *
       * If the backend response does
       * not contain it, keep the
       * mapping we just submitted.
       */

      const savedMapping =
        response.client
          .column_mapping ??
        mapping;


      setRows(
        mappingToRows(
          savedMapping,
        ),
      );


      setSuccess(
        "Schema mapping saved successfully.",
      );


      onSaved?.(
        savedMapping,
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
          "Unable to save schema mapping.",
        );
      }
    } finally {
      setSaving(false);
    }
  }


  const mappedFields =
    new Set(
      rows
        .map(
          (row) =>
            row.canonical,
        )
        .filter(
          Boolean,
        ),
    );


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

      {/* HEADER */}

      <div
        className="
          flex
          flex-col
          gap-4
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
            Schema / Column Mapping
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
            Map the column names
            received from this
            company to FinGuard&apos;s
            canonical financial
            schema.
          </p>
        </div>


        <button
          type="button"
          onClick={
            addRow
          }
          disabled={
            saving
          }
          className="
            rounded-xl
            border
            border-purple-700
            bg-purple-950/30
            px-4
            py-2.5
            text-sm
            font-semibold
            text-purple-300
            transition
            hover:bg-purple-900/40
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >
          + Add Mapping
        </button>
      </div>


      {/* EXPLANATION */}

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
            font-medium
            text-blue-300
          "
        >
          Client Column
          {" → "}
          FinGuard Field
        </p>


        <p
          className="
            mt-2
            text-sm
            leading-6
            text-slate-400
          "
        >
          Example:{" "}

          <code
            className="
              text-slate-200
            "
          >
            account_id
          </code>

          {" → "}

          <code
            className="
              text-purple-300
            "
          >
            entity_id
          </code>

          {" · "}

          <code
            className="
              text-slate-200
            "
          >
            transaction_timestamp
          </code>

          {" → "}

          <code
            className="
              text-purple-300
            "
          >
            timestamp
          </code>
        </p>
      </div>


      {/* ERROR */}

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


      {/* SUCCESS */}

      {success && (
        <div
          className="
            mt-5
            rounded-xl
            border
            border-emerald-900/60
            bg-emerald-950/20
            p-4
            text-sm
            text-emerald-300
          "
        >
          {success}
        </div>
      )}


      {/* MAPPING EDITOR */}

      <div
        className="
          mt-6
          space-y-3
        "
      >
        {rows.length ===
        0 ? (
          <div
            className="
              rounded-xl
              border
              border-dashed
              border-slate-700
              bg-slate-950/40
              p-8
              text-center
            "
          >
            <p
              className="
                font-medium
                text-slate-300
              "
            >
              No client-specific
              schema mapping
              configured.
            </p>


            <p
              className="
                mt-2
                text-sm
                text-slate-500
              "
            >
              Add the columns used
              by this client&apos;s
              transaction files.
            </p>


            <button
              type="button"
              onClick={
                addRow
              }
              className="
                mt-5
                rounded-xl
                bg-purple-600
                px-4
                py-2.5
                text-sm
                font-semibold
                text-white
                transition
                hover:bg-purple-500
              "
            >
              Add First Mapping
            </button>
          </div>
        ) : (
          <>

            {/* DESKTOP HEADER */}

            <div
              className="
                hidden
                grid-cols-[1fr_60px_1fr_60px]
                gap-4
                px-2
                text-xs
                font-medium
                uppercase
                tracking-wide
                text-slate-500
                md:grid
              "
            >
              <span>
                Client Source Column
              </span>

              <span />

              <span>
                FinGuard Field
              </span>

              <span />
            </div>


            {/* ROWS */}

            {rows.map(
              (row) => (
                <div
                  key={
                    row.id
                  }
                  className="
                    grid
                    gap-3
                    rounded-xl
                    border
                    border-slate-800
                    bg-slate-950/60
                    p-4
                    md:grid-cols-[1fr_60px_1fr_60px]
                    md:items-center
                  "
                >

                  {/* SOURCE */}

                  <div>
                    <label
                      className="
                        mb-2
                        block
                        text-xs
                        text-slate-500
                        md:hidden
                      "
                    >
                      Client Source
                      Column
                    </label>


                    <input
                      type="text"
                      value={
                        row.source
                      }
                      onChange={(
                        event,
                      ) => {
                        updateRow(
                          row.id,
                          "source",
                          event
                            .target
                            .value,
                        );
                      }}
                      placeholder="account_id"
                      disabled={
                        saving
                      }
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
                        placeholder:text-slate-600
                        focus:border-purple-500
                        disabled:opacity-60
                      "
                    />
                  </div>


                  {/* ARROW */}

                  <div
                    className="
                      hidden
                      text-center
                      text-xl
                      text-slate-500
                      md:block
                    "
                  >
                    →
                  </div>


                  {/* CANONICAL */}

                  <div>
                    <label
                      className="
                        mb-2
                        block
                        text-xs
                        text-slate-500
                        md:hidden
                      "
                    >
                      FinGuard Field
                    </label>


                    <select
                      value={
                        row.canonical
                      }
                      onChange={(
                        event,
                      ) => {
                        updateRow(
                          row.id,
                          "canonical",
                          event
                            .target
                            .value,
                        );
                      }}
                      disabled={
                        saving
                      }
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
                        focus:border-purple-500
                        disabled:opacity-60
                      "
                    >
                      <option
                        value=""
                      >
                        Select field...
                      </option>


                      {CANONICAL_FIELDS.map(
                        (
                          field,
                        ) => (
                          <option
                            key={
                              field
                            }
                            value={
                              field
                            }
                          >
                            {field}
                          </option>
                        ),
                      )}
                    </select>
                  </div>


                  {/* REMOVE */}

                  <button
                    type="button"
                    onClick={() => {
                      removeRow(
                        row.id,
                      );
                    }}
                    disabled={
                      saving
                    }
                    title="Remove mapping"
                    className="
                      rounded-lg
                      border
                      border-red-900/50
                      px-3
                      py-2
                      text-sm
                      text-red-300
                      transition
                      hover:bg-red-950/40
                      disabled:cursor-not-allowed
                      disabled:opacity-50
                    "
                  >
                    ✕
                  </button>

                </div>
              ),
            )}
          </>
        )}
      </div>


      {/* CANONICAL SCHEMA STATUS */}

      <div
        className="
          mt-7
          rounded-xl
          border
          border-slate-800
          bg-slate-950/40
          p-5
        "
      >
        <div
          className="
            flex
            flex-col
            gap-2
            sm:flex-row
            sm:items-center
            sm:justify-between
          "
        >
          <div>
            <p
              className="
                text-sm
                font-medium
                text-white
              "
            >
              FinGuard Canonical
              Schema
            </p>


            <p
              className="
                mt-1
                text-xs
                text-slate-500
              "
            >
              Green fields are
              currently mapped.
            </p>
          </div>


          <p
            className="
              text-sm
              text-slate-400
            "
          >
            {
              mappedFields.size
            }
            /
            {
              CANONICAL_FIELDS.length
            }
            {" "}
            mapped
          </p>
        </div>


        <div
          className="
            mt-4
            flex
            flex-wrap
            gap-2
          "
        >
          {CANONICAL_FIELDS.map(
            (field) => {
              const mapped =
                mappedFields.has(
                  field,
                );


              return (
                <span
                  key={
                    field
                  }
                  className={`
                    rounded-lg
                    border
                    px-3
                    py-1.5
                    text-xs
                    font-medium
                    ${
                      mapped
                        ? `
                          border-emerald-900
                          bg-emerald-950/30
                          text-emerald-300
                        `
                        : `
                          border-slate-700
                          bg-slate-900
                          text-slate-400
                        `
                    }
                  `}
                >
                  {field}

                  {mapped
                    ? " ✓"
                    : ""}
                </span>
              );
            },
          )}
        </div>
      </div>


      {/* IMPORTANT FIELD */}

      <div
        className="
          mt-5
          rounded-xl
          border
          border-slate-800
          bg-slate-950/30
          p-4
        "
      >
        <p
          className="
            text-sm
            text-slate-400
          "
        >
          <span
            className="
              font-medium
              text-white
            "
          >
            Required for saving:
          </span>

          {" "}

          the client schema must
          include a mapping to

          {" "}

          <code
            className="
              text-purple-300
            "
          >
            amount
          </code>

          .
        </p>
      </div>


      {/* ACTIONS */}

      <div
        className="
          mt-6
          flex
          flex-col
          gap-3
          sm:flex-row
          sm:justify-end
        "
      >
        <button
          type="button"
          onClick={
            resetMapping
          }
          disabled={
            saving
          }
          className="
            rounded-xl
            border
            border-slate-700
            px-5
            py-3
            text-sm
            font-medium
            text-slate-300
            transition
            hover:bg-slate-800
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >
          Reset
        </button>


        <button
          type="button"
          onClick={() => {
            void saveMapping();
          }}
          disabled={
            saving
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
          {saving
            ? "Saving Mapping..."
            : "Save Schema Mapping"}
        </button>
      </div>

    </section>
  );
}
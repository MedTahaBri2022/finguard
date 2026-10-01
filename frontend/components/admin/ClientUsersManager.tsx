"use client";

import {
  FormEvent,
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  ApiError,
  apiFetch,
} from "@/lib/api";


interface ClientUser {
  id: number;
  email: string;
  role: string;
  client_profile_id: number;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}


interface UsersResponse {
  client: {
    id: number;
    name: string;
  };

  total: number;

  users: ClientUser[];
}


interface CreateUserResponse {
  message: string;
  user: ClientUser;
}


interface UpdateUserResponse {
  message: string;
  user: ClientUser;
}


interface ClientUsersManagerProps {
  clientId: string;
  clientName: string;
}


interface CreateUserForm {
  email: string;
  password: string;
  role: string;
  is_active: boolean;
}


const initialForm: CreateUserForm = {
  email: "",
  password: "",
  role: "client_member",
  is_active: true,
};


function formatDate(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}


function roleLabel(
  role: string,
): string {
  if (role === "client_admin") {
    return "Client Admin";
  }

  if (role === "client_member") {
    return "Client Member";
  }

  return role;
}


export default function ClientUsersManager({
  clientId,
  clientName,
}: ClientUsersManagerProps) {
  const [
    users,
    setUsers,
  ] = useState<ClientUser[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");

  const [
    success,
    setSuccess,
  ] = useState("");

  const [
    showCreateForm,
    setShowCreateForm,
  ] = useState(false);

  const [
    creating,
    setCreating,
  ] = useState(false);

  const [
    busyUserId,
    setBusyUserId,
  ] = useState<number | null>(null);

  const [
    form,
    setForm,
  ] = useState<CreateUserForm>(
    initialForm,
  );


  // =========================================================
  // LOAD USERS
  // =========================================================

  const loadUsers = useCallback(
    async (
      showLoader = true,
    ) => {
      if (!clientId) {
        return;
      }

      if (showLoader) {
        setLoading(true);
      }

      setError("");

      try {
        const data =
          await apiFetch<UsersResponse>(
            `/api/v1/admin/clients/${clientId}/users`,
          );

        setUsers(data.users ?? []);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError(
            "Failed to load client users.",
          );
        }
      } finally {
        if (showLoader) {
          setLoading(false);
        }
      }
    },
    [clientId],
  );


  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);


  // =========================================================
  // FORM HELPERS
  // =========================================================

  function updateForm(
    field: keyof CreateUserForm,
    value: string | boolean,
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }


  function closeCreateForm() {
    if (creating) {
      return;
    }

    setShowCreateForm(false);
    setForm(initialForm);
    setError("");
  }


  // =========================================================
  // CREATE USER
  // =========================================================

  async function handleCreateUser(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError("");
    setSuccess("");

    const email =
      form.email.trim().toLowerCase();

    if (!email) {
      setError(
        "Email is required.",
      );
      return;
    }

    if (form.password.length < 8) {
      setError(
        "Password must contain at least 8 characters.",
      );
      return;
    }

    if (
      form.role !== "client_admin" &&
      form.role !== "client_member"
    ) {
      setError(
        "Invalid client role.",
      );
      return;
    }

    setCreating(true);

    try {
      const response =
        await apiFetch<CreateUserResponse>(
          `/api/v1/admin/clients/${clientId}/users`,
          {
            method: "POST",

            body: JSON.stringify({
              email,
              password: form.password,
              role: form.role,
              is_active: form.is_active,
            }),
          },
        );

      setUsers((current) => [
        ...current,
        response.user,
      ]);

      setSuccess(
        `${response.user.email} created successfully.`,
      );

      setForm(initialForm);
      setShowCreateForm(false);

      await loadUsers(false);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(
          "Failed to create user.",
        );
      }
    } finally {
      setCreating(false);
    }
  }


  // =========================================================
  // UPDATE USER
  // =========================================================

  async function updateUser(
    userId: number,
    payload: {
      role?: string;
      is_active?: boolean;
    },
  ) {
    setError("");
    setSuccess("");
    setBusyUserId(userId);

    try {
      const response =
        await apiFetch<UpdateUserResponse>(
          `/api/v1/admin/clients/${clientId}/users/${userId}`,
          {
            method: "PATCH",

            body: JSON.stringify(
              payload,
            ),
          },
        );

      setUsers((current) =>
        current.map((user) =>
          user.id === userId
            ? response.user
            : user,
        ),
      );

      setSuccess(
        `${response.user.email} updated successfully.`,
      );
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(
          "Failed to update user.",
        );
      }
    } finally {
      setBusyUserId(null);
    }
  }


  // =========================================================
  // CHANGE ROLE
  // =========================================================

  function handleRoleChange(
    user: ClientUser,
    newRole: string,
  ) {
    if (
      newRole !== "client_admin" &&
      newRole !== "client_member"
    ) {
      return;
    }

    if (newRole === user.role) {
      return;
    }

    void updateUser(
      user.id,
      {
        role: newRole,
      },
    );
  }


  // =========================================================
  // TOGGLE STATUS
  // =========================================================

  function handleToggleStatus(
    user: ClientUser,
  ) {
    void updateUser(
      user.id,
      {
        is_active:
          !user.is_active,
      },
    );
  }


  // =========================================================
  // LOADING
  // =========================================================

  if (loading) {
    return (
      <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
        <div className="animate-pulse">
          <div className="h-6 w-40 rounded bg-white/10" />

          <div className="mt-3 h-4 w-72 rounded bg-white/10" />

          <div className="mt-6 space-y-3">
            <div className="h-20 rounded-xl bg-white/5" />
            <div className="h-20 rounded-xl bg-white/5" />
          </div>
        </div>
      </section>
    );
  }


  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
      {/* HEADER */}

      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold text-white">
              Users & Access
            </h2>

            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-zinc-400">
              {users.length}{" "}
              {users.length === 1
                ? "user"
                : "users"}
            </span>
          </div>

          <p className="mt-2 text-sm text-zinc-400">
            Manage users who can access{" "}
            <span className="font-medium text-zinc-200">
              {clientName}
            </span>
            .
          </p>
        </div>

        <button
          type="button"
          onClick={() => {
            setError("");
            setSuccess("");
            setShowCreateForm(true);
          }}
          className="rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-black transition hover:bg-zinc-200"
        >
          + Add User
        </button>
      </div>


      {/* FEEDBACK */}

      {error && (
        <div className="mt-5 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {success && (
        <div className="mt-5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">
          {success}
        </div>
      )}


      {/* SECURITY INFORMATION */}

      <div className="mt-6 rounded-xl border border-blue-500/10 bg-blue-500/[0.05] p-4">
        <p className="text-sm font-medium text-blue-200">
          Tenant-secured access
        </p>

        <p className="mt-1 text-xs leading-5 text-zinc-400">
          Users created here are automatically
          assigned to this client. They cannot
          select or access another client profile.
        </p>
      </div>


      {/* USERS */}

      <div className="mt-6">
        {users.length === 0 ? (
          <div className="rounded-xl border border-dashed border-white/10 p-8 text-center">
            <p className="text-sm font-medium text-zinc-200">
              No users found
            </p>

            <p className="mt-2 text-sm text-zinc-500">
              Create the first user for this client.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {users.map((user) => {
              const isBusy =
                busyUserId === user.id;

              return (
                <div
                  key={user.id}
                  className="rounded-xl border border-white/10 bg-black/20 p-4"
                >
                  <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                    {/* USER INFO */}

                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="truncate font-medium text-white">
                          {user.email}
                        </p>

                        <span
                          className={
                            user.is_active
                              ? "rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-300"
                              : "rounded-full border border-zinc-500/20 bg-zinc-500/10 px-2.5 py-1 text-xs text-zinc-400"
                          }
                        >
                          {user.is_active
                            ? "Active"
                            : "Inactive"}
                        </span>
                      </div>

                      <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-zinc-500">
                        <span>
                          User ID: {user.id}
                        </span>

                        <span>
                          Client ID:{" "}
                          {user.client_profile_id}
                        </span>

                        <span>
                          Created:{" "}
                          {formatDate(
                            user.created_at,
                          )}
                        </span>
                      </div>
                    </div>


                    {/* ACTIONS */}

                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                      <div>
                        <label className="mb-1 block text-xs text-zinc-500">
                          Role
                        </label>

                        <select
                          value={user.role}
                          disabled={isBusy}
                          onChange={(event) => {
                            handleRoleChange(
                              user,
                              event.target.value,
                            );
                          }}
                          className="min-w-[160px] rounded-lg border border-white/10 bg-zinc-950 px-3 py-2 text-sm text-white outline-none transition focus:border-white/30 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          <option value="client_admin">
                            Client Admin
                          </option>

                          <option value="client_member">
                            Client Member
                          </option>
                        </select>
                      </div>


                      <div className="sm:pt-5">
                        <button
                          type="button"
                          disabled={isBusy}
                          onClick={() => {
                            handleToggleStatus(
                              user,
                            );
                          }}
                          className={
                            user.is_active
                              ? "min-w-[120px] rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-2 text-sm font-medium text-red-300 transition hover:bg-red-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                              : "min-w-[120px] rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-4 py-2 text-sm font-medium text-emerald-300 transition hover:bg-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                          }
                        >
                          {isBusy
                            ? "Updating..."
                            : user.is_active
                              ? "Deactivate"
                              : "Activate"}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>


      {/* CREATE USER MODAL */}

      {showCreateForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-zinc-950 p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-semibold text-white">
                  Add Client User
                </h3>

                <p className="mt-2 text-sm text-zinc-400">
                  Create access for{" "}
                  {clientName}.
                </p>
              </div>

              <button
                type="button"
                onClick={closeCreateForm}
                className="rounded-lg border border-white/10 px-3 py-1.5 text-sm text-zinc-400 transition hover:bg-white/5 hover:text-white"
              >
                Close
              </button>
            </div>


            <form
              onSubmit={handleCreateUser}
              className="mt-6 space-y-5"
            >
              {/* EMAIL */}

              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  Email
                </label>

                <input
                  type="email"
                  required
                  autoComplete="off"
                  placeholder="finance.manager@company.com"
                  value={form.email}
                  onChange={(event) => {
                    updateForm(
                      "email",
                      event.target.value,
                    );
                  }}
                  className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none placeholder:text-zinc-600 focus:border-white/30"
                />
              </div>


              {/* PASSWORD */}

              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  Temporary Password
                </label>

                <input
                  type="password"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  placeholder="Minimum 8 characters"
                  value={form.password}
                  onChange={(event) => {
                    updateForm(
                      "password",
                      event.target.value,
                    );
                  }}
                  className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none placeholder:text-zinc-600 focus:border-white/30"
                />

                <p className="mt-2 text-xs text-zinc-500">
                  The password is sent securely to the
                  backend and stored only as a hash.
                </p>
              </div>


              {/* ROLE */}

              <div>
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  Role
                </label>

                <select
                  value={form.role}
                  onChange={(event) => {
                    updateForm(
                      "role",
                      event.target.value,
                    );
                  }}
                  className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none focus:border-white/30"
                >
                  <option value="client_member">
                    Client Member
                  </option>

                  <option value="client_admin">
                    Client Admin
                  </option>
                </select>

                <div className="mt-3 rounded-lg border border-white/5 bg-white/[0.02] p-3 text-xs leading-5 text-zinc-500">
                  <strong className="text-zinc-300">
                    Client Admin:
                  </strong>{" "}
                  company-level administrator.
                  <br />

                  <strong className="text-zinc-300">
                    Client Member:
                  </strong>{" "}
                  regular company workspace user.
                </div>
              </div>


              {/* ACTIVE */}

              <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-white/10 bg-black/20 p-4">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(event) => {
                    updateForm(
                      "is_active",
                      event.target.checked,
                    );
                  }}
                  className="h-4 w-4"
                />

                <div>
                  <p className="text-sm font-medium text-zinc-200">
                    Activate User
                  </p>

                  <p className="mt-1 text-xs text-zinc-500">
                    Active users can authenticate
                    immediately.
                  </p>
                </div>
              </label>


              {/* ACTIONS */}

              <div className="flex justify-end gap-3 border-t border-white/10 pt-5">
                <button
                  type="button"
                  disabled={creating}
                  onClick={closeCreateForm}
                  className="rounded-xl border border-white/10 px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:bg-white/5 disabled:opacity-50"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={creating}
                  className="rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {creating
                    ? "Creating..."
                    : "Create User"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}
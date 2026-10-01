from pathlib import Path

from sqlalchemy import (
    MetaData,
    create_engine,
    func,
    inspect,
    select,
    text,
)

from app.core.database import DATABASE_URL


# ============================================================
# PATHS / CONNECTIONS
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]

SQLITE_PATH = BACKEND_DIR / "business_watchdog.db"

SQLITE_URL = f"sqlite:///{SQLITE_PATH.as_posix()}"

POSTGRES_URL = DATABASE_URL


# ============================================================
# TABLE COPY ORDER
# ============================================================

# Order is important because of foreign keys.
TABLES = [
    "client_profiles",
    "client_baselines",
    "users",
    "analyses",
    "findings",
    "alerts",
    "transactions",
]


# ============================================================
# HELPERS
# ============================================================

def print_header(title: str) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def get_table_count(connection, table) -> int:
    return connection.execute(
        select(func.count()).select_from(table)
    ).scalar_one()


def reset_postgres_sequence(
    connection,
    table_name: str,
) -> None:
    """
    Reset PostgreSQL SERIAL / identity sequence after
    inserting explicit IDs migrated from SQLite.
    """

    sequence_name = connection.execute(
        text(
            """
            SELECT pg_get_serial_sequence(
                :table_name,
                'id'
            )
            """
        ),
        {
            "table_name": table_name,
        },
    ).scalar_one_or_none()

    if not sequence_name:
        print(
            f"  Sequence: none for {table_name}"
        )
        return

    max_id = connection.execute(
        text(
            f'SELECT MAX(id) FROM "{table_name}"'
        )
    ).scalar_one()

    if max_id is None:
        connection.execute(
            text(
                """
                SELECT setval(
                    CAST(:sequence_name AS regclass),
                    1,
                    false
                )
                """
            ),
            {
                "sequence_name": sequence_name,
            },
        )

        print(
            f"  Sequence reset: {table_name} -> 1"
        )

        return

    connection.execute(
        text(
            """
            SELECT setval(
                CAST(:sequence_name AS regclass),
                :max_id,
                true
            )
            """
        ),
        {
            "sequence_name": sequence_name,
            "max_id": int(max_id),
        },
    )

    print(
        f"  Sequence reset: "
        f"{table_name} -> {max_id}"
    )


# ============================================================
# MAIN MIGRATION
# ============================================================

def main() -> None:
    print_header(
        "FinGuard SQLite -> PostgreSQL Migration"
    )

    print(
        f"SQLite source:\n{SQLITE_PATH}"
    )

    print(
        "\nPostgreSQL target:"
    )

    # Avoid printing database password.
    postgres_engine = create_engine(
        POSTGRES_URL,
    )

    print(
        postgres_engine.url.render_as_string(
            hide_password=True
        )
    )

    if not SQLITE_PATH.exists():
        raise RuntimeError(
            f"SQLite database not found: "
            f"{SQLITE_PATH}"
        )

    sqlite_engine = create_engine(
        SQLITE_URL,
    )

    # --------------------------------------------------------
    # Reflect schemas
    # --------------------------------------------------------

    sqlite_metadata = MetaData()
    postgres_metadata = MetaData()

    sqlite_metadata.reflect(
        bind=sqlite_engine,
    )

    postgres_metadata.reflect(
        bind=postgres_engine,
    )

    sqlite_tables = set(
        inspect(sqlite_engine).get_table_names()
    )

    postgres_tables = set(
        inspect(postgres_engine).get_table_names()
    )

    # --------------------------------------------------------
    # Validate required tables
    # --------------------------------------------------------

    print_header(
        "Checking Tables"
    )

    for table_name in TABLES:

        if table_name not in sqlite_tables:
            raise RuntimeError(
                f"Missing SQLite table: "
                f"{table_name}"
            )

        if table_name not in postgres_tables:
            raise RuntimeError(
                f"Missing PostgreSQL table: "
                f"{table_name}"
            )

        print(
            f"{table_name}: OK"
        )

    # --------------------------------------------------------
    # Safety check:
    # PostgreSQL should be empty before migration
    # --------------------------------------------------------

    print_header(
        "Checking PostgreSQL Target"
    )

    with postgres_engine.connect() as pg_conn:

        non_empty_tables = []

        for table_name in TABLES:

            table = postgres_metadata.tables[
                table_name
            ]

            count = get_table_count(
                pg_conn,
                table,
            )

            print(
                f"{table_name}: {count} rows"
            )

            if count > 0:
                non_empty_tables.append(
                    (
                        table_name,
                        count,
                    )
                )

        if non_empty_tables:

            details = ", ".join(
                f"{name}={count}"
                for name, count
                in non_empty_tables
            )

            raise RuntimeError(
                "\nPostgreSQL target is not empty.\n"
                "Migration aborted for safety.\n"
                f"Existing rows: {details}"
            )

    # --------------------------------------------------------
    # Perform migration in one PostgreSQL transaction
    # --------------------------------------------------------

    print_header(
        "Migrating Data"
    )

    migrated_counts = {}

    with sqlite_engine.connect() as sqlite_conn:

        with postgres_engine.begin() as pg_conn:

            for table_name in TABLES:

                source_table = (
                    sqlite_metadata.tables[
                        table_name
                    ]
                )

                target_table = (
                    postgres_metadata.tables[
                        table_name
                    ]
                )

                print(
                    f"\nMigrating: {table_name}"
                )

                # Columns existing in BOTH schemas.
                source_columns = {
                    column.name
                    for column
                    in source_table.columns
                }

                target_columns = {
                    column.name
                    for column
                    in target_table.columns
                }

                common_columns = [
                    column.name
                    for column
                    in source_table.columns
                    if column.name
                    in target_columns
                ]

                missing_in_target = (
                    source_columns
                    - target_columns
                )

                if missing_in_target:

                    print(
                        "  SQLite-only columns "
                        "ignored:",
                        sorted(
                            missing_in_target
                        ),
                    )

                rows = sqlite_conn.execute(
                    select(source_table)
                ).mappings().all()

                if not rows:

                    print(
                        "  0 rows"
                    )

                    migrated_counts[
                        table_name
                    ] = 0

                    continue

                payload = []

                for row in rows:

                    payload.append(
                        {
                            column:
                            row[column]
                            for column
                            in common_columns
                        }
                    )

                pg_conn.execute(
                    target_table.insert(),
                    payload,
                )

                migrated_counts[
                    table_name
                ] = len(payload)

                print(
                    f"  Migrated: "
                    f"{len(payload)} rows"
                )

            # ------------------------------------------------
            # Reset PostgreSQL sequences
            # ------------------------------------------------

            print_header(
                "Resetting PostgreSQL Sequences"
            )

            for table_name in TABLES:

                if "id" not in (
                    postgres_metadata
                    .tables[table_name]
                    .columns
                ):
                    continue

                reset_postgres_sequence(
                    pg_conn,
                    table_name,
                )

    # --------------------------------------------------------
    # Final verification
    # --------------------------------------------------------

    print_header(
        "Verification"
    )

    success = True

    with sqlite_engine.connect() as sqlite_conn:
        with postgres_engine.connect() as pg_conn:

            for table_name in TABLES:

                source_table = (
                    sqlite_metadata.tables[
                        table_name
                    ]
                )

                target_table = (
                    postgres_metadata.tables[
                        table_name
                    ]
                )

                sqlite_count = get_table_count(
                    sqlite_conn,
                    source_table,
                )

                postgres_count = get_table_count(
                    pg_conn,
                    target_table,
                )

                status = (
                    "PASS"
                    if sqlite_count
                    == postgres_count
                    else "FAIL"
                )

                if status == "FAIL":
                    success = False

                print(
                    f"{table_name:<20}"
                    f"SQLite={sqlite_count:<8}"
                    f"PostgreSQL={postgres_count:<8}"
                    f"{status}"
                )

    print_header(
        "Migration Result"
    )

    if not success:
        raise RuntimeError(
            "Migration completed but row-count "
            "verification failed."
        )

    print(
        "SQLite -> PostgreSQL migration "
        "completed successfully."
    )

    print()
    print(
        "The original SQLite database "
        "was not modified."
    )


if __name__ == "__main__":
    main()
import sqlite3

DB_PATH = "business_watchdog.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=== Current Alembic revision ===")
current_revision = cursor.execute(
    "SELECT version_num FROM alembic_version"
).fetchall()

print(current_revision)


print("\n=== Users table exists? ===")
users_table = cursor.execute(
    """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
      AND name = 'users'
    """
).fetchall()

print(users_table)


if users_table:
    print(
        "\nSTOP: users table already exists."
        "\nDo not change the Alembic revision automatically."
    )

else:
    print("\nUsers table does not exist.")
    print("Fixing Alembic revision...")

    cursor.execute(
        """
        UPDATE alembic_version
        SET version_num = ?
        """,
        ("5ac78b4b3aac",),
    )

    conn.commit()

    new_revision = cursor.execute(
        "SELECT version_num FROM alembic_version"
    ).fetchall()

    print("\n=== New Alembic revision ===")
    print(new_revision)


conn.close()
from getpass import getpass

# Load all SQLAlchemy models before any ORM query.
from app.models.alert import Alert  # noqa: F401
from app.models.analysis import Analysis  # noqa: F401
from app.models.client_baseline import ClientBaseline  # noqa: F401
from app.models.client_profile import ClientProfile  # noqa: F401
from app.models.finding import Finding  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.user import User  # noqa: F401

from sqlalchemy.orm import configure_mappers

from app.core.database import SessionLocal
from app.services.auth_service import create_user


VALID_ROLES = {
    "platform_admin",
    "client_admin",
    "client_member",
}


def main() -> None:
    # Force SQLAlchemy to validate all model relationships now.
    configure_mappers()

    print("\n=== FinGuard User Creation ===\n")

    email = input("Email: ").strip()
    password = getpass("Password: ")

    role = input(
        "Role [platform_admin/client_admin/client_member]: "
    ).strip()

    if role not in VALID_ROLES:
        print("\nERROR: Invalid role.")
        return

    client_profile_id = None

    if role != "platform_admin":
        raw_client_id = input(
            "Client profile ID: "
        ).strip()

        try:
            client_profile_id = int(raw_client_id)
        except ValueError:
            print(
                "\nERROR: Client profile ID must be an integer."
            )
            return

    db = SessionLocal()

    try:
        user = create_user(
            db,
            email=email,
            password=password,
            role=role,
            client_profile_id=client_profile_id,
        )

        print("\nUser created successfully.")
        print(f"ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Role: {user.role}")
        print(
            f"Client profile ID: "
            f"{user.client_profile_id}"
        )

    except Exception as exc:
        db.rollback()
        print(
            f"\nERROR: {type(exc).__name__}: {exc}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()
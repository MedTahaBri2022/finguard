from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.database import Base, DATABASE_URL

# Import all models so SQLAlchemy registers them
# inside Base.metadata for Alembic.
from app.models.alert import Alert
from app.models.analysis import Analysis
from app.models.client_baseline import ClientBaseline
from app.models.client_profile import ClientProfile
from app.models.finding import Finding
from app.models.transaction import Transaction
from app.models.user import User


# Alembic Config object
config = context.config


# ---------------------------------------------------------
# Use the same DATABASE_URL as the FastAPI application
# ---------------------------------------------------------

config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL.replace("%", "%%"),
)


# Configure Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# SQLAlchemy metadata used by Alembic
target_metadata = Base.metadata


# ---------------------------------------------------------
# Offline migrations
# ---------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Run migrations without creating a database connection.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------
# Online migrations
# ---------------------------------------------------------

def run_migrations_online() -> None:
    """
    Run migrations using a real database connection.
    """

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------
# Alembic entry point
# ---------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
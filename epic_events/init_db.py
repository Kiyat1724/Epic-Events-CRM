from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from epic_events.database import engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_CONFIG_PATH = PROJECT_ROOT / "alembic.ini"

EXPECTED_TABLES: set[str] = {
    "roles",
    "employees",
    "clients",
    "contracts",
    "events",
}


def initialize_database() -> None:
    """Apply every migration and verify the expected database tables."""

    alembic_config = Config(str(ALEMBIC_CONFIG_PATH))
    command.upgrade(
        alembic_config,
        "head",
    )

    inspector = inspect(engine)
    created_tables = set(inspector.get_table_names())
    missing_tables = EXPECTED_TABLES - created_tables

    if missing_tables:
        missing_names = ", ".join(sorted(missing_tables))
        raise RuntimeError(f"Missing database tables: {missing_names}")

    table_names = ", ".join(sorted(EXPECTED_TABLES))
    print("Database migrations applied successfully: " f"{table_names}")


if __name__ == "__main__":
    initialize_database()

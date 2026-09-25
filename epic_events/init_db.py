from sqlalchemy import inspect

from epic_events.database import Base, engine
from epic_events.models import Client, Contract, Employee, Event, Role

MODEL_CLASSES = (
    Role,
    Employee,
    Client,
    Contract,
    Event,
)

EXPECTED_TABLES: set[str] = {model_class.__tablename__ for model_class in MODEL_CLASSES}


def initialize_database() -> None:
    """Create all database tables and verify their existence."""

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    created_tables = set(inspector.get_table_names())
    missing_tables = EXPECTED_TABLES - created_tables

    if missing_tables:
        missing_names = ", ".join(sorted(missing_tables))
        raise RuntimeError(f"Missing database tables: {missing_names}")

    table_names = ", ".join(sorted(created_tables))
    print(f"Database initialized successfully: {table_names}")


if __name__ == "__main__":
    initialize_database()

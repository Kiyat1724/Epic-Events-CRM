from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy import event as sqlalchemy_event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from epic_events import models


@pytest.fixture
def database_session() -> Generator[Session, None, None]:
    """Provide an isolated in-memory database for one integration test."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    @sqlalchemy_event.listens_for(engine, "connect")
    def enable_foreign_keys(
        database_connection,
        connection_record,
    ) -> None:
        """Enable foreign-key constraints in SQLite."""

        cursor = database_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    models.Role.metadata.create_all(engine)

    with Session(engine) as session:
        yield session
        session.rollback()

    models.Role.metadata.drop_all(engine)
    engine.dispose()

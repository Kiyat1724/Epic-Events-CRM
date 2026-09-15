from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from epic_events.config import settings


class Base(DeclarativeBase):
    """Base class inherited by all SQLAlchemy models."""

    pass


database_url = URL.create(
    drivername="postgresql+psycopg",
    username=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
)


engine: Engine = create_engine(
    database_url,
    echo=False,
    pool_pre_ping=True,
)


session_factory: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional database session."""
    session = session_factory()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_database_connection() -> None:
    """Check that the application can communicate with PostgreSQL."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

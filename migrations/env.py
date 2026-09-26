from logging.config import fileConfig

from alembic import context

from epic_events import models
from epic_events.database import database_url, engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = models.Role.metadata


def run_migrations_offline() -> None:
    """Generate migration SQL without opening a database connection."""

    context.configure(
        url=database_url.render_as_string(
            hide_password=False,
        ),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using the application database engine."""

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

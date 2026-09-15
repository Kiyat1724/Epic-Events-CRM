import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


load_dotenv()


def get_required_env(name: str) -> str:
    """Return a required environment variable or raise an explicit error."""
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"The required environment variable {name} is missing."
        )

    return value


@dataclass(frozen=True, slots=True)
class Settings:
    """Store the application configuration loaded from environment variables."""

    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str = field(repr=False)
    jwt_secret: str | None = field(default=None, repr=False)
    sentry_dsn: str | None = field(default=None, repr=False)

    @classmethod
    def from_env(cls) -> "Settings":
        """Create the settings from environment variables."""
        port_value = os.getenv("DB_PORT", "5432")

        try:
            db_port = int(port_value)
        except ValueError as error:
            raise RuntimeError("DB_PORT must be an integer.") from error

        return cls(
            db_host=get_required_env("DB_HOST"),
            db_port=db_port,
            db_name=get_required_env("DB_NAME"),
            db_user=get_required_env("DB_USER"),
            db_password=get_required_env("DB_PASSWORD"),
            jwt_secret=os.getenv("JWT_SECRET") or None,
            sentry_dsn=os.getenv("SENTRY_DSN") or None,
        )


settings = Settings.from_env()

import sentry_sdk

from epic_events.config import settings


def initialize_sentry() -> bool:
    """Initialize Sentry when a DSN is configured."""

    if not settings.sentry_dsn:
        return False

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        send_default_pii=False,
        traces_sample_rate=0.0,
    )

    return True

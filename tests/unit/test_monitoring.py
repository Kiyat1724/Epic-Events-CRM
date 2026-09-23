from types import SimpleNamespace
from unittest.mock import patch

from epic_events import monitoring


def test_initialize_sentry_returns_false_without_dsn(
    monkeypatch,
) -> None:
    """Do not initialize Sentry when no DSN is configured."""

    fake_settings = SimpleNamespace(sentry_dsn=None)
    monkeypatch.setattr(
        monitoring,
        "settings",
        fake_settings,
    )

    with patch("epic_events.monitoring.sentry_sdk.init") as sentry_init:
        initialized = monitoring.initialize_sentry()

    assert initialized is False
    sentry_init.assert_not_called()


def test_initialize_sentry_uses_secure_configuration(
    monkeypatch,
) -> None:
    """Initialize Sentry without automatically sending personal data."""

    fake_settings = SimpleNamespace(
        sentry_dsn="https://public@example.ingest.sentry.io/123",
    )
    monkeypatch.setattr(
        monitoring,
        "settings",
        fake_settings,
    )

    with patch("epic_events.monitoring.sentry_sdk.init") as sentry_init:
        initialized = monitoring.initialize_sentry()

    assert initialized is True
    sentry_init.assert_called_once_with(
        dsn="https://public@example.ingest.sentry.io/123",
        send_default_pii=False,
        traces_sample_rate=0.0,
    )

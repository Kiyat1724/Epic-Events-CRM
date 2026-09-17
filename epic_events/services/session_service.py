from pathlib import Path
from epic_events.services.jwt_service import (
    AuthenticationError,
    TokenPayload,
    decode_access_token,
)

SESSION_DIRECTORY = Path.home() / ".epic_events_crm"
SESSION_FILE = SESSION_DIRECTORY / "session.jwt"


def save_session_token(
    token: str,
    *,
    session_file: Path = SESSION_FILE,
) -> None:
    """Store a JWT locally using an atomic file replacement."""

    normalized_token = token.strip()
    if not normalized_token:
        raise ValueError("The session token cannot be empty.")

    session_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_file = session_file.with_suffix(".tmp")
    temporary_file.write_text(
        normalized_token,
        encoding="utf-8",
    )
    temporary_file.chmod(0o600)
    temporary_file.replace(session_file)
    session_file.chmod(0o600)


def load_session_token(
    *,
    session_file: Path = SESSION_FILE,
) -> str | None:
    """Return the stored JWT, or None when no session exists."""

    if not session_file.exists():
        return None

    token = session_file.read_text(encoding="utf-8").strip()
    return token or None


def delete_session_token(
    *,
    session_file: Path = SESSION_FILE,
) -> bool:
    """Delete the local JWT and return whether a session existed."""

    if not session_file.exists():
        return False

    session_file.unlink()
    return True


def get_current_identity() -> TokenPayload:
    """Return the validated identity stored in the local session."""

    token = load_session_token()
    if token is None:
        raise AuthenticationError("Authentication is required. Use the login command.")

    try:
        return decode_access_token(token)
    except AuthenticationError:
        delete_session_token()
        raise

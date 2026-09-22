from pathlib import Path

import pytest

from epic_events.services.session_service import (
    delete_session_token,
    load_session_token,
    save_session_token,
)


def test_save_and_load_session_token(tmp_path: Path) -> None:
    session_file = tmp_path / "session.jwt"

    save_session_token(
        "signed-jwt-token",
        session_file=session_file,
    )

    assert (
        load_session_token(
            session_file=session_file,
        )
        == "signed-jwt-token"
    )


def test_save_session_token_rejects_empty_token(tmp_path: Path) -> None:
    session_file = tmp_path / "session.jwt"

    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        save_session_token(
            "   ",
            session_file=session_file,
        )


def test_load_session_token_returns_none_when_missing(
    tmp_path: Path,
) -> None:
    session_file = tmp_path / "session.jwt"

    assert load_session_token(session_file=session_file) is None


def test_delete_session_token_removes_existing_session(
    tmp_path: Path,
) -> None:
    session_file = tmp_path / "session.jwt"
    save_session_token(
        "signed-jwt-token",
        session_file=session_file,
    )

    deleted = delete_session_token(session_file=session_file)

    assert deleted is True
    assert session_file.exists() is False


def test_delete_session_token_returns_false_when_missing(
    tmp_path: Path,
) -> None:
    session_file = tmp_path / "session.jwt"

    assert delete_session_token(session_file=session_file) is False

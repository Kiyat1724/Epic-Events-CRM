from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from click.testing import CliRunner

from epic_events.cli.auth_commands import login, logout, status
from epic_events.services.auth_service import InvalidCredentialsError
from epic_events.services.jwt_service import AuthenticationError


def test_login_authenticates_and_saves_session_token() -> None:
    """Authenticate an employee and persist the generated token."""

    runner = CliRunner()
    database_context = MagicMock()
    database_session = Mock()
    database_context.return_value.__enter__.return_value = database_session

    employee = SimpleNamespace(
        id=1,
        full_name="Alice Manager",
        email="alice@example.com",
        role=SimpleNamespace(name="management"),
    )

    with (
        patch(
            "epic_events.cli.auth_commands.session_scope",
            database_context,
        ),
        patch(
            "epic_events.cli.auth_commands.authenticate_employee",
            return_value=employee,
        ) as authenticate_employee,
        patch(
            "epic_events.cli.auth_commands.create_access_token",
            return_value="secure-token",
        ) as create_access_token,
        patch(
            "epic_events.cli.auth_commands.save_session_token",
        ) as save_session_token,
    ):
        result = runner.invoke(
            login,
            input="alice@example.com\nSecurePassword123!\n",
        )

    assert result.exit_code == 0
    assert "Login successful. Welcome Alice Manager (management)." in result.output
    authenticate_employee.assert_called_once()
    assert authenticate_employee.call_args.kwargs["email"] == "alice@example.com"
    assert authenticate_employee.call_args.kwargs["password"] == "SecurePassword123!"
    create_access_token.assert_called_once_with(employee)
    save_session_token.assert_called_once_with("secure-token")


def test_login_rejects_invalid_credentials() -> None:
    """Display a safe error when authentication fails."""

    runner = CliRunner()
    database_context = MagicMock()
    database_context.return_value.__enter__.return_value = Mock()

    with (
        patch(
            "epic_events.cli.auth_commands.session_scope",
            database_context,
        ),
        patch(
            "epic_events.cli.auth_commands.authenticate_employee",
            side_effect=InvalidCredentialsError("Invalid email or password."),
        ),
        patch(
            "epic_events.cli.auth_commands.save_session_token",
        ) as save_session_token,
    ):
        result = runner.invoke(
            login,
            input="unknown@example.com\nWrongPassword123!\n",
        )

    assert result.exit_code == 1
    assert "Error: Invalid email or password." in result.output
    save_session_token.assert_not_called()


def test_status_displays_authenticated_identity() -> None:
    """Display the identity stored in a valid session token."""

    runner = CliRunner()
    expires_at = datetime(
        2026,
        10,
        10,
        18,
        0,
        tzinfo=timezone.utc,
    )
    payload = SimpleNamespace(
        employee_id=1,
        email="alice@example.com",
        role="management",
        expires_at=expires_at,
    )

    with (
        patch(
            "epic_events.cli.auth_commands.load_session_token",
            return_value="secure-token",
        ),
        patch(
            "epic_events.cli.auth_commands.decode_access_token",
            return_value=payload,
        ),
    ):
        result = runner.invoke(status)

    assert result.exit_code == 0
    assert "Employee ID: 1" in result.output
    assert "Email: alice@example.com" in result.output
    assert "Role: management" in result.output
    assert expires_at.isoformat() in result.output


def test_status_rejects_missing_session() -> None:
    """Display an error when no local session exists."""

    runner = CliRunner()

    with patch(
        "epic_events.cli.auth_commands.load_session_token",
        return_value=None,
    ):
        result = runner.invoke(status)

    assert result.exit_code == 1
    assert "No active session. Use the login command." in result.output


def test_status_deletes_invalid_session() -> None:
    """Delete an expired or invalid local token."""

    runner = CliRunner()

    with (
        patch(
            "epic_events.cli.auth_commands.load_session_token",
            return_value="expired-token",
        ),
        patch(
            "epic_events.cli.auth_commands.decode_access_token",
            side_effect=AuthenticationError("The authentication token has expired."),
        ),
        patch(
            "epic_events.cli.auth_commands.delete_session_token",
        ) as delete_session_token,
    ):
        result = runner.invoke(status)

    assert result.exit_code == 1
    assert "Error: The authentication token has expired." in result.output
    delete_session_token.assert_called_once_with()


def test_logout_deletes_existing_session() -> None:
    """Delete an existing local session."""

    runner = CliRunner()

    with patch(
        "epic_events.cli.auth_commands.delete_session_token",
        return_value=True,
    ):
        result = runner.invoke(logout)

    assert result.exit_code == 0
    assert "Logout successful." in result.output


def test_logout_reports_missing_session() -> None:
    """Report that there is no session to delete."""

    runner = CliRunner()

    with patch(
        "epic_events.cli.auth_commands.delete_session_token",
        return_value=False,
    ):
        result = runner.invoke(logout)

    assert result.exit_code == 0
    assert "No active session." in result.output

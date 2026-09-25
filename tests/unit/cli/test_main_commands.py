import pytest
from click.testing import CliRunner

from main import cli


def test_main_help_displays_every_command_group() -> None:
    """Display every main application command."""

    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["--help"],
    )

    assert result.exit_code == 0
    assert "bootstrap-admin" in result.output
    assert "clients" in result.output
    assert "contracts" in result.output
    assert "employees" in result.output
    assert "events" in result.output
    assert "login" in result.output
    assert "logout" in result.output
    assert "status" in result.output


@pytest.mark.parametrize(
    ("command_name", "expected_description"),
    [
        ("clients", "Manage Epic Events clients."),
        ("contracts", "Manage Epic Events contracts."),
        ("employees", "Manage Epic Events employees."),
        ("events", "Manage Epic Events events."),
    ],
)
def test_resource_command_help_is_available(
    command_name: str,
    expected_description: str,
) -> None:
    """Display the help of every resource command group."""

    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            command_name,
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert expected_description in result.output


@pytest.mark.parametrize(
    "command_name",
    [
        "bootstrap-admin",
        "login",
        "logout",
        "status",
    ],
)
def test_standalone_command_help_is_available(
    command_name: str,
) -> None:
    """Display the help of each standalone command."""

    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            command_name,
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "Options:" in result.output


def test_hello_command_confirms_application_is_running() -> None:
    """Run the public application health command."""

    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["hello"],
    )

    assert result.exit_code == 0
    assert result.output == "Epic Events CRM is running.\n"

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from epic_events.cli.client_commands import clients
from epic_events.cli.contract_commands import contracts
from epic_events.cli.employee_commands import employees
from epic_events.cli.event_commands import events


def make_database_context() -> MagicMock:
    """Create a simulated database context manager."""

    context = MagicMock()
    context.return_value.__enter__.return_value = Mock()
    return context


def make_identity(
    *,
    employee_id: int = 1,
    role: str = "management",
) -> SimpleNamespace:
    """Create a lightweight authenticated identity."""

    return SimpleNamespace(
        employee_id=employee_id,
        email="employee@example.com",
        role=role,
    )


def make_client() -> SimpleNamespace:
    """Create a client displayed by CLI commands."""

    return SimpleNamespace(
        id=1,
        full_name="Kevin Casey",
        email="kevin@example.com",
        phone="+33 6 12 34 56 78",
        company_name="Secure Company",
        sales_contact_id=2,
        created_at=datetime(
            2026,
            9,
            20,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        updated_at=None,
    )


def make_contract() -> SimpleNamespace:
    """Create a contract displayed by CLI commands."""

    return SimpleNamespace(
        id=1,
        client_id=1,
        client=SimpleNamespace(
            full_name="Kevin Casey",
            sales_contact_id=2,
        ),
        total_amount=Decimal("5000.00"),
        remaining_amount=Decimal("3500.00"),
        created_at=datetime(
            2026,
            9,
            21,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        signed=True,
    )


def make_employee() -> SimpleNamespace:
    """Create an employee displayed by CLI commands."""

    return SimpleNamespace(
        id=3,
        employee_number="SUP-2026",
        full_name="Anne Fox",
        email="anne@example.com",
        role=SimpleNamespace(name="support"),
    )


def make_event() -> SimpleNamespace:
    """Create an event displayed by CLI commands."""

    return SimpleNamespace(
        id=1,
        contract_id=1,
        name="Cybersecurity Conference",
        start_date=datetime(
            2026,
            10,
            10,
            14,
            0,
            tzinfo=timezone.utc,
        ),
        end_date=datetime(
            2026,
            10,
            10,
            18,
            0,
            tzinfo=timezone.utc,
        ),
        location="Lyon",
        attendees=150,
        notes="Annual customer event.",
        support_contact_id=3,
    )


def test_clients_list_displays_clients() -> None:
    """Display all clients returned by the service."""

    runner = CliRunner()
    service = Mock()
    service.list_clients.return_value = [make_client()]

    with (
        patch(
            "epic_events.cli.client_commands." "get_authenticated_identity",
            return_value=make_identity(role="sales"),
        ),
        patch(
            "epic_events.cli.client_commands.session_scope",
            make_database_context(),
        ),
        patch(
            "epic_events.cli.client_commands.ClientService",
            return_value=service,
        ),
    ):
        result = runner.invoke(
            clients,
            ["list"],
        )

    assert result.exit_code == 0
    assert "Kevin Casey" in result.output
    assert "Secure Company" in result.output
    service.list_clients.assert_called_once_with()


def test_clients_show_displays_one_client() -> None:
    """Display one client returned by the service."""

    runner = CliRunner()
    service = Mock()
    service.get_client.return_value = make_client()

    with (
        patch(
            "epic_events.cli.client_commands." "get_authenticated_identity",
            return_value=make_identity(role="sales"),
        ),
        patch(
            "epic_events.cli.client_commands.session_scope",
            make_database_context(),
        ),
        patch(
            "epic_events.cli.client_commands.ClientService",
            return_value=service,
        ),
    ):
        result = runner.invoke(
            clients,
            [
                "show",
                "1",
            ],
        )

    assert result.exit_code == 0
    assert "ID: 1" in result.output
    assert "kevin@example.com" in result.output
    service.get_client.assert_called_once_with(
        client_id=1,
    )


@pytest.mark.parametrize(
    (
        "command_name",
        "service_method_name",
    ),
    [
        ("list", "list_contracts"),
        ("unsigned", "list_unsigned_contracts"),
        ("unpaid", "list_unpaid_contracts"),
    ],
)
def test_contract_collection_commands_display_contracts(
    command_name: str,
    service_method_name: str,
) -> None:
    """Display contracts for every available collection filter."""

    runner = CliRunner()
    service = Mock()
    service_method = getattr(
        service,
        service_method_name,
    )
    service_method.return_value = [make_contract()]

    with (
        patch(
            "epic_events.cli.contract_commands." "get_authenticated_identity",
            return_value=make_identity(role="management"),
        ),
        patch(
            "epic_events.cli.contract_commands.session_scope",
            make_database_context(),
        ),
        patch(
            "epic_events.cli.contract_commands.build_service",
            return_value=service,
        ),
    ):
        result = runner.invoke(
            contracts,
            [command_name],
        )

    assert result.exit_code == 0
    assert "Total amount: 5000.00" in result.output
    assert "Kevin Casey" in result.output
    service_method.assert_called_once()


def test_contracts_show_displays_one_contract() -> None:
    """Display one contract returned by the service."""

    runner = CliRunner()
    service = Mock()
    service.get_contract.return_value = make_contract()

    with (
        patch(
            "epic_events.cli.contract_commands." "get_authenticated_identity",
            return_value=make_identity(),
        ),
        patch(
            "epic_events.cli.contract_commands.session_scope",
            make_database_context(),
        ),
        patch(
            "epic_events.cli.contract_commands.build_service",
            return_value=service,
        ),
    ):
        result = runner.invoke(
            contracts,
            [
                "show",
                "1",
            ],
        )

    assert result.exit_code == 0
    assert "Remaining amount: 3500.00" in result.output
    assert "Signed: True" in result.output
    service.get_contract.assert_called_once_with(
        contract_id=1,
    )


def test_employees_list_displays_employees() -> None:
    """Display all employees returned to a manager."""

    runner = CliRunner()
    identity = make_identity()
    service = Mock()
    service.list_employees.return_value = [make_employee()]

    with (
        patch(
            "epic_events.cli.employee_commands." "get_authenticated_manager",
            return_value=identity,
        ),
        patch(
            "epic_events.cli.employee_commands.session_scope",
            make_database_context(),
        ),
        patch(
            "epic_events.cli.employee_commands." "build_employee_service",
            return_value=service,
        ),
    ):
        result = runner.invoke(
            employees,
            ["list"],
        )

    assert result.exit_code == 0
    assert "Anne Fox" in result.output
    assert "Role: support" in result.output
    assert "password" not in result.output.lower()
    service.list_employees.assert_called_once_with(identity)


def test_employees_show_displays_one_employee() -> None:
    """Display one employee returned to a manager."""

    runner = CliRunner()
    identity = make_identity()
    service = Mock()
    service.get_employee.return_value = make_employee()

    with (
        patch(
            "epic_events.cli.employee_commands." "get_authenticated_manager",
            return_value=identity,
        ),
        patch(
            "epic_events.cli.employee_commands.session_scope",
            make_database_context(),
        ),
        patch(
            "epic_events.cli.employee_commands." "build_employee_service",
            return_value=service,
        ),
    ):
        result = runner.invoke(
            employees,
            [
                "show",
                "3",
            ],
        )

    assert result.exit_code == 0
    assert "Employee number: SUP-2026" in result.output
    assert "anne@example.com" in result.output
    service.get_employee.assert_called_once_with(
        identity,
        employee_id=3,
    )


@pytest.mark.parametrize(
    (
        "command_name",
        "service_method_name",
        "role_name",
    ),
    [
        ("list", "list_events", "management"),
        (
            "without-support",
            "list_events_without_support",
            "management",
        ),
        (
            "assigned",
            "list_assigned_events",
            "support",
        ),
    ],
)
def test_event_collection_commands_display_events(
    command_name: str,
    service_method_name: str,
    role_name: str,
) -> None:
    """Display events for every available collection filter."""

    runner = CliRunner()
    identity = make_identity(
        employee_id=3,
        role=role_name,
    )
    service = Mock()
    service_method = getattr(
        service,
        service_method_name,
    )
    service_method.return_value = [make_event()]

    with (
        patch(
            "epic_events.cli.event_commands." "get_authenticated_identity",
            return_value=identity,
        ),
        patch(
            "epic_events.cli.event_commands.session_scope",
            make_database_context(),
        ),
        patch(
            "epic_events.cli.event_commands." "build_event_service",
            return_value=service,
        ),
    ):
        result = runner.invoke(
            events,
            [command_name],
        )

    assert result.exit_code == 0
    assert "Cybersecurity Conference" in result.output
    assert "Attendees: 150" in result.output

    if command_name == "list":
        service_method.assert_called_once_with()
    else:
        service_method.assert_called_once_with(identity)


def test_events_show_displays_one_event() -> None:
    """Display one event returned by the service."""

    runner = CliRunner()
    service = Mock()
    service.get_event.return_value = make_event()

    with (
        patch(
            "epic_events.cli.event_commands." "get_authenticated_identity",
            return_value=make_identity(role="support"),
        ),
        patch(
            "epic_events.cli.event_commands.session_scope",
            make_database_context(),
        ),
        patch(
            "epic_events.cli.event_commands." "build_event_service",
            return_value=service,
        ),
    ):
        result = runner.invoke(
            events,
            [
                "show",
                "1",
            ],
        )

    assert result.exit_code == 0
    assert "Location: Lyon" in result.output
    assert "Support contact ID: 3" in result.output
    service.get_event.assert_called_once_with(
        event_id=1,
    )

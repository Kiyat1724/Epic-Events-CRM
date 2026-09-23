from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest

from epic_events.models import Client, Contract, Employee, Event
from epic_events.repositories.contract_repository import ContractRepository
from epic_events.repositories.employee_repository import EmployeeRepository
from epic_events.repositories.event_repository import EventRepository
from epic_events.services.event_service import (
    EventAlreadyExistsError,
    EventContractNotFoundError,
    EventNotFoundError,
    EventService,
    InvalidSupportRoleError,
    SupportEmployeeNotFoundError,
)
from epic_events.services.jwt_service import TokenPayload
from epic_events.services.permission_service import PermissionDeniedError


def make_identity(
    *,
    employee_id: int,
    role: str,
) -> Mock:
    """Create a simulated authenticated identity."""

    identity = Mock(spec=TokenPayload)
    identity.employee_id = employee_id
    identity.role = role
    return identity


def make_contract(
    *,
    sales_contact_id: int = 2,
    signed: bool = True,
) -> Contract:
    """Create a contract associated with a salesperson."""

    client = Client(
        full_name="Kevin Casey",
        email="kevin@startup.io",
        phone="+33 6 12 34 56 77",
        company_name="Cool IT SECU",
        sales_contact_id=sales_contact_id,
    )

    return Contract(
        id=1,
        client_id=1,
        client=client,
        total_amount=Decimal("5000.00"),
        remaining_amount=Decimal("3500.00"),
        signed=signed,
    )


def make_event(
    *,
    support_contact_id: int | None = 3,
) -> Event:
    """Create an event used by the service tests."""

    start_date = datetime(
        2026,
        10,
        10,
        14,
        0,
        tzinfo=timezone.utc,
    )

    return Event(
        id=1,
        contract_id=1,
        name="Cybersecurity Conference",
        start_date=start_date,
        end_date=start_date + timedelta(hours=4),
        location="Lyon",
        attendees=100,
        notes="Annual customer event.",
        support_contact_id=support_contact_id,
    )


def build_service() -> tuple[
    EventService,
    Mock,
    Mock,
    Mock,
]:
    """Create the service with simulated repositories."""

    event_repository = Mock(spec=EventRepository)
    contract_repository = Mock(spec=ContractRepository)
    employee_repository = Mock(spec=EmployeeRepository)

    event_repository.add.side_effect = lambda event: event
    event_repository.save.side_effect = lambda event: event

    service = EventService(
        event_repository,
        contract_repository,
        employee_repository,
    )

    return (
        service,
        event_repository,
        contract_repository,
        employee_repository,
    )


def test_list_events_returns_every_event() -> None:
    service, event_repository, _, _ = build_service()
    expected_events = [make_event()]
    event_repository.list_all.return_value = expected_events

    events = service.list_events()

    assert events == expected_events
    event_repository.list_all.assert_called_once_with()


def test_management_can_list_events_without_support() -> None:
    service, event_repository, _, _ = build_service()
    identity = make_identity(
        employee_id=1,
        role="management",
    )
    expected_events = [make_event(support_contact_id=None)]
    event_repository.list_without_support.return_value = expected_events

    events = service.list_events_without_support(identity)

    assert events == expected_events
    event_repository.list_without_support.assert_called_once_with()


def test_sales_cannot_list_events_without_support() -> None:
    service, event_repository, _, _ = build_service()
    identity = make_identity(
        employee_id=2,
        role="sales",
    )

    with pytest.raises(PermissionDeniedError):
        service.list_events_without_support(identity)

    event_repository.list_without_support.assert_not_called()


def test_support_can_list_assigned_events() -> None:
    service, event_repository, _, _ = build_service()
    identity = make_identity(
        employee_id=3,
        role="support",
    )
    expected_events = [make_event(support_contact_id=3)]
    event_repository.list_assigned_to.return_value = expected_events

    events = service.list_assigned_events(identity)

    assert events == expected_events
    event_repository.list_assigned_to.assert_called_once_with(3)


def test_get_event_rejects_unknown_event() -> None:
    service, event_repository, _, _ = build_service()
    event_repository.get_by_id.return_value = None

    with pytest.raises(EventNotFoundError):
        service.get_event(event_id=999)


def test_sales_can_create_event_for_own_signed_contract() -> None:
    service, event_repository, contract_repository, _ = build_service()
    identity = make_identity(
        employee_id=2,
        role="sales",
    )
    contract = make_contract(
        sales_contact_id=2,
        signed=True,
    )
    contract_repository.get_by_id.return_value = contract
    event_repository.get_by_contract_id.return_value = None

    start_date = datetime(
        2026,
        10,
        10,
        14,
        0,
        tzinfo=timezone.utc,
    )
    end_date = start_date + timedelta(hours=4)

    event = service.create_event(
        identity,
        contract_id=1,
        name=" Cybersecurity Conference ",
        start_date=start_date,
        end_date=end_date,
        location=" Lyon ",
        attendees=100,
        notes=" Annual customer event. ",
    )

    assert event.contract_id == 1
    assert event.name == "Cybersecurity Conference"
    assert event.location == "Lyon"
    assert event.attendees == 100
    assert event.notes == "Annual customer event."
    assert event.support_contact_id is None
    event_repository.add.assert_called_once_with(event)


def test_create_event_rejects_unknown_contract() -> None:
    service, event_repository, contract_repository, _ = build_service()
    identity = make_identity(
        employee_id=2,
        role="sales",
    )
    contract_repository.get_by_id.return_value = None

    start_date = datetime.now(timezone.utc)

    with pytest.raises(EventContractNotFoundError):
        service.create_event(
            identity,
            contract_id=999,
            name="Conference",
            start_date=start_date,
            end_date=start_date + timedelta(hours=2),
            location="Lyon",
            attendees=50,
            notes=None,
        )

    event_repository.add.assert_not_called()


def test_create_event_rejects_unsigned_contract() -> None:
    service, event_repository, contract_repository, _ = build_service()
    identity = make_identity(
        employee_id=2,
        role="sales",
    )
    contract_repository.get_by_id.return_value = make_contract(
        sales_contact_id=2,
        signed=False,
    )

    start_date = datetime.now(timezone.utc)

    with pytest.raises(
        ValueError,
        match="An event can only be created for a signed contract.",
    ):
        service.create_event(
            identity,
            contract_id=1,
            name="Conference",
            start_date=start_date,
            end_date=start_date + timedelta(hours=2),
            location="Lyon",
            attendees=50,
            notes=None,
        )

    event_repository.add.assert_not_called()


def test_create_event_rejects_existing_contract_event() -> None:
    service, event_repository, contract_repository, _ = build_service()
    identity = make_identity(
        employee_id=2,
        role="sales",
    )
    contract_repository.get_by_id.return_value = make_contract()
    event_repository.get_by_contract_id.return_value = make_event()

    start_date = datetime.now(timezone.utc)

    with pytest.raises(EventAlreadyExistsError):
        service.create_event(
            identity,
            contract_id=1,
            name="Conference",
            start_date=start_date,
            end_date=start_date + timedelta(hours=2),
            location="Lyon",
            attendees=50,
            notes=None,
        )

    event_repository.add.assert_not_called()


def test_management_can_assign_support_employee() -> None:
    service, event_repository, _, employee_repository = build_service()
    identity = make_identity(
        employee_id=1,
        role="management",
    )
    event = make_event(support_contact_id=None)

    support_employee = Mock(spec=Employee)
    support_employee.id = 3
    support_employee.role = Mock()
    support_employee.role.name = "support"

    event_repository.get_by_id.return_value = event
    employee_repository.get_by_id.return_value = support_employee

    updated_event = service.assign_support(
        identity,
        event_id=1,
        support_employee_id=3,
    )

    assert updated_event.support_contact_id == 3
    event_repository.save.assert_called_once_with(event)


def test_assign_support_rejects_unknown_employee() -> None:
    service, event_repository, _, employee_repository = build_service()
    identity = make_identity(
        employee_id=1,
        role="management",
    )
    event_repository.get_by_id.return_value = make_event(
        support_contact_id=None,
    )
    employee_repository.get_by_id.return_value = None

    with pytest.raises(SupportEmployeeNotFoundError):
        service.assign_support(
            identity,
            event_id=1,
            support_employee_id=999,
        )

    event_repository.save.assert_not_called()


def test_assign_support_rejects_non_support_employee() -> None:
    service, event_repository, _, employee_repository = build_service()
    identity = make_identity(
        employee_id=1,
        role="management",
    )
    event = make_event(support_contact_id=None)

    sales_employee = Mock(spec=Employee)
    sales_employee.id = 2
    sales_employee.role = Mock()
    sales_employee.role.name = "sales"

    event_repository.get_by_id.return_value = event
    employee_repository.get_by_id.return_value = sales_employee

    with pytest.raises(InvalidSupportRoleError):
        service.assign_support(
            identity,
            event_id=1,
            support_employee_id=2,
        )

    event_repository.save.assert_not_called()


def test_support_can_update_assigned_event() -> None:
    service, event_repository, _, _ = build_service()
    identity = make_identity(
        employee_id=3,
        role="support",
    )
    event = make_event(support_contact_id=3)
    event_repository.get_by_id.return_value = event

    new_start_date = datetime(
        2026,
        10,
        11,
        10,
        0,
        tzinfo=timezone.utc,
    )
    new_end_date = new_start_date + timedelta(hours=5)

    updated_event = service.update_event(
        identity,
        event_id=1,
        name=" Updated Conference ",
        start_date=new_start_date,
        end_date=new_end_date,
        location=" Paris ",
        attendees=150,
        notes=" Updated notes. ",
    )

    assert updated_event.name == "Updated Conference"
    assert updated_event.start_date == new_start_date
    assert updated_event.end_date == new_end_date
    assert updated_event.location == "Paris"
    assert updated_event.attendees == 150
    assert updated_event.notes == "Updated notes."
    event_repository.save.assert_called_once_with(event)


def test_support_cannot_update_unassigned_event() -> None:
    service, event_repository, _, _ = build_service()
    identity = make_identity(
        employee_id=3,
        role="support",
    )
    event_repository.get_by_id.return_value = make_event(
        support_contact_id=4,
    )

    start_date = datetime.now(timezone.utc)

    with pytest.raises(PermissionDeniedError):
        service.update_event(
            identity,
            event_id=1,
            name="Conference",
            start_date=start_date,
            end_date=start_date + timedelta(hours=2),
            location="Lyon",
            attendees=50,
            notes=None,
        )

    event_repository.save.assert_not_called()

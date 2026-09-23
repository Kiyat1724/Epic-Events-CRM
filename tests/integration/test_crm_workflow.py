from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from epic_events.models import Role
from epic_events.repositories.client_repository import ClientRepository
from epic_events.repositories.contract_repository import ContractRepository
from epic_events.repositories.employee_repository import EmployeeRepository
from epic_events.repositories.event_repository import EventRepository
from epic_events.repositories.role_repository import RoleRepository
from epic_events.services.client_service import ClientService
from epic_events.services.contract_service import ContractService
from epic_events.services.employee_service import EmployeeService
from epic_events.services.event_service import EventService
from epic_events.services.jwt_service import TokenPayload
from epic_events.services.permission_service import PermissionDeniedError


def make_identity(
    *,
    employee_id: int,
    email: str,
    role: str,
) -> Mock:
    """Create an authenticated identity for an integration workflow."""

    identity = Mock(spec=TokenPayload)
    identity.employee_id = employee_id
    identity.email = email
    identity.role = role
    return identity


def seed_roles(session: Session) -> None:
    """Insert the Epic Events roles in the temporary database."""

    session.add_all(
        [
            Role(name="management"),
            Role(name="sales"),
            Role(name="support"),
        ]
    )
    session.flush()


def build_services(
    session: Session,
) -> tuple[
    EmployeeService,
    ClientService,
    ContractService,
    EventService,
]:
    """Build services backed by real repositories and one database."""

    employee_repository = EmployeeRepository(session)
    role_repository = RoleRepository(session)
    client_repository = ClientRepository(session)
    contract_repository = ContractRepository(session)
    event_repository = EventRepository(session)

    employee_service = EmployeeService(
        employee_repository,
        role_repository,
    )
    client_service = ClientService(client_repository)
    contract_service = ContractService(
        contract_repository,
        client_repository,
    )
    event_service = EventService(
        event_repository,
        contract_repository,
        employee_repository,
    )

    return (
        employee_service,
        client_service,
        contract_service,
        event_service,
    )


def test_complete_crm_workflow_persists_data(
    database_session: Session,
) -> None:
    """Exercise the complete client-to-event business workflow."""

    seed_roles(database_session)

    (
        employee_service,
        client_service,
        contract_service,
        event_service,
    ) = build_services(database_session)

    manager = employee_service.create_employee(
        employee_number="MGT-001",
        full_name="Alice Manager",
        email="manager@example.com",
        password="ManagerPassword123!",
        role_name="management",
    )
    salesperson = employee_service.create_employee(
        employee_number="SAL-001",
        full_name="Bob Sales",
        email="sales@example.com",
        password="SalesPassword123!",
        role_name="sales",
    )
    support_employee = employee_service.create_employee(
        employee_number="SUP-001",
        full_name="Carol Support",
        email="support@example.com",
        password="SupportPassword123!",
        role_name="support",
    )

    manager_identity = make_identity(
        employee_id=manager.id,
        email=manager.email,
        role="management",
    )
    sales_identity = make_identity(
        employee_id=salesperson.id,
        email=salesperson.email,
        role="sales",
    )
    support_identity = make_identity(
        employee_id=support_employee.id,
        email=support_employee.email,
        role="support",
    )

    client = client_service.create_client(
        sales_identity,
        full_name="Kevin Casey",
        email="kevin@example.com",
        phone="+33 6 12 34 56 78",
        company_name="Secure Company",
    )

    contract = contract_service.create_contract(
        manager_identity,
        client_id=client.id,
        total_amount=Decimal("5000.00"),
        remaining_amount=Decimal("3500.00"),
        signed=True,
    )

    start_date = datetime(
        2026,
        10,
        10,
        14,
        0,
        tzinfo=timezone.utc,
    )
    end_date = start_date + timedelta(hours=4)

    event = event_service.create_event(
        sales_identity,
        contract_id=contract.id,
        name="Cybersecurity Conference",
        start_date=start_date,
        end_date=end_date,
        location="Lyon",
        attendees=100,
        notes="Initial event notes.",
    )

    assigned_event = event_service.assign_support(
        manager_identity,
        event_id=event.id,
        support_employee_id=support_employee.id,
    )

    assert assigned_event.support_contact_id == support_employee.id

    updated_event = event_service.update_event(
        support_identity,
        event_id=event.id,
        name="Cybersecurity Conference",
        start_date=start_date,
        end_date=end_date,
        location="Paris",
        attendees=150,
        notes="Event confirmed by support.",
    )

    database_session.flush()
    database_session.expire_all()

    persisted_client = ClientRepository(database_session).get_by_id(client.id)
    persisted_contract = ContractRepository(database_session).get_by_id(contract.id)
    persisted_event = EventRepository(database_session).get_by_id(updated_event.id)

    assert persisted_client is not None
    assert persisted_client.sales_contact_id == salesperson.id

    assert persisted_contract is not None
    assert persisted_contract.client_id == persisted_client.id
    assert persisted_contract.signed is True
    assert persisted_contract.total_amount == Decimal("5000.00")

    assert persisted_event is not None
    assert persisted_event.contract_id == persisted_contract.id
    assert persisted_event.support_contact_id == support_employee.id
    assert persisted_event.location == "Paris"
    assert persisted_event.attendees == 150
    assert persisted_event.notes == "Event confirmed by support."


def test_salesperson_cannot_create_contract(
    database_session: Session,
) -> None:
    """Reject contract creation by a salesperson across real layers."""

    seed_roles(database_session)

    (
        employee_service,
        client_service,
        contract_service,
        _,
    ) = build_services(database_session)

    salesperson = employee_service.create_employee(
        employee_number="SAL-002",
        full_name="Diane Sales",
        email="diane@example.com",
        password="SalesPassword123!",
        role_name="sales",
    )

    sales_identity = make_identity(
        employee_id=salesperson.id,
        email=salesperson.email,
        role="sales",
    )

    client = client_service.create_client(
        sales_identity,
        full_name="John Customer",
        email="john@example.com",
        phone="+33 6 98 76 54 32",
        company_name="Customer Company",
    )

    with pytest.raises(PermissionDeniedError):
        contract_service.create_contract(
            sales_identity,
            client_id=client.id,
            total_amount=Decimal("2500.00"),
            remaining_amount=Decimal("2500.00"),
            signed=False,
        )

    assert ContractRepository(database_session).list_all() == []

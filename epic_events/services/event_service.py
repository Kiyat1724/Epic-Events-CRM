from datetime import datetime

from epic_events.models import Event
from epic_events.repositories.contract_repository import ContractRepository
from epic_events.repositories.employee_repository import EmployeeRepository
from epic_events.repositories.event_repository import EventRepository
from epic_events.services.jwt_service import TokenPayload
from epic_events.services.permission_service import (
    require_event_creation,
    require_event_update,
    require_management,
    require_support,
    require_support_assignment,
)


class EventNotFoundError(Exception):
    """Represent a requested event that does not exist."""


class EventContractNotFoundError(Exception):
    """Represent a contract that cannot be attached to an event."""


class EventAlreadyExistsError(Exception):
    """Represent a contract that already has an event."""


class SupportEmployeeNotFoundError(Exception):
    """Represent a requested support employee that does not exist."""


class InvalidSupportRoleError(Exception):
    """Represent an employee who does not belong to support."""


class EventService:
    """Apply business rules related to events."""

    def __init__(
        self,
        event_repository: EventRepository,
        contract_repository: ContractRepository,
        employee_repository: EmployeeRepository,
    ) -> None:
        self.event_repository = event_repository
        self.contract_repository = contract_repository
        self.employee_repository = employee_repository

    def list_events(self) -> list[Event]:
        """Return all events."""

        return self.event_repository.list_all()

    def list_events_without_support(
        self,
        identity: TokenPayload,
    ) -> list[Event]:
        """Return unassigned events to management employees."""

        require_management(identity)
        return self.event_repository.list_without_support()

    def list_assigned_events(
        self,
        identity: TokenPayload,
    ) -> list[Event]:
        """Return events assigned to the authenticated support employee."""

        require_support(identity)
        return self.event_repository.list_assigned_to(identity.employee_id)

    def get_event(
        self,
        *,
        event_id: int,
    ) -> Event:
        """Return one event."""

        event = self.event_repository.get_by_id(event_id)

        if event is None:
            raise EventNotFoundError("Event not found.")

        return event

    def create_event(
        self,
        identity: TokenPayload,
        *,
        contract_id: int,
        name: str,
        start_date: datetime,
        end_date: datetime,
        location: str,
        attendees: int,
        notes: str | None,
    ) -> Event:
        """Create an event for a signed contract owned by sales."""

        contract = self.contract_repository.get_by_id(contract_id)
        if contract is None:
            raise EventContractNotFoundError("Contract not found.")

        require_event_creation(
            identity,
            sales_contact_id=contract.client.sales_contact_id,
            contract_is_signed=contract.signed,
        )

        existing_event = self.event_repository.get_by_contract_id(contract_id)
        if existing_event is not None:
            raise EventAlreadyExistsError("This contract already has an event.")

        self._validate_event_data(
            name=name,
            start_date=start_date,
            end_date=end_date,
            location=location,
            attendees=attendees,
        )

        event = Event(
            contract_id=contract_id,
            name=name.strip(),
            start_date=start_date,
            end_date=end_date,
            location=location.strip(),
            attendees=attendees,
            notes=notes.strip() if notes else None,
            support_contact_id=None,
        )
        return self.event_repository.add(event)

    def assign_support(
        self,
        identity: TokenPayload,
        *,
        event_id: int,
        support_employee_id: int,
    ) -> Event:
        """Assign a support employee to an event as management."""

        require_support_assignment(identity)

        event = self.event_repository.get_by_id(event_id)
        if event is None:
            raise EventNotFoundError("Event not found.")

        employee = self.employee_repository.get_by_id(support_employee_id)
        if employee is None:
            raise SupportEmployeeNotFoundError("Support employee not found.")

        if employee.role.name != "support":
            raise InvalidSupportRoleError(
                "The selected employee must have the support role."
            )

        event.support_contact_id = employee.id
        return self.event_repository.save(event)

    def update_event(
        self,
        identity: TokenPayload,
        *,
        event_id: int,
        name: str,
        start_date: datetime,
        end_date: datetime,
        location: str,
        attendees: int,
        notes: str | None,
    ) -> Event:
        """Update an event assigned to the authenticated support employee."""

        event = self.event_repository.get_by_id(event_id)
        if event is None:
            raise EventNotFoundError("Event not found.")

        require_event_update(
            identity,
            support_contact_id=event.support_contact_id,
        )
        self._validate_event_data(
            name=name,
            start_date=start_date,
            end_date=end_date,
            location=location,
            attendees=attendees,
        )

        event.name = name.strip()
        event.start_date = start_date
        event.end_date = end_date
        event.location = location.strip()
        event.attendees = attendees
        event.notes = notes.strip() if notes else None

        return self.event_repository.save(event)

    @staticmethod
    def _validate_event_data(
        *,
        name: str,
        start_date: datetime,
        end_date: datetime,
        location: str,
        attendees: int,
    ) -> None:
        if not name.strip():
            raise ValueError("Event name is required.")

        if end_date <= start_date:
            raise ValueError("Event end date must be after its start date.")

        if not location.strip():
            raise ValueError("Event location is required.")

        if attendees <= 0:
            raise ValueError("Event attendees must be greater than zero.")

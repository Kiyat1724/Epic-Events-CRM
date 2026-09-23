from datetime import datetime
from typing import NoReturn

import click
from sqlalchemy.orm import Session

from epic_events.database import session_scope
from epic_events.models import Event
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
from epic_events.services.jwt_service import (
    AuthenticationError,
    TokenPayload,
)
from epic_events.services.permission_service import (
    PermissionDeniedError,
    require_event_update,
    require_sales,
)
from epic_events.services.session_service import get_current_identity


def get_authenticated_identity() -> TokenPayload:
    """Return the authenticated identity or convert the error for Click."""

    try:
        return get_current_identity()
    except AuthenticationError as error:
        raise click.ClickException(str(error)) from error


def build_event_service(session: Session) -> EventService:
    """Create an event service using the current database session."""

    return EventService(
        EventRepository(session),
        ContractRepository(session),
        EmployeeRepository(session),
    )


def raise_invalid_datetime(value: str) -> NoReturn:
    """Raise a Click error for an invalid date and time."""

    raise click.BadParameter(
        (
            f"{value!r} is not a valid date and time. "
            "Use an ISO 8601 value with a timezone, "
            "for example: 2026-10-10T14:00:00+02:00."
        ),
        param_hint="date",
    )


def parse_datetime(value: str) -> datetime:
    """Convert an ISO 8601 string into a timezone-aware datetime."""

    try:
        parsed_value = datetime.fromisoformat(value)
    except ValueError:
        raise_invalid_datetime(value)

    if parsed_value.tzinfo is None:
        raise_invalid_datetime(value)

    return parsed_value


def prompt_datetime(
    label: str,
    *,
    default: datetime | None = None,
) -> datetime:
    """Prompt until the user enters a valid timezone-aware date."""

    default_value = default.isoformat() if default else None

    while True:
        value = click.prompt(
            label,
            default=default_value,
            show_default=default_value is not None,
        )

        try:
            return parse_datetime(value)
        except click.BadParameter as error:
            click.secho(f"Error: {error}", fg="red")


def display_event(event: Event) -> None:
    """Display one event in the terminal."""

    click.echo(f"ID: {event.id}")
    click.echo(f"Contract ID: {event.contract_id}")
    click.echo(f"Name: {event.name}")
    click.echo(f"Start date: {event.start_date}")
    click.echo(f"End date: {event.end_date}")
    click.echo(f"Location: {event.location}")
    click.echo(f"Attendees: {event.attendees}")
    click.echo(f"Notes: {event.notes or ''}")
    click.echo(
        "Support contact ID: "
        f"{event.support_contact_id if event.support_contact_id else 'Unassigned'}"
    )


def display_event_list(event_list: list[Event]) -> None:
    """Display a collection of events."""

    if not event_list:
        click.echo("No events found.")
        return

    for index, event in enumerate(event_list):
        if index:
            click.echo("-" * 40)

        display_event(event)


@click.group()
def events() -> None:
    """Manage Epic Events events."""


@events.command("list")
def list_events_command() -> None:
    """List every event."""

    get_authenticated_identity()

    with session_scope() as session:
        service = build_event_service(session)
        event_list = service.list_events()
        display_event_list(event_list)


@events.command("show")
@click.argument("event_id", type=int)
def show_event_command(event_id: int) -> None:
    """Display one event."""

    get_authenticated_identity()

    try:
        with session_scope() as session:
            service = build_event_service(session)
            event = service.get_event(event_id=event_id)
            display_event(event)

    except EventNotFoundError as error:
        raise click.ClickException(str(error)) from error


@events.command("without-support")
def list_events_without_support_command() -> None:
    """List events that do not have an assigned support employee."""

    identity = get_authenticated_identity()

    try:
        with session_scope() as session:
            service = build_event_service(session)
            event_list = service.list_events_without_support(identity)
            display_event_list(event_list)

    except PermissionDeniedError as error:
        raise click.ClickException(str(error)) from error


@events.command("assigned")
def list_assigned_events_command() -> None:
    """List events assigned to the authenticated support employee."""

    identity = get_authenticated_identity()

    try:
        with session_scope() as session:
            service = build_event_service(session)
            event_list = service.list_assigned_events(identity)
            display_event_list(event_list)

    except PermissionDeniedError as error:
        raise click.ClickException(str(error)) from error


@events.command("create")
def create_event_command() -> None:
    """Create an event for a signed contract owned by the salesperson."""

    identity = get_authenticated_identity()

    try:
        require_sales(identity)
    except PermissionDeniedError as error:
        raise click.ClickException(str(error)) from error

    contract_id = click.prompt("Contract ID", type=int)
    name = click.prompt("Event name", type=str)
    start_date = prompt_datetime("Start date")
    end_date = prompt_datetime("End date")
    location = click.prompt("Location", type=str)
    attendees = click.prompt("Number of attendees", type=int)
    notes = click.prompt(
        "Notes",
        default="",
        show_default=False,
    )

    try:
        with session_scope() as session:
            service = build_event_service(session)
            event = service.create_event(
                identity,
                contract_id=contract_id,
                name=name,
                start_date=start_date,
                end_date=end_date,
                location=location,
                attendees=attendees,
                notes=notes or None,
            )
            event_id = event.id

    except (
        EventAlreadyExistsError,
        EventContractNotFoundError,
        PermissionDeniedError,
        ValueError,
    ) as error:
        raise click.ClickException(str(error)) from error

    click.secho(
        f"Event {event_id} created successfully.",
        fg="green",
    )


@events.command("assign-support")
@click.argument("event_id", type=int)
@click.argument("support_employee_id", type=int)
def assign_support_command(
    event_id: int,
    support_employee_id: int,
) -> None:
    """Assign a support employee to an event."""

    identity = get_authenticated_identity()

    try:
        with session_scope() as session:
            service = build_event_service(session)
            event = service.assign_support(
                identity,
                event_id=event_id,
                support_employee_id=support_employee_id,
            )
            updated_event_id = event.id

    except (
        EventNotFoundError,
        InvalidSupportRoleError,
        PermissionDeniedError,
        SupportEmployeeNotFoundError,
    ) as error:
        raise click.ClickException(str(error)) from error

    click.secho(
        (
            f"Support employee {support_employee_id} "
            f"assigned to event {updated_event_id} successfully."
        ),
        fg="green",
    )


@events.command("update")
@click.argument("event_id", type=int)
def update_event_command(event_id: int) -> None:
    """Update an event assigned to the authenticated support employee."""

    identity = get_authenticated_identity()

    try:
        with session_scope() as session:
            service = build_event_service(session)
            existing_event = service.get_event(event_id=event_id)

            require_event_update(
                identity,
                support_contact_id=existing_event.support_contact_id,
            )

            name = click.prompt(
                "Event name",
                default=existing_event.name,
            )
            start_date = prompt_datetime(
                "Start date",
                default=existing_event.start_date,
            )
            end_date = prompt_datetime(
                "End date",
                default=existing_event.end_date,
            )
            location = click.prompt(
                "Location",
                default=existing_event.location,
            )
            attendees = click.prompt(
                "Number of attendees",
                type=int,
                default=existing_event.attendees,
            )
            notes = click.prompt(
                "Notes",
                default=existing_event.notes or "",
                show_default=bool(existing_event.notes),
            )

            event = service.update_event(
                identity,
                event_id=event_id,
                name=name,
                start_date=start_date,
                end_date=end_date,
                location=location,
                attendees=attendees,
                notes=notes or None,
            )
            updated_event_id = event.id

    except (
        EventNotFoundError,
        PermissionDeniedError,
        ValueError,
    ) as error:
        raise click.ClickException(str(error)) from error

    click.secho(
        f"Event {updated_event_id} updated successfully.",
        fg="green",
    )

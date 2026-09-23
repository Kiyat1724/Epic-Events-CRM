from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from epic_events.models import Client, Contract, Event


class EventRepository:
    """Manage event persistence in the database."""

    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _loading_options() -> tuple[object, ...]:
        return (
            selectinload(Event.contract)
            .selectinload(Contract.client)
            .selectinload(Client.sales_contact),
            selectinload(Event.support_contact),
        )

    def list_all(self) -> list[Event]:
        statement = select(Event).options(*self._loading_options()).order_by(Event.id)
        return list(self.session.scalars(statement))

    def list_without_support(self) -> list[Event]:
        statement = (
            select(Event)
            .options(*self._loading_options())
            .where(Event.support_contact_id.is_(None))
            .order_by(Event.id)
        )
        return list(self.session.scalars(statement))

    def list_assigned_to(self, employee_id: int) -> list[Event]:
        statement = (
            select(Event)
            .options(*self._loading_options())
            .where(Event.support_contact_id == employee_id)
            .order_by(Event.id)
        )
        return list(self.session.scalars(statement))

    def get_by_id(self, event_id: int) -> Event | None:
        statement = (
            select(Event).options(*self._loading_options()).where(Event.id == event_id)
        )
        return self.session.scalar(statement)

    def get_by_contract_id(self, contract_id: int) -> Event | None:
        statement = select(Event).where(Event.contract_id == contract_id)
        return self.session.scalar(statement)

    def add(self, event: Event) -> Event:
        self.session.add(event)
        self.session.flush()
        self.session.refresh(event)
        return event

    def save(self, event: Event) -> Event:
        self.session.flush()
        self.session.refresh(event)
        return event

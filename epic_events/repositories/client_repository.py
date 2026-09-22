from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from epic_events.models import Client


class ClientRepository:
    """Manage client persistence in the database."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[Client]:
        statement = (
            select(Client)
            .options(selectinload(Client.sales_contact))
            .order_by(Client.id)
        )
        return list(self.session.scalars(statement))

    def get_by_id(self, client_id: int) -> Client | None:
        statement = (
            select(Client)
            .options(selectinload(Client.sales_contact))
            .where(Client.id == client_id)
        )
        return self.session.scalar(statement)

    def add(self, client: Client) -> Client:
        self.session.add(client)
        self.session.flush()
        self.session.refresh(client)
        return client

    def save(self, client: Client) -> Client:
        self.session.flush()
        self.session.refresh(client)
        return client

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from epic_events.models import Client, Contract


class ContractRepository:
    """Manage contract persistence in the database."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[Contract]:
        statement = (
            select(Contract)
            .options(selectinload(Contract.client).selectinload(Client.sales_contact))
            .order_by(Contract.id)
        )
        return list(self.session.scalars(statement))

    def list_unsigned(self) -> list[Contract]:
        statement = (
            select(Contract)
            .options(selectinload(Contract.client).selectinload(Client.sales_contact))
            .where(Contract.signed.is_(False))
            .order_by(Contract.id)
        )
        return list(self.session.scalars(statement))

    def list_unpaid(self) -> list[Contract]:
        statement = (
            select(Contract)
            .options(selectinload(Contract.client).selectinload(Client.sales_contact))
            .where(Contract.remaining_amount > 0)
            .order_by(Contract.id)
        )
        return list(self.session.scalars(statement))

    def get_by_id(self, contract_id: int) -> Contract | None:
        statement = (
            select(Contract)
            .options(selectinload(Contract.client).selectinload(Client.sales_contact))
            .where(Contract.id == contract_id)
        )
        return self.session.scalar(statement)

    def add(self, contract: Contract) -> Contract:
        self.session.add(contract)
        self.session.flush()
        self.session.refresh(contract)
        return contract

    def save(self, contract: Contract) -> Contract:
        self.session.flush()
        self.session.refresh(contract)
        return contract

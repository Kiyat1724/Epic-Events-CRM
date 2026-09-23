from decimal import Decimal

from epic_events.models import Contract
from epic_events.repositories.client_repository import ClientRepository
from epic_events.repositories.contract_repository import ContractRepository
from epic_events.services.jwt_service import TokenPayload
from epic_events.services.permission_service import (
    require_contract_creation,
    require_contract_update,
)


class ContractNotFoundError(Exception):
    """Represent a requested contract that does not exist."""


class ContractClientNotFoundError(Exception):
    """Represent a client that cannot be attached to a contract."""


class ContractService:
    """Apply business rules related to contracts."""

    def __init__(
        self,
        contract_repository: ContractRepository,
        client_repository: ClientRepository,
    ) -> None:
        self.contract_repository = contract_repository
        self.client_repository = client_repository

    def list_contracts(self) -> list[Contract]:
        """Return all contracts."""

        return self.contract_repository.list_all()

    def list_unsigned_contracts(self) -> list[Contract]:
        """Return contracts that have not been signed."""

        return self.contract_repository.list_unsigned()

    def list_unpaid_contracts(self) -> list[Contract]:
        """Return contracts with a remaining amount to pay."""

        return self.contract_repository.list_unpaid()

    def get_contract(
        self,
        *,
        contract_id: int,
    ) -> Contract:
        """Return one contract."""

        contract = self.contract_repository.get_by_id(contract_id)

        if contract is None:
            raise ContractNotFoundError("Contract not found.")

        return contract

    def create_contract(
        self,
        identity: TokenPayload,
        *,
        client_id: int,
        total_amount: Decimal,
        remaining_amount: Decimal,
        signed: bool,
    ) -> Contract:
        """Create a contract as a management employee."""

        require_contract_creation(identity)

        client = self.client_repository.get_by_id(client_id)
        if client is None:
            raise ContractClientNotFoundError("Client not found.")

        self._validate_amounts(
            total_amount=total_amount,
            remaining_amount=remaining_amount,
        )

        contract = Contract(
            client_id=client.id,
            total_amount=total_amount,
            remaining_amount=remaining_amount,
            signed=signed,
        )
        return self.contract_repository.add(contract)

    def update_contract(
        self,
        identity: TokenPayload,
        *,
        contract_id: int,
        total_amount: Decimal,
        remaining_amount: Decimal,
        signed: bool,
    ) -> Contract:
        """Update a contract with role and ownership controls."""

        contract = self.contract_repository.get_by_id(contract_id)
        if contract is None:
            raise ContractNotFoundError("Contract not found.")

        require_contract_update(
            identity,
            sales_contact_id=contract.client.sales_contact_id,
        )
        self._validate_amounts(
            total_amount=total_amount,
            remaining_amount=remaining_amount,
        )

        contract.total_amount = total_amount
        contract.remaining_amount = remaining_amount
        contract.signed = signed

        return self.contract_repository.save(contract)

    @staticmethod
    def _validate_amounts(
        *,
        total_amount: Decimal,
        remaining_amount: Decimal,
    ) -> None:
        if total_amount < 0:
            raise ValueError("Total amount cannot be negative.")

        if remaining_amount < 0:
            raise ValueError("Remaining amount cannot be negative.")

        if remaining_amount > total_amount:
            raise ValueError("Remaining amount cannot exceed total amount.")

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest

from epic_events.models import Client, Contract
from epic_events.repositories.client_repository import ClientRepository
from epic_events.repositories.contract_repository import ContractRepository
from epic_events.services.contract_service import (
    ContractNotFoundError,
    ContractService,
)
from epic_events.services.jwt_service import TokenPayload
from epic_events.services.permission_service import PermissionDeniedError


def build_identity(
    role: str,
    *,
    employee_id: int = 1,
) -> TokenPayload:
    return TokenPayload(
        employee_id=employee_id,
        email=f"{role}@example.com",
        role=role,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )


def build_service() -> tuple[ContractService, Mock, Mock]:
    contract_repository = Mock(spec=ContractRepository)
    client_repository = Mock(spec=ClientRepository)
    service = ContractService(
        contract_repository=contract_repository,
        client_repository=client_repository,
    )
    return service, contract_repository, client_repository


def test_list_contracts_returns_all_contracts() -> None:
    service, contract_repository, _ = build_service()
    contracts = [Mock(spec=Contract)]
    contract_repository.list_all.return_value = contracts

    assert service.list_contracts() == contracts


def test_list_unsigned_contracts_returns_unsigned_contracts() -> None:
    service, contract_repository, _ = build_service()
    contracts = [Mock(spec=Contract)]
    contract_repository.list_unsigned.return_value = contracts

    assert service.list_unsigned_contracts() == contracts


def test_list_unpaid_contracts_returns_unpaid_contracts() -> None:
    service, contract_repository, _ = build_service()
    contracts = [Mock(spec=Contract)]
    contract_repository.list_unpaid.return_value = contracts

    assert service.list_unpaid_contracts() == contracts


def test_get_contract_rejects_unknown_contract() -> None:
    service, contract_repository, _ = build_service()
    contract_repository.get_by_id.return_value = None

    with pytest.raises(
        ContractNotFoundError,
        match="Contract not found",
    ):
        service.get_contract(contract_id=999)


def test_management_creates_contract() -> None:
    service, contract_repository, client_repository = build_service()
    identity = build_identity("management")
    client = Client(
        full_name="Kevin Casey",
        email="kevin@startup.io",
        phone="+33 6 12 34 56 77",
        company_name="Cool IT SECU",
        sales_contact_id=2,
    )
    client.id = 1
    client_repository.get_by_id.return_value = client
    contract_repository.add.side_effect = lambda contract: contract

    contract = service.create_contract(
        identity,
        client_id=1,
        total_amount=Decimal("10000.00"),
        remaining_amount=Decimal("5000.00"),
        signed=False,
    )

    assert contract.client_id == 1
    assert contract.total_amount == Decimal("10000.00")
    assert contract.remaining_amount == Decimal("5000.00")
    assert contract.signed is False
    contract_repository.add.assert_called_once_with(contract)


def test_sales_employee_cannot_create_contract() -> None:
    service, contract_repository, _ = build_service()
    identity = build_identity("sales", employee_id=2)

    with pytest.raises(PermissionDeniedError):
        service.create_contract(
            identity,
            client_id=1,
            total_amount=Decimal("10000.00"),
            remaining_amount=Decimal("5000.00"),
            signed=False,
        )

    contract_repository.add.assert_not_called()


def test_create_contract_rejects_remaining_amount_above_total() -> None:
    service, contract_repository, client_repository = build_service()
    identity = build_identity("management")
    client = Mock(spec=Client)
    client.id = 1
    client_repository.get_by_id.return_value = client

    with pytest.raises(
        ValueError,
        match="cannot exceed total amount",
    ):
        service.create_contract(
            identity,
            client_id=1,
            total_amount=Decimal("1000.00"),
            remaining_amount=Decimal("1500.00"),
            signed=False,
        )

    contract_repository.add.assert_not_called()


def test_sales_employee_updates_own_clients_contract() -> None:
    service, contract_repository, _ = build_service()
    identity = build_identity("sales", employee_id=2)
    client = Client(
        full_name="Kevin Casey",
        email="kevin@startup.io",
        phone="+33 6 12 34 56 77",
        company_name="Cool IT SECU",
        sales_contact_id=2,
    )
    contract = Contract(
        client_id=1,
        total_amount=Decimal("10000.00"),
        remaining_amount=Decimal("5000.00"),
        signed=False,
        client=client,
    )
    contract_repository.get_by_id.return_value = contract
    contract_repository.save.side_effect = lambda saved_contract: saved_contract

    result = service.update_contract(
        identity,
        contract_id=1,
        total_amount=Decimal("10000.00"),
        remaining_amount=Decimal("0.00"),
        signed=True,
    )

    assert result.remaining_amount == Decimal("0.00")
    assert result.signed is True
    contract_repository.save.assert_called_once_with(contract)


def test_sales_employee_cannot_update_another_clients_contract() -> None:
    service, contract_repository, _ = build_service()
    identity = build_identity("sales", employee_id=2)
    client = Client(
        full_name="Another Client",
        email="client@example.com",
        phone="+33 6 00 00 00 00",
        company_name="Another Company",
        sales_contact_id=99,
    )
    contract = Contract(
        client_id=1,
        total_amount=Decimal("10000.00"),
        remaining_amount=Decimal("5000.00"),
        signed=False,
        client=client,
    )
    contract_repository.get_by_id.return_value = contract

    with pytest.raises(PermissionDeniedError):
        service.update_contract(
            identity,
            contract_id=1,
            total_amount=Decimal("10000.00"),
            remaining_amount=Decimal("0.00"),
            signed=True,
        )

    contract_repository.save.assert_not_called()

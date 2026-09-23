from unittest.mock import Mock

from sqlalchemy.orm import Session

from epic_events.models import Contract
from epic_events.repositories.contract_repository import ContractRepository


def test_list_all_returns_contracts() -> None:
    session = Mock(spec=Session)
    contracts = [
        Mock(spec=Contract),
        Mock(spec=Contract),
    ]
    session.scalars.return_value = contracts
    repository = ContractRepository(session)

    result = repository.list_all()

    assert result == contracts
    session.scalars.assert_called_once()


def test_list_unsigned_returns_contracts() -> None:
    session = Mock(spec=Session)
    contracts = [Mock(spec=Contract)]
    session.scalars.return_value = contracts
    repository = ContractRepository(session)

    result = repository.list_unsigned()

    assert result == contracts
    session.scalars.assert_called_once()


def test_list_unpaid_returns_contracts() -> None:
    session = Mock(spec=Session)
    contracts = [Mock(spec=Contract)]
    session.scalars.return_value = contracts
    repository = ContractRepository(session)

    result = repository.list_unpaid()

    assert result == contracts
    session.scalars.assert_called_once()


def test_get_by_id_returns_contract() -> None:
    session = Mock(spec=Session)
    contract = Mock(spec=Contract)
    session.scalar.return_value = contract
    repository = ContractRepository(session)

    result = repository.get_by_id(1)

    assert result is contract
    session.scalar.assert_called_once()


def test_add_persists_and_refreshes_contract() -> None:
    session = Mock(spec=Session)
    contract = Mock(spec=Contract)
    repository = ContractRepository(session)

    result = repository.add(contract)

    assert result is contract
    session.add.assert_called_once_with(contract)
    session.flush.assert_called_once_with()
    session.refresh.assert_called_once_with(contract)


def test_save_flushes_and_refreshes_contract() -> None:
    session = Mock(spec=Session)
    contract = Mock(spec=Contract)
    repository = ContractRepository(session)

    result = repository.save(contract)

    assert result is contract
    session.flush.assert_called_once_with()
    session.refresh.assert_called_once_with(contract)

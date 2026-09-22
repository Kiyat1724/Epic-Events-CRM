from unittest.mock import Mock

from sqlalchemy.orm import Session

from epic_events.models import Client
from epic_events.repositories.client_repository import ClientRepository


def test_list_all_returns_clients() -> None:
    session = Mock(spec=Session)
    clients = [
        Mock(spec=Client),
        Mock(spec=Client),
    ]
    session.scalars.return_value = clients
    repository = ClientRepository(session)

    result = repository.list_all()

    assert result == clients
    session.scalars.assert_called_once()


def test_get_by_id_returns_client() -> None:
    session = Mock(spec=Session)
    expected_client = Mock(spec=Client)
    session.scalar.return_value = expected_client
    repository = ClientRepository(session)

    result = repository.get_by_id(1)

    assert result is expected_client
    session.scalar.assert_called_once()


def test_add_persists_and_refreshes_client() -> None:
    session = Mock(spec=Session)
    client = Mock(spec=Client)
    repository = ClientRepository(session)

    result = repository.add(client)

    assert result is client
    session.add.assert_called_once_with(client)
    session.flush.assert_called_once_with()
    session.refresh.assert_called_once_with(client)


def test_save_flushes_and_refreshes_client() -> None:
    session = Mock(spec=Session)
    client = Mock(spec=Client)
    repository = ClientRepository(session)

    result = repository.save(client)

    assert result is client
    session.flush.assert_called_once_with()
    session.refresh.assert_called_once_with(client)

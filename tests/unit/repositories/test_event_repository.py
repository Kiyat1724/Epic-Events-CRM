from unittest.mock import Mock

from sqlalchemy.orm import Session

from epic_events.models import Event
from epic_events.repositories.event_repository import EventRepository


def test_list_all_returns_events() -> None:
    session = Mock(spec=Session)
    events = [Mock(spec=Event)]
    session.scalars.return_value = events
    repository = EventRepository(session)

    result = repository.list_all()

    assert result == events
    session.scalars.assert_called_once()


def test_list_without_support_returns_events() -> None:
    session = Mock(spec=Session)
    events = [Mock(spec=Event)]
    session.scalars.return_value = events
    repository = EventRepository(session)

    result = repository.list_without_support()

    assert result == events
    session.scalars.assert_called_once()


def test_list_assigned_to_returns_events() -> None:
    session = Mock(spec=Session)
    events = [Mock(spec=Event)]
    session.scalars.return_value = events
    repository = EventRepository(session)

    result = repository.list_assigned_to(3)

    assert result == events
    session.scalars.assert_called_once()


def test_get_by_id_returns_event() -> None:
    session = Mock(spec=Session)
    event = Mock(spec=Event)
    session.scalar.return_value = event
    repository = EventRepository(session)

    result = repository.get_by_id(1)

    assert result is event
    session.scalar.assert_called_once()


def test_get_by_contract_id_returns_event() -> None:
    session = Mock(spec=Session)
    event = Mock(spec=Event)
    session.scalar.return_value = event
    repository = EventRepository(session)

    result = repository.get_by_contract_id(1)

    assert result is event
    session.scalar.assert_called_once()


def test_add_persists_and_refreshes_event() -> None:
    session = Mock(spec=Session)
    event = Mock(spec=Event)
    repository = EventRepository(session)

    result = repository.add(event)

    assert result is event
    session.add.assert_called_once_with(event)
    session.flush.assert_called_once_with()
    session.refresh.assert_called_once_with(event)


def test_save_flushes_and_refreshes_event() -> None:
    session = Mock(spec=Session)
    event = Mock(spec=Event)
    repository = EventRepository(session)

    result = repository.save(event)

    assert result is event
    session.flush.assert_called_once_with()
    session.refresh.assert_called_once_with(event)

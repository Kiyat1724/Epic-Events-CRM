from unittest.mock import Mock

from sqlalchemy.orm import Session

from epic_events.models import Role
from epic_events.repositories.role_repository import RoleRepository


def test_get_by_name_returns_role() -> None:
    session = Mock(spec=Session)
    expected_role = Mock(spec=Role)
    session.scalar.return_value = expected_role
    repository = RoleRepository(session)

    role = repository.get_by_name("management")

    assert role is expected_role
    session.scalar.assert_called_once()

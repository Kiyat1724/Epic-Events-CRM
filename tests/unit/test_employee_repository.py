from unittest.mock import Mock

from sqlalchemy.orm import Session

from epic_events.models import Employee
from epic_events.repositories.employee_repository import EmployeeRepository


def test_get_by_email_returns_employee() -> None:
    session = Mock(spec=Session)
    expected_employee = Mock(spec=Employee)
    session.scalar.return_value = expected_employee
    repository = EmployeeRepository(session)

    employee = repository.get_by_email("manager@example.com")

    assert employee is expected_employee
    session.scalar.assert_called_once()


def test_get_by_employee_number_returns_employee() -> None:
    session = Mock(spec=Session)
    expected_employee = Mock(spec=Employee)
    session.scalar.return_value = expected_employee
    repository = EmployeeRepository(session)

    employee = repository.get_by_employee_number("EMP-001")

    assert employee is expected_employee
    session.scalar.assert_called_once()


def test_add_persists_and_refreshes_employee() -> None:
    session = Mock(spec=Session)
    employee = Mock(spec=Employee)
    repository = EmployeeRepository(session)

    result = repository.add(employee)

    assert result is employee
    session.add.assert_called_once_with(employee)
    session.flush.assert_called_once_with()
    session.refresh.assert_called_once_with(employee)


def test_exists_by_role_name_returns_true_when_employee_exists() -> None:
    session = Mock(spec=Session)
    session.scalar.return_value = 1
    repository = EmployeeRepository(session)

    result = repository.exists_by_role_name("management")

    assert result is True
    session.scalar.assert_called_once()


def test_exists_by_role_name_returns_false_when_employee_does_not_exist() -> None:
    session = Mock(spec=Session)
    session.scalar.return_value = None
    repository = EmployeeRepository(session)

    result = repository.exists_by_role_name("management")

    assert result is False
    session.scalar.assert_called_once()

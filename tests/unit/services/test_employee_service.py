from unittest.mock import Mock

import pytest

from epic_events.models import Role
from epic_events.repositories.employee_repository import EmployeeRepository
from epic_events.repositories.role_repository import RoleRepository
from epic_events.services.auth_service import verify_password
from epic_events.services.employee_service import EmployeeService


def build_service() -> tuple[EmployeeService, Mock, Mock]:
    employee_repository = Mock(spec=EmployeeRepository)
    role_repository = Mock(spec=RoleRepository)
    service = EmployeeService(employee_repository, role_repository)
    return service, employee_repository, role_repository


def test_create_employee_normalizes_and_hashes_data() -> None:
    service, employee_repository, role_repository = build_service()
    role = Role(name="management")

    employee_repository.get_by_email.return_value = None
    employee_repository.get_by_employee_number.return_value = None
    employee_repository.add.side_effect = lambda employee: employee
    role_repository.get_by_name.return_value = role

    employee = service.create_employee(
        employee_number=" EMP-001 ",
        full_name=" Alice Martin ",
        email=" ALICE@EXAMPLE.COM ",
        password="SecurePassword123!",
        role_name=" MANAGEMENT ",
    )

    assert employee.employee_number == "EMP-001"
    assert employee.full_name == "Alice Martin"
    assert employee.email == "alice@example.com"
    assert employee.role is role
    assert employee.password_hash != "SecurePassword123!"
    assert verify_password(
        "SecurePassword123!",
        employee.password_hash,
    )
    employee_repository.add.assert_called_once_with(employee)


def test_create_employee_rejects_invalid_role() -> None:
    service, employee_repository, role_repository = build_service()

    with pytest.raises(
        ValueError,
        match="Role must be management, sales, or support",
    ):
        service.create_employee(
            employee_number="EMP-001",
            full_name="Alice Martin",
            email="alice@example.com",
            password="SecurePassword123!",
            role_name="administrator",
        )

    employee_repository.add.assert_not_called()
    role_repository.get_by_name.assert_not_called()


def test_create_employee_rejects_duplicate_email() -> None:
    service, employee_repository, role_repository = build_service()
    employee_repository.get_by_email.return_value = Mock()

    with pytest.raises(
        ValueError,
        match="employee with this email already exists",
    ):
        service.create_employee(
            employee_number="EMP-001",
            full_name="Alice Martin",
            email="alice@example.com",
            password="SecurePassword123!",
            role_name="management",
        )

    employee_repository.add.assert_not_called()
    role_repository.get_by_name.assert_not_called()


def test_create_employee_rejects_duplicate_employee_number() -> None:
    service, employee_repository, role_repository = build_service()
    employee_repository.get_by_email.return_value = None
    employee_repository.get_by_employee_number.return_value = Mock()

    with pytest.raises(
        ValueError,
        match="employee with this employee number already exists",
    ):
        service.create_employee(
            employee_number="EMP-001",
            full_name="Alice Martin",
            email="alice@example.com",
            password="SecurePassword123!",
            role_name="management",
        )

    employee_repository.add.assert_not_called()
    role_repository.get_by_name.assert_not_called()


def test_create_employee_rejects_role_missing_from_database() -> None:
    service, employee_repository, role_repository = build_service()
    employee_repository.get_by_email.return_value = None
    employee_repository.get_by_employee_number.return_value = None
    role_repository.get_by_name.return_value = None

    with pytest.raises(
        ValueError,
        match="Role does not exist",
    ):
        service.create_employee(
            employee_number="EMP-001",
            full_name="Alice Martin",
            email="alice@example.com",
            password="SecurePassword123!",
            role_name="management",
        )

    employee_repository.add.assert_not_called()


def test_create_employee_rejects_invalid_email() -> None:
    service, employee_repository, role_repository = build_service()

    with pytest.raises(
        ValueError,
        match="A valid email address is required",
    ):
        service.create_employee(
            employee_number="EMP-001",
            full_name="Alice Martin",
            email="invalid-email",
            password="SecurePassword123!",
            role_name="management",
        )

    employee_repository.add.assert_not_called()
    role_repository.get_by_name.assert_not_called()

from unittest.mock import Mock

import pytest

from epic_events.models import Employee, Role
from epic_events.repositories.employee_repository import EmployeeRepository
from epic_events.repositories.role_repository import RoleRepository
from epic_events.services.auth_service import (
    hash_password,
    verify_password,
)
from epic_events.services.employee_service import (
    CurrentEmployeeDeletionError,
    EmployeeNotFoundError,
    EmployeeService,
)
from epic_events.services.jwt_service import TokenPayload
from epic_events.services.permission_service import PermissionDeniedError


def build_service() -> tuple[EmployeeService, Mock, Mock]:
    """Create an employee service with simulated repositories."""

    employee_repository = Mock(spec=EmployeeRepository)
    role_repository = Mock(spec=RoleRepository)

    service = EmployeeService(
        employee_repository,
        role_repository,
    )

    return service, employee_repository, role_repository


def make_identity(
    *,
    employee_id: int = 1,
    role: str = "management",
) -> Mock:
    """Create a simulated authenticated employee identity."""

    identity = Mock(spec=TokenPayload)
    identity.employee_id = employee_id
    identity.role = role
    return identity


def make_employee(
    *,
    employee_id: int = 2,
    employee_number: str = "EMP-002",
    full_name: str = "Alice Martin",
    email: str = "alice@example.com",
    role_name: str = "sales",
) -> Employee:
    """Create an employee used by the service tests."""

    role = Role(
        id=2,
        name=role_name,
    )

    return Employee(
        id=employee_id,
        employee_number=employee_number,
        full_name=full_name,
        email=email,
        password_hash=hash_password("ExistingPassword123!"),
        role=role,
    )


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
    existing_employee = make_employee()
    employee_repository.get_by_email.return_value = existing_employee

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
    existing_employee = make_employee()
    employee_repository.get_by_email.return_value = None
    employee_repository.get_by_employee_number.return_value = existing_employee

    with pytest.raises(
        ValueError,
        match="employee with this employee number already exists",
    ):
        service.create_employee(
            employee_number="EMP-002",
            full_name="Alice Martin",
            email="another@example.com",
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


def test_management_can_list_employees() -> None:
    service, employee_repository, _ = build_service()
    identity = make_identity()
    expected_employees = [make_employee()]
    employee_repository.list_all.return_value = expected_employees

    employees = service.list_employees(identity)

    assert employees == expected_employees
    employee_repository.list_all.assert_called_once_with()


def test_sales_cannot_list_employees() -> None:
    service, employee_repository, _ = build_service()
    identity = make_identity(
        employee_id=2,
        role="sales",
    )

    with pytest.raises(PermissionDeniedError):
        service.list_employees(identity)

    employee_repository.list_all.assert_not_called()


def test_management_can_get_employee() -> None:
    service, employee_repository, _ = build_service()
    identity = make_identity()
    expected_employee = make_employee()
    employee_repository.get_by_id.return_value = expected_employee

    employee = service.get_employee(
        identity,
        employee_id=2,
    )

    assert employee is expected_employee
    employee_repository.get_by_id.assert_called_once_with(2)


def test_get_employee_rejects_unknown_employee() -> None:
    service, employee_repository, _ = build_service()
    identity = make_identity()
    employee_repository.get_by_id.return_value = None

    with pytest.raises(
        EmployeeNotFoundError,
        match="Employee 999 was not found",
    ):
        service.get_employee(
            identity,
            employee_id=999,
        )


def test_management_can_update_employee_without_changing_password() -> None:
    service, employee_repository, role_repository = build_service()
    identity = make_identity()
    employee = make_employee()
    original_password_hash = employee.password_hash
    support_role = Role(
        id=3,
        name="support",
    )

    employee_repository.get_by_id.return_value = employee
    employee_repository.get_by_email.return_value = employee
    employee_repository.get_by_employee_number.return_value = employee
    employee_repository.save.side_effect = lambda saved_employee: saved_employee
    role_repository.get_by_name.return_value = support_role

    updated_employee = service.update_employee(
        identity,
        employee_id=2,
        employee_number=" EMP-002 ",
        full_name=" Alice Dupont ",
        email=" ALICE@EXAMPLE.COM ",
        role_name=" SUPPORT ",
    )

    assert updated_employee.employee_number == "EMP-002"
    assert updated_employee.full_name == "Alice Dupont"
    assert updated_employee.email == "alice@example.com"
    assert updated_employee.role is support_role
    assert updated_employee.password_hash == original_password_hash
    employee_repository.save.assert_called_once_with(employee)


def test_management_can_update_employee_password() -> None:
    service, employee_repository, role_repository = build_service()
    identity = make_identity()
    employee = make_employee()
    sales_role = Role(
        id=2,
        name="sales",
    )

    employee_repository.get_by_id.return_value = employee
    employee_repository.get_by_email.return_value = employee
    employee_repository.get_by_employee_number.return_value = employee
    employee_repository.save.side_effect = lambda saved_employee: saved_employee
    role_repository.get_by_name.return_value = sales_role

    updated_employee = service.update_employee(
        identity,
        employee_id=2,
        employee_number="EMP-002",
        full_name="Alice Martin",
        email="alice@example.com",
        role_name="sales",
        password="NewSecurePassword123!",
    )

    assert verify_password(
        "NewSecurePassword123!",
        updated_employee.password_hash,
    )
    employee_repository.save.assert_called_once_with(employee)


def test_update_employee_rejects_duplicate_email() -> None:
    service, employee_repository, role_repository = build_service()
    identity = make_identity()
    employee = make_employee()
    another_employee = make_employee(
        employee_id=3,
        employee_number="EMP-003",
        email="other@example.com",
    )

    employee_repository.get_by_id.return_value = employee
    employee_repository.get_by_email.return_value = another_employee

    with pytest.raises(
        ValueError,
        match="employee with this email already exists",
    ):
        service.update_employee(
            identity,
            employee_id=2,
            employee_number="EMP-002",
            full_name="Alice Martin",
            email="other@example.com",
            role_name="sales",
        )

    employee_repository.save.assert_not_called()
    role_repository.get_by_name.assert_not_called()


def test_sales_cannot_update_employee() -> None:
    service, employee_repository, _ = build_service()
    identity = make_identity(
        employee_id=2,
        role="sales",
    )

    with pytest.raises(PermissionDeniedError):
        service.update_employee(
            identity,
            employee_id=3,
            employee_number="EMP-003",
            full_name="Other Employee",
            email="other@example.com",
            role_name="support",
        )

    employee_repository.get_by_id.assert_not_called()
    employee_repository.save.assert_not_called()


def test_management_can_delete_another_employee() -> None:
    service, employee_repository, _ = build_service()
    identity = make_identity(employee_id=1)
    employee = make_employee(employee_id=2)
    employee_repository.get_by_id.return_value = employee

    service.delete_employee(
        identity,
        employee_id=2,
    )

    employee_repository.delete.assert_called_once_with(employee)


def test_manager_cannot_delete_current_account() -> None:
    service, employee_repository, _ = build_service()
    identity = make_identity(employee_id=1)

    with pytest.raises(
        CurrentEmployeeDeletionError,
        match="cannot delete your own employee account",
    ):
        service.delete_employee(
            identity,
            employee_id=1,
        )

    employee_repository.get_by_id.assert_not_called()
    employee_repository.delete.assert_not_called()


def test_delete_employee_rejects_unknown_employee() -> None:
    service, employee_repository, _ = build_service()
    identity = make_identity(employee_id=1)
    employee_repository.get_by_id.return_value = None

    with pytest.raises(
        EmployeeNotFoundError,
        match="Employee 999 was not found",
    ):
        service.delete_employee(
            identity,
            employee_id=999,
        )

    employee_repository.delete.assert_not_called()

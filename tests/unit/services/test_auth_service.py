from unittest.mock import Mock

import pytest

from epic_events.models import Employee
from epic_events.repositories.employee_repository import EmployeeRepository
from epic_events.services.auth_service import (
    InvalidCredentialsError,
    authenticate_employee,
    hash_password,
    verify_password,
)


def test_hash_password_returns_argon2_hash() -> None:
    password = "TestPassword123!"

    password_hash = hash_password(password)

    assert password_hash.startswith("$argon2")
    assert password_hash != password


def test_verify_password_accepts_correct_password() -> None:
    password = "TestPassword123!"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True


def test_verify_password_rejects_incorrect_password() -> None:
    password_hash = hash_password("TestPassword123!")

    assert verify_password("WrongPassword123!", password_hash) is False


def test_hash_password_rejects_short_password() -> None:
    with pytest.raises(ValueError, match="at least 12 characters"):
        hash_password("TooShort1!")


def test_verify_password_rejects_invalid_hash() -> None:
    assert verify_password("TestPassword123!", "invalid-hash") is False


def test_authenticate_employee_returns_employee() -> None:
    repository = Mock(spec=EmployeeRepository)
    employee = Mock(spec=Employee)
    employee.password_hash = hash_password("TestPassword123!")
    repository.get_by_email.return_value = employee

    result = authenticate_employee(
        repository,
        email=" MANAGER@EXAMPLE.COM ",
        password="TestPassword123!",
    )

    assert result is employee
    repository.get_by_email.assert_called_once_with("manager@example.com")


def test_authenticate_employee_rejects_unknown_email() -> None:
    repository = Mock(spec=EmployeeRepository)
    repository.get_by_email.return_value = None

    with pytest.raises(
        InvalidCredentialsError,
        match="Invalid email or password",
    ):
        authenticate_employee(
            repository,
            email="unknown@example.com",
            password="TestPassword123!",
        )


def test_authenticate_employee_rejects_wrong_password() -> None:
    repository = Mock(spec=EmployeeRepository)
    employee = Mock(spec=Employee)
    employee.password_hash = hash_password("TestPassword123!")
    repository.get_by_email.return_value = employee

    with pytest.raises(
        InvalidCredentialsError,
        match="Invalid email or password",
    ):
        authenticate_employee(
            repository,
            email="manager@example.com",
            password="WrongPassword123!",
        )


def test_hash_password_uses_random_salt() -> None:
    """Generate a different salted hash for the same password."""

    password = "SecurePassword123!"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash)
    assert verify_password(password, second_hash)

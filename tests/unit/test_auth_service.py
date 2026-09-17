from unittest.mock import Mock

import pytest

from epic_events.models import Employee
from epic_events.repositories.employee_repository import EmployeeRepository
from epic_events.services import auth_service
from epic_events.services.auth_service import (
    InvalidCredentialsError,
    authenticate_employee,
    hash_password,
    password_needs_rehash,
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


def test_invalid_hash_needs_rehash() -> None:
    assert password_needs_rehash("invalid-hash") is True


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


def test_authenticate_employee_upgrades_old_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = Mock(spec=EmployeeRepository)
    employee = Mock(spec=Employee)
    employee.password_hash = "old-valid-hash"
    repository.get_by_email.return_value = employee

    monkeypatch.setattr(
        auth_service,
        "verify_password",
        lambda password, password_hash: True,
    )
    monkeypatch.setattr(
        auth_service,
        "password_needs_rehash",
        lambda password_hash: True,
    )
    monkeypatch.setattr(
        auth_service,
        "hash_password",
        lambda password: "upgraded-argon2-hash",
    )

    result = authenticate_employee(
        repository,
        email="manager@example.com",
        password="TestPassword123!",
    )

    assert result is employee
    assert employee.password_hash == "upgraded-argon2-hash"

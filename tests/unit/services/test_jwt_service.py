from datetime import timedelta

import pytest

from epic_events.models import Employee, Role
from epic_events.services import jwt_service
from epic_events.services.jwt_service import (
    AuthenticationError,
    create_access_token,
    decode_access_token,
)


@pytest.fixture(autouse=True)
def use_test_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    test_secret = "test-secret-" + ("x" * 64)
    monkeypatch.setattr(
        jwt_service,
        "get_jwt_secret",
        lambda: test_secret,
    )


def build_employee(*, persisted: bool = True) -> Employee:
    role = Role(name="management")
    employee = Employee(
        employee_number="EMP-001",
        full_name="Alice Martin",
        email="alice@example.com",
        password_hash="$argon2id$test-hash",
        role=role,
    )

    if persisted:
        employee.id = 1

    return employee


def test_create_and_decode_access_token() -> None:
    employee = build_employee()

    token = create_access_token(employee)
    payload = decode_access_token(token)

    assert isinstance(token, str)
    assert payload.employee_id == 1
    assert payload.email == "alice@example.com"
    assert payload.role == "management"


def test_access_tokens_are_unique() -> None:
    employee = build_employee()

    first_token = create_access_token(employee)
    second_token = create_access_token(employee)

    assert first_token != second_token


def test_decode_access_token_rejects_expired_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    employee = build_employee()
    monkeypatch.setattr(
        jwt_service,
        "ACCESS_TOKEN_LIFETIME",
        timedelta(seconds=-1),
    )
    token = create_access_token(employee)

    with pytest.raises(
        AuthenticationError,
        match="token has expired",
    ):
        decode_access_token(token)


def test_decode_access_token_rejects_tampered_token() -> None:
    employee = build_employee()
    token = create_access_token(employee)
    tampered_token = token + "tampered"

    with pytest.raises(
        AuthenticationError,
        match="token is invalid",
    ):
        decode_access_token(tampered_token)


def test_create_access_token_rejects_unpersisted_employee() -> None:
    employee = build_employee(persisted=False)

    with pytest.raises(
        ValueError,
        match="must be persisted",
    ):
        create_access_token(employee)

import pytest

from epic_events.services.auth_service import (
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

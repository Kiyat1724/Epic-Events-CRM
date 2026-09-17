from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from epic_events.models import Employee
from epic_events.repositories.employee_repository import EmployeeRepository

MINIMUM_PASSWORD_LENGTH = 12

password_hasher = PasswordHasher()
DUMMY_PASSWORD_HASH = password_hasher.hash("DummyPasswordUsedForTimingProtection123!")


class InvalidCredentialsError(Exception):
    """Represent invalid authentication credentials."""


def hash_password(password: str) -> str:
    """Hash a password with Argon2."""

    if len(password) < MINIMUM_PASSWORD_LENGTH:
        raise ValueError(
            "The password must contain at least "
            f"{MINIMUM_PASSWORD_LENGTH} characters."
        )

    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether a password matches an Argon2 hash."""

    try:
        return password_hasher.verify(
            password_hash,
            password,
        )
    except (VerifyMismatchError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """Return whether an existing hash should be upgraded."""

    try:
        return password_hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True


def authenticate_employee(
    employee_repository: EmployeeRepository,
    *,
    email: str,
    password: str,
) -> Employee:
    """Authenticate an employee without revealing which credential failed."""

    normalized_email = email.strip().lower()
    employee = employee_repository.get_by_email(normalized_email)

    password_hash = (
        employee.password_hash if employee is not None else DUMMY_PASSWORD_HASH
    )
    password_is_valid = verify_password(password, password_hash)

    if employee is None or not password_is_valid:
        raise InvalidCredentialsError("Invalid email or password.")

    if password_needs_rehash(employee.password_hash):
        employee.password_hash = hash_password(password)

    return employee

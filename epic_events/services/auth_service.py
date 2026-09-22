from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from epic_events.models import Employee
from epic_events.repositories.employee_repository import EmployeeRepository

MINIMUM_PASSWORD_LENGTH = 12

password_hasher = PasswordHasher()


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


def authenticate_employee(
    employee_repository: EmployeeRepository,
    *,
    email: str,
    password: str,
) -> Employee:
    """Authenticate an employee with an email and password."""

    normalized_email = email.strip().lower()
    employee = employee_repository.get_by_email(normalized_email)

    if employee is None:
        raise InvalidCredentialsError("Invalid email or password.")

    if not verify_password(password, employee.password_hash):
        raise InvalidCredentialsError("Invalid email or password.")

    return employee

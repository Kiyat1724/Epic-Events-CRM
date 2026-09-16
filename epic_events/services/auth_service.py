from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

MINIMUM_PASSWORD_LENGTH = 12

password_hasher = PasswordHasher()


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

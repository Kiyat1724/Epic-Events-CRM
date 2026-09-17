from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from epic_events.config import settings
from epic_events.models import Employee

JWT_ALGORITHM = "HS256"
JWT_ISSUER = "epic-events-crm"
JWT_AUDIENCE = "epic-events-cli"
ACCESS_TOKEN_LIFETIME = timedelta(hours=8)


class AuthenticationError(Exception):
    """Represent an authentication or token validation failure."""


@dataclass(frozen=True, slots=True)
class TokenPayload:
    """Contain the validated identity extracted from an access token."""

    employee_id: int
    email: str
    role: str
    expires_at: datetime


def get_jwt_secret() -> str:
    """Return the JWT secret after validating its strength."""

    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET is not configured.")

    if len(settings.jwt_secret) < 32:
        raise RuntimeError("JWT_SECRET must contain at least 32 characters.")

    return settings.jwt_secret


def create_access_token(employee: Employee) -> str:
    """Create a signed access token for a persisted employee."""

    if employee.id is None:
        raise ValueError("The employee must be persisted before creating a token.")

    issued_at = datetime.now(UTC)
    expires_at = issued_at + ACCESS_TOKEN_LIFETIME

    payload = {
        "sub": str(employee.id),
        "email": employee.email,
        "role": employee.role.name,
        "type": "access",
        "iat": issued_at,
        "exp": expires_at,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "jti": uuid4().hex,
    }

    return jwt.encode(
        payload,
        get_jwt_secret(),
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> TokenPayload:
    """Validate an access token and return its trusted identity."""

    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={
                "require": [
                    "sub",
                    "email",
                    "role",
                    "type",
                    "iat",
                    "exp",
                    "iss",
                    "aud",
                    "jti",
                ]
            },
        )

        if payload["type"] != "access":
            raise AuthenticationError("Invalid token type.")

        return TokenPayload(
            employee_id=int(payload["sub"]),
            email=str(payload["email"]),
            role=str(payload["role"]),
            expires_at=datetime.fromtimestamp(
                payload["exp"],
                tz=UTC,
            ),
        )

    except jwt.ExpiredSignatureError as error:
        raise AuthenticationError("The authentication token has expired.") from error
    except jwt.InvalidTokenError as error:
        raise AuthenticationError("The authentication token is invalid.") from error
    except (KeyError, TypeError, ValueError) as error:
        raise AuthenticationError(
            "The authentication token contains invalid data."
        ) from error

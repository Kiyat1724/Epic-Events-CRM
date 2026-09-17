from epic_events.services.jwt_service import TokenPayload


class PermissionDeniedError(Exception):
    """Represent an operation forbidden for the authenticated employee."""


def deny_access() -> None:
    """Raise the common permission error."""

    raise PermissionDeniedError("You do not have permission to perform this action.")


def require_management(identity: TokenPayload) -> None:
    """Allow access only to management employees."""

    if identity.role != "management":
        deny_access()


def require_sales(identity: TokenPayload) -> None:
    """Allow access only to sales employees."""

    if identity.role != "sales":
        deny_access()


def require_support(identity: TokenPayload) -> None:
    """Allow access only to support employees."""

    if identity.role != "support":
        deny_access()


def require_client_update(
    identity: TokenPayload,
    *,
    sales_contact_id: int,
) -> None:
    """Allow a salesperson to update only their own client."""

    require_sales(identity)

    if identity.employee_id != sales_contact_id:
        deny_access()


def require_contract_creation(identity: TokenPayload) -> None:
    """Allow only management employees to create contracts."""

    require_management(identity)


def require_contract_update(
    identity: TokenPayload,
    *,
    sales_contact_id: int,
) -> None:
    """Allow management or the client's salesperson to update a contract."""

    if identity.role == "management":
        return

    if identity.role == "sales" and identity.employee_id == sales_contact_id:
        return

    deny_access()


def require_event_creation(
    identity: TokenPayload,
    *,
    sales_contact_id: int,
    contract_is_signed: bool,
) -> None:
    """Allow a salesperson to create an event for their signed contract."""

    require_sales(identity)

    if identity.employee_id != sales_contact_id:
        deny_access()

    if not contract_is_signed:
        raise ValueError("An event can only be created for a signed contract.")


def require_support_assignment(identity: TokenPayload) -> None:
    """Allow only management to assign support to an event."""

    require_management(identity)


def require_event_update(
    identity: TokenPayload,
    *,
    support_contact_id: int | None,
) -> None:
    """Allow support employees to update only assigned events."""

    require_support(identity)

    if identity.employee_id != support_contact_id:
        deny_access()

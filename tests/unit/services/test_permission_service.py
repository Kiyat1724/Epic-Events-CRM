from datetime import UTC, datetime, timedelta

import pytest

from epic_events.services.jwt_service import TokenPayload
from epic_events.services.permission_service import (
    PermissionDeniedError,
    require_client_update,
    require_contract_creation,
    require_contract_update,
    require_event_creation,
    require_event_update,
    require_management,
    require_support_assignment,
)


def build_identity(
    role: str,
    *,
    employee_id: int = 1,
) -> TokenPayload:
    return TokenPayload(
        employee_id=employee_id,
        email=f"{role}@example.com",
        role=role,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )


def test_management_can_manage_employees() -> None:
    identity = build_identity("management")

    require_management(identity)


def test_sales_cannot_manage_employees() -> None:
    identity = build_identity("sales")

    with pytest.raises(PermissionDeniedError):
        require_management(identity)


def test_management_can_create_contract() -> None:
    identity = build_identity("management")

    require_contract_creation(identity)


def test_sales_can_update_own_client() -> None:
    identity = build_identity("sales", employee_id=10)

    require_client_update(
        identity,
        sales_contact_id=10,
    )


def test_sales_cannot_update_another_salespersons_client() -> None:
    identity = build_identity("sales", employee_id=10)

    with pytest.raises(PermissionDeniedError):
        require_client_update(
            identity,
            sales_contact_id=20,
        )


@pytest.mark.parametrize(
    ("role", "employee_id", "sales_contact_id"),
    [
        ("management", 1, 20),
        ("sales", 10, 10),
    ],
)
def test_authorized_employee_can_update_contract(
    role: str,
    employee_id: int,
    sales_contact_id: int,
) -> None:
    identity = build_identity(
        role,
        employee_id=employee_id,
    )

    require_contract_update(
        identity,
        sales_contact_id=sales_contact_id,
    )


def test_sales_cannot_create_event_for_unsigned_contract() -> None:
    identity = build_identity("sales", employee_id=10)

    with pytest.raises(
        ValueError,
        match="signed contract",
    ):
        require_event_creation(
            identity,
            sales_contact_id=10,
            contract_is_signed=False,
        )


def test_support_can_update_assigned_event() -> None:
    identity = build_identity("support", employee_id=30)

    require_event_update(
        identity,
        support_contact_id=30,
    )


def test_support_cannot_update_unassigned_event() -> None:
    identity = build_identity("support", employee_id=30)

    with pytest.raises(PermissionDeniedError):
        require_event_update(
            identity,
            support_contact_id=None,
        )


def test_only_management_can_assign_support() -> None:
    management = build_identity("management")
    sales = build_identity("sales")

    require_support_assignment(management)

    with pytest.raises(PermissionDeniedError):
        require_support_assignment(sales)

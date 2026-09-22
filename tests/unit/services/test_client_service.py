from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from epic_events.models import Client
from epic_events.repositories.client_repository import ClientRepository
from epic_events.services.client_service import (
    ClientNotFoundError,
    ClientService,
)
from epic_events.services.jwt_service import TokenPayload
from epic_events.services.permission_service import PermissionDeniedError


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


def test_list_clients_returns_all_clients() -> None:
    repository = Mock(spec=ClientRepository)
    clients = [
        Mock(spec=Client),
        Mock(spec=Client),
    ]
    repository.list_all.return_value = clients
    service = ClientService(repository)

    result = service.list_clients()

    assert result == clients
    repository.list_all.assert_called_once_with()


def test_get_client_returns_existing_client() -> None:
    repository = Mock(spec=ClientRepository)
    client = Mock(spec=Client)
    repository.get_by_id.return_value = client
    service = ClientService(repository)

    result = service.get_client(client_id=1)

    assert result is client
    repository.get_by_id.assert_called_once_with(1)


def test_get_client_rejects_unknown_client() -> None:
    repository = Mock(spec=ClientRepository)
    repository.get_by_id.return_value = None
    service = ClientService(repository)

    with pytest.raises(
        ClientNotFoundError,
        match="Client not found",
    ):
        service.get_client(client_id=999)


def test_sales_employee_creates_owned_client() -> None:
    repository = Mock(spec=ClientRepository)
    repository.add.side_effect = lambda client: client
    service = ClientService(repository)
    identity = build_identity("sales", employee_id=2)

    client = service.create_client(
        identity,
        full_name=" Kevin Casey ",
        email=" KEVIN@STARTUP.IO ",
        phone=" +33 6 12 34 56 77 ",
        company_name=" Cool IT SECU ",
    )

    assert client.full_name == "Kevin Casey"
    assert client.email == "kevin@startup.io"
    assert client.phone == "+33 6 12 34 56 77"
    assert client.company_name == "Cool IT SECU"
    assert client.sales_contact_id == 2
    repository.add.assert_called_once_with(client)


def test_management_cannot_create_client() -> None:
    repository = Mock(spec=ClientRepository)
    service = ClientService(repository)
    identity = build_identity("management")

    with pytest.raises(PermissionDeniedError):
        service.create_client(
            identity,
            full_name="Kevin Casey",
            email="kevin@startup.io",
            phone="+33 6 12 34 56 77",
            company_name="Cool IT SECU",
        )

    repository.add.assert_not_called()


def test_sales_employee_updates_owned_client() -> None:
    repository = Mock(spec=ClientRepository)
    client = Client(
        full_name="Kevin Casey",
        email="kevin@startup.io",
        phone="+33 6 12 34 56 77",
        company_name="Cool IT SECU",
        sales_contact_id=2,
    )
    repository.get_by_id.return_value = client
    repository.save.side_effect = lambda saved_client: saved_client
    service = ClientService(repository)
    identity = build_identity("sales", employee_id=2)

    result = service.update_client(
        identity,
        client_id=1,
        full_name="Kevin Casey",
        email="kevin@startup.io",
        phone="+33 6 98 76 54 32",
        company_name="Cool IT Security",
    )

    assert result.phone == "+33 6 98 76 54 32"
    assert result.company_name == "Cool IT Security"
    assert result.updated_at is not None
    repository.save.assert_called_once_with(client)


def test_sales_employee_cannot_update_another_client() -> None:
    repository = Mock(spec=ClientRepository)
    client = Client(
        full_name="Kevin Casey",
        email="kevin@startup.io",
        phone="+33 6 12 34 56 77",
        company_name="Cool IT SECU",
        sales_contact_id=99,
    )
    repository.get_by_id.return_value = client
    service = ClientService(repository)
    identity = build_identity("sales", employee_id=2)

    with pytest.raises(PermissionDeniedError):
        service.update_client(
            identity,
            client_id=1,
            full_name="Kevin Casey",
            email="kevin@startup.io",
            phone="+33 6 98 76 54 32",
            company_name="Cool IT Security",
        )

    repository.save.assert_not_called()

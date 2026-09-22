from datetime import UTC, datetime

from epic_events.models import Client
from epic_events.repositories.client_repository import ClientRepository
from epic_events.services.jwt_service import TokenPayload
from epic_events.services.permission_service import (
    require_client_update,
    require_sales,
)


class ClientNotFoundError(Exception):
    """Represent a requested client that does not exist."""


class ClientService:
    """Apply business rules related to clients."""

    def __init__(self, repository: ClientRepository) -> None:
        self.repository = repository

    def list_clients(self) -> list[Client]:
        """Return all clients."""

        return self.repository.list_all()

    def get_client(
        self,
        *,
        client_id: int,
    ) -> Client:
        """Return one client."""

        client = self.repository.get_by_id(client_id)

        if client is None:
            raise ClientNotFoundError("Client not found.")

        return client

    def create_client(
        self,
        identity: TokenPayload,
        *,
        full_name: str,
        email: str,
        phone: str,
        company_name: str,
    ) -> Client:
        """Create a client owned by the authenticated salesperson."""

        require_sales(identity)
        normalized_data = self._normalize_and_validate(
            full_name=full_name,
            email=email,
            phone=phone,
            company_name=company_name,
        )

        client = Client(
            **normalized_data,
            sales_contact_id=identity.employee_id,
        )
        return self.repository.add(client)

    def update_client(
        self,
        identity: TokenPayload,
        *,
        client_id: int,
        full_name: str,
        email: str,
        phone: str,
        company_name: str,
    ) -> Client:
        """Update a client owned by the authenticated salesperson."""

        client = self.repository.get_by_id(client_id)
        if client is None:
            raise ClientNotFoundError("Client not found.")

        require_client_update(
            identity,
            sales_contact_id=client.sales_contact_id,
        )
        normalized_data = self._normalize_and_validate(
            full_name=full_name,
            email=email,
            phone=phone,
            company_name=company_name,
        )

        client.full_name = normalized_data["full_name"]
        client.email = normalized_data["email"]
        client.phone = normalized_data["phone"]
        client.company_name = normalized_data["company_name"]
        client.updated_at = datetime.now(UTC)

        return self.repository.save(client)

    @staticmethod
    def _normalize_and_validate(
        *,
        full_name: str,
        email: str,
        phone: str,
        company_name: str,
    ) -> dict[str, str]:
        normalized_data = {
            "full_name": full_name.strip(),
            "email": email.strip().lower(),
            "phone": phone.strip(),
            "company_name": company_name.strip(),
        }

        if not normalized_data["full_name"]:
            raise ValueError("Client full name is required.")

        if not normalized_data["email"] or "@" not in normalized_data["email"]:
            raise ValueError("A valid client email is required.")

        if not normalized_data["phone"]:
            raise ValueError("Client phone is required.")

        if not normalized_data["company_name"]:
            raise ValueError("Client company name is required.")

        return normalized_data

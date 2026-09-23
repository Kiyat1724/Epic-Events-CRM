from decimal import Decimal, InvalidOperation

import click

from epic_events.database import session_scope
from epic_events.models import Contract
from epic_events.repositories.client_repository import ClientRepository
from epic_events.repositories.contract_repository import ContractRepository
from epic_events.services.contract_service import (
    ContractClientNotFoundError,
    ContractNotFoundError,
    ContractService,
)
from epic_events.services.jwt_service import (
    AuthenticationError,
    TokenPayload,
)
from epic_events.services.permission_service import (
    PermissionDeniedError,
    require_contract_creation,
    require_contract_update,
)
from epic_events.services.session_service import get_current_identity


def get_authenticated_identity() -> TokenPayload:
    """Return the CLI identity or convert the error for Click."""

    try:
        return get_current_identity()
    except AuthenticationError as error:
        raise click.ClickException(str(error)) from error


def prompt_amount(
    label: str,
    *,
    default: Decimal | None = None,
) -> Decimal:
    """Prompt until the user enters a non-negative decimal amount."""

    while True:
        default_value = str(default) if default is not None else None
        raw_value = click.prompt(
            label,
            type=str,
            default=default_value,
        )
        normalized_value = raw_value.strip().replace(",", ".")

        try:
            amount = Decimal(normalized_value)
        except InvalidOperation:
            click.echo("Enter a valid decimal amount.")
            continue

        if amount < 0:
            click.echo("The amount cannot be negative.")
            continue

        return amount


def display_contract(contract: Contract) -> None:
    """Display one contract in the terminal."""

    click.echo(f"ID: {contract.id}")
    click.echo(f"Client ID: {contract.client_id}")
    click.echo(f"Client name: {contract.client.full_name}")
    click.echo("Sales contact ID: " f"{contract.client.sales_contact_id}")
    click.echo(f"Total amount: {contract.total_amount}")
    click.echo(f"Remaining amount: {contract.remaining_amount}")
    click.echo(f"Created at: {contract.created_at}")
    click.echo(f"Signed: {contract.signed}")


def build_service(session: object) -> ContractService:
    """Build the contract service for one database session."""

    return ContractService(
        contract_repository=ContractRepository(session),
        client_repository=ClientRepository(session),
    )


@click.group()
def contracts() -> None:
    """Manage Epic Events contracts."""


@contracts.command("list")
def list_contracts_command() -> None:
    """List every contract."""

    get_authenticated_identity()

    with session_scope() as session:
        contract_list = build_service(session).list_contracts()

        if not contract_list:
            click.echo("No contracts found.")
            return

        for index, contract in enumerate(contract_list):
            if index:
                click.echo("-" * 40)
            display_contract(contract)


@contracts.command("show")
@click.argument("contract_id", type=int)
def show_contract_command(contract_id: int) -> None:
    """Display one contract."""

    get_authenticated_identity()

    try:
        with session_scope() as session:
            contract = build_service(session).get_contract(
                contract_id=contract_id,
            )
            display_contract(contract)
    except ContractNotFoundError as error:
        raise click.ClickException(str(error)) from error


@contracts.command("unsigned")
def list_unsigned_contracts_command() -> None:
    """List contracts that have not been signed."""

    get_authenticated_identity()

    with session_scope() as session:
        contract_list = build_service(session).list_unsigned_contracts()

        if not contract_list:
            click.echo("No unsigned contracts found.")
            return

        for index, contract in enumerate(contract_list):
            if index:
                click.echo("-" * 40)
            display_contract(contract)


@contracts.command("unpaid")
def list_unpaid_contracts_command() -> None:
    """List contracts that are not fully paid."""

    get_authenticated_identity()

    with session_scope() as session:
        contract_list = build_service(session).list_unpaid_contracts()

        if not contract_list:
            click.echo("No unpaid contracts found.")
            return

        for index, contract in enumerate(contract_list):
            if index:
                click.echo("-" * 40)
            display_contract(contract)


@contracts.command("create")
def create_contract_command() -> None:
    """Create a contract as a management employee."""

    identity = get_authenticated_identity()

    try:
        require_contract_creation(identity)
    except PermissionDeniedError as error:
        raise click.ClickException(str(error)) from error

    client_id = click.prompt(
        "Client ID",
        type=click.IntRange(min=1),
    )
    total_amount = prompt_amount("Total amount")
    remaining_amount = prompt_amount("Remaining amount")
    signed = click.confirm(
        "Is the contract signed?",
        default=False,
    )

    try:
        with session_scope() as session:
            contract = build_service(session).create_contract(
                identity,
                client_id=client_id,
                total_amount=total_amount,
                remaining_amount=remaining_amount,
                signed=signed,
            )
            contract_id = contract.id

    except (
        ContractClientNotFoundError,
        PermissionDeniedError,
        ValueError,
    ) as error:
        raise click.ClickException(str(error)) from error

    click.secho(
        f"Contract {contract_id} created successfully.",
        fg="green",
    )


@contracts.command("update")
@click.argument("contract_id", type=int)
def update_contract_command(contract_id: int) -> None:
    """Update a contract with role and ownership controls."""

    identity = get_authenticated_identity()

    try:
        with session_scope() as session:
            service = build_service(session)
            existing_contract = service.get_contract(
                contract_id=contract_id,
            )
            require_contract_update(
                identity,
                sales_contact_id=(existing_contract.client.sales_contact_id),
            )

            total_amount = prompt_amount(
                "Total amount",
                default=existing_contract.total_amount,
            )
            remaining_amount = prompt_amount(
                "Remaining amount",
                default=existing_contract.remaining_amount,
            )
            signed = click.confirm(
                "Is the contract signed?",
                default=existing_contract.signed,
            )

            contract = service.update_contract(
                identity,
                contract_id=contract_id,
                total_amount=total_amount,
                remaining_amount=remaining_amount,
                signed=signed,
            )
            updated_contract_id = contract.id

    except (
        ContractNotFoundError,
        PermissionDeniedError,
        ValueError,
    ) as error:
        raise click.ClickException(str(error)) from error

    click.secho(
        f"Contract {updated_contract_id} updated successfully.",
        fg="green",
    )

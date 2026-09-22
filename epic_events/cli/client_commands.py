import click

from epic_events.database import session_scope
from epic_events.models import Client
from epic_events.repositories.client_repository import ClientRepository
from epic_events.services.client_service import (
    ClientNotFoundError,
    ClientService,
)
from epic_events.services.jwt_service import (
    AuthenticationError,
    TokenPayload,
)
from epic_events.services.permission_service import (
    PermissionDeniedError,
    require_client_update,
    require_sales,
)
from epic_events.services.session_service import get_current_identity


def get_authenticated_identity() -> TokenPayload:
    """Return the CLI identity or convert the error for Click."""

    try:
        return get_current_identity()
    except AuthenticationError as error:
        raise click.ClickException(str(error)) from error


def display_client(client: Client) -> None:
    """Display one client in the terminal."""

    click.echo(f"ID: {client.id}")
    click.echo(f"Name: {client.full_name}")
    click.echo(f"Email: {client.email}")
    click.echo(f"Phone: {client.phone}")
    click.echo(f"Company: {client.company_name}")
    click.echo(f"Sales contact ID: {client.sales_contact_id}")
    click.echo(f"Created at: {client.created_at}")
    click.echo(f"Updated at: {client.updated_at}")


@click.group()
def clients() -> None:
    """Manage Epic Events clients."""


@clients.command("list")
def list_clients_command() -> None:
    """List every client."""

    get_authenticated_identity()

    with session_scope() as session:
        service = ClientService(ClientRepository(session))
        client_list = service.list_clients()

        if not client_list:
            click.echo("No clients found.")
            return

        for index, client in enumerate(client_list):
            if index:
                click.echo("-" * 40)
            display_client(client)


@clients.command("show")
@click.argument("client_id", type=int)
def show_client_command(client_id: int) -> None:
    """Display one client."""

    get_authenticated_identity()

    try:
        with session_scope() as session:
            service = ClientService(ClientRepository(session))
            client = service.get_client(
                client_id=client_id,
            )
            display_client(client)

    except ClientNotFoundError as error:
        raise click.ClickException(str(error)) from error


@clients.command("create")
def create_client_command() -> None:
    """Create a client as an authenticated salesperson."""

    identity = get_authenticated_identity()

    try:
        require_sales(identity)
    except PermissionDeniedError as error:
        raise click.ClickException(str(error)) from error

    full_name = click.prompt("Full name", type=str)
    email = click.prompt("Email", type=str)
    phone = click.prompt("Phone", type=str)
    company_name = click.prompt("Company name", type=str)

    try:
        with session_scope() as session:
            service = ClientService(ClientRepository(session))
            client = service.create_client(
                identity,
                full_name=full_name,
                email=email,
                phone=phone,
                company_name=company_name,
            )
            client_id = client.id

    except (PermissionDeniedError, ValueError) as error:
        raise click.ClickException(str(error)) from error

    click.secho(
        f"Client {client_id} created successfully.",
        fg="green",
    )


@clients.command("update")
@click.argument("client_id", type=int)
def update_client_command(client_id: int) -> None:
    """Update a client owned by the authenticated salesperson."""

    identity = get_authenticated_identity()

    try:
        with session_scope() as session:
            service = ClientService(ClientRepository(session))
            existing_client = service.get_client(
                client_id=client_id,
            )
            require_client_update(
                identity,
                sales_contact_id=existing_client.sales_contact_id,
            )

            full_name = click.prompt(
                "Full name",
                default=existing_client.full_name,
            )
            email = click.prompt(
                "Email",
                default=existing_client.email,
            )
            phone = click.prompt(
                "Phone",
                default=existing_client.phone,
            )
            company_name = click.prompt(
                "Company name",
                default=existing_client.company_name,
            )

            client = service.update_client(
                identity,
                client_id=client_id,
                full_name=full_name,
                email=email,
                phone=phone,
                company_name=company_name,
            )
            updated_client_id = client.id

    except (
        ClientNotFoundError,
        PermissionDeniedError,
        ValueError,
    ) as error:
        raise click.ClickException(str(error)) from error

    click.secho(
        f"Client {updated_client_id} updated successfully.",
        fg="green",
    )

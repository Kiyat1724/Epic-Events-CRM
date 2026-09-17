import click

from epic_events.database import session_scope
from epic_events.repositories.employee_repository import EmployeeRepository
from epic_events.services.auth_service import (
    InvalidCredentialsError,
    authenticate_employee,
)
from epic_events.services.jwt_service import (
    AuthenticationError,
    create_access_token,
    decode_access_token,
)
from epic_events.services.session_service import (
    delete_session_token,
    load_session_token,
    save_session_token,
)


@click.command()
def login() -> None:
    """Authenticate an employee and create a local session."""

    email = click.prompt("Email", type=str)
    password = click.prompt(
        "Password",
        type=str,
        hide_input=True,
    )

    try:
        with session_scope() as session:
            repository = EmployeeRepository(session)
            employee = authenticate_employee(
                repository,
                email=email,
                password=password,
            )
            token = create_access_token(employee)
            full_name = employee.full_name
            role_name = employee.role.name

    except InvalidCredentialsError as error:
        raise click.ClickException(str(error)) from error

    save_session_token(token)
    click.secho(
        f"Login successful. Welcome {full_name} ({role_name}).",
        fg="green",
    )


@click.command()
def status() -> None:
    """Display the currently authenticated employee."""

    token = load_session_token()
    if token is None:
        raise click.ClickException("No active session. Use the login command.")

    try:
        payload = decode_access_token(token)
    except AuthenticationError as error:
        delete_session_token()
        raise click.ClickException(str(error)) from error

    click.echo(f"Employee ID: {payload.employee_id}")
    click.echo(f"Email: {payload.email}")
    click.echo(f"Role: {payload.role}")
    click.echo("Token expires at: " f"{payload.expires_at.isoformat()}")


@click.command()
def logout() -> None:
    """Delete the current local session."""

    if delete_session_token():
        click.secho("Logout successful.", fg="green")
        return

    click.echo("No active session.")

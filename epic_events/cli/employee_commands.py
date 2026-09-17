import click

from epic_events.database import session_scope
from epic_events.repositories.employee_repository import EmployeeRepository
from epic_events.repositories.role_repository import RoleRepository
from epic_events.services.employee_service import EmployeeService
from epic_events.services.jwt_service import AuthenticationError
from epic_events.services.permission_service import (
    PermissionDeniedError,
    require_management,
)
from epic_events.services.session_service import get_current_identity


@click.command("bootstrap-admin")
def bootstrap_admin() -> None:
    """Create the first management employee."""

    try:
        with session_scope() as session:
            employee_repository = EmployeeRepository(session)

            if employee_repository.exists_by_role_name("management"):
                raise click.ClickException(
                    "A management employee already exists. "
                    "Use an authenticated management command instead."
                )

            employee_number = click.prompt("Employee number", type=str)
            full_name = click.prompt("Full name", type=str)
            email = click.prompt("Email", type=str)
            password = click.prompt(
                "Password",
                type=str,
                hide_input=True,
                confirmation_prompt=True,
            )

            role_repository = RoleRepository(session)
            service = EmployeeService(
                employee_repository=employee_repository,
                role_repository=role_repository,
            )

            employee = service.create_employee(
                employee_number=employee_number,
                full_name=full_name,
                email=email,
                password=password,
                role_name="management",
            )
            created_employee_number = employee.employee_number

    except ValueError as error:
        raise click.ClickException(str(error)) from error

    click.secho(
        f"Management employee {created_employee_number} created successfully.",
        fg="green",
    )


@click.group()
def employees() -> None:
    """Manage Epic Events employees."""


@employees.command("create")
def create_employee_command() -> None:
    """Create an employee as an authenticated manager."""

    try:
        identity = get_current_identity()
        require_management(identity)
    except (AuthenticationError, PermissionDeniedError) as error:
        raise click.ClickException(str(error)) from error

    employee_number = click.prompt("Employee number", type=str)
    full_name = click.prompt("Full name", type=str)
    email = click.prompt("Email", type=str)
    role_name = click.prompt(
        "Role",
        type=click.Choice(
            ["management", "sales", "support"],
            case_sensitive=False,
        ),
    )
    password = click.prompt(
        "Password",
        type=str,
        hide_input=True,
        confirmation_prompt=True,
    )

    try:
        with session_scope() as session:
            service = EmployeeService(
                employee_repository=EmployeeRepository(session),
                role_repository=RoleRepository(session),
            )
            employee = service.create_employee(
                employee_number=employee_number,
                full_name=full_name,
                email=email,
                password=password,
                role_name=role_name,
            )
            created_employee_number = employee.employee_number

    except ValueError as error:
        raise click.ClickException(str(error)) from error

    click.secho(
        f"Employee {created_employee_number} created successfully.",
        fg="green",
    )

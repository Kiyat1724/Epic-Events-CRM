import click
from sqlalchemy.orm import Session

from epic_events.database import session_scope
from epic_events.models import Employee
from epic_events.repositories.employee_repository import EmployeeRepository
from epic_events.repositories.role_repository import RoleRepository
from epic_events.services.employee_service import (
    CurrentEmployeeDeletionError,
    EmployeeNotFoundError,
    EmployeeService,
)
from epic_events.services.jwt_service import (
    AuthenticationError,
    TokenPayload,
)
from epic_events.services.permission_service import (
    PermissionDeniedError,
    require_management,
)
from epic_events.services.session_service import get_current_identity


def get_authenticated_manager() -> TokenPayload:
    """Return the authenticated management identity."""

    try:
        identity = get_current_identity()
        require_management(identity)
        return identity
    except (AuthenticationError, PermissionDeniedError) as error:
        raise click.ClickException(str(error)) from error


def build_employee_service(session: Session) -> EmployeeService:
    """Create an employee service using the current database session."""

    return EmployeeService(
        employee_repository=EmployeeRepository(session),
        role_repository=RoleRepository(session),
    )


def display_employee(employee: Employee) -> None:
    """Display one employee without exposing their password hash."""

    click.echo(f"ID: {employee.id}")
    click.echo(f"Employee number: {employee.employee_number}")
    click.echo(f"Full name: {employee.full_name}")
    click.echo(f"Email: {employee.email}")
    click.echo(f"Role: {employee.role.name}")


def display_employee_list(
    employee_list: list[Employee],
) -> None:
    """Display a collection of employees."""

    if not employee_list:
        click.echo("No employees found.")
        return

    for index, employee in enumerate(employee_list):
        if index:
            click.echo("-" * 40)

        display_employee(employee)


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

            employee_number = click.prompt(
                "Employee number",
                type=str,
            )
            full_name = click.prompt(
                "Full name",
                type=str,
            )
            email = click.prompt(
                "Email",
                type=str,
            )
            password = click.prompt(
                "Password",
                type=str,
                hide_input=True,
                confirmation_prompt=True,
            )

            service = EmployeeService(
                employee_repository=employee_repository,
                role_repository=RoleRepository(session),
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
        (f"Management employee {created_employee_number} " "created successfully."),
        fg="green",
    )


@click.group()
def employees() -> None:
    """Manage Epic Events employees."""


@employees.command("list")
def list_employees_command() -> None:
    """List every employee as an authenticated manager."""

    identity = get_authenticated_manager()

    with session_scope() as session:
        service = build_employee_service(session)
        employee_list = service.list_employees(identity)
        display_employee_list(employee_list)


@employees.command("show")
@click.argument("employee_id", type=int)
def show_employee_command(employee_id: int) -> None:
    """Display one employee as an authenticated manager."""

    identity = get_authenticated_manager()

    try:
        with session_scope() as session:
            service = build_employee_service(session)
            employee = service.get_employee(
                identity,
                employee_id=employee_id,
            )
            display_employee(employee)

    except EmployeeNotFoundError as error:
        raise click.ClickException(str(error)) from error


@employees.command("create")
def create_employee_command() -> None:
    """Create an employee as an authenticated manager."""

    get_authenticated_manager()

    employee_number = click.prompt(
        "Employee number",
        type=str,
    )
    full_name = click.prompt(
        "Full name",
        type=str,
    )
    email = click.prompt(
        "Email",
        type=str,
    )
    role_name = click.prompt(
        "Role",
        type=click.Choice(
            [
                "management",
                "sales",
                "support",
            ],
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
            service = build_employee_service(session)
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


@employees.command("update")
@click.argument("employee_id", type=int)
def update_employee_command(employee_id: int) -> None:
    """Update an employee as an authenticated manager."""

    identity = get_authenticated_manager()

    try:
        with session_scope() as session:
            service = build_employee_service(session)
            existing_employee = service.get_employee(
                identity,
                employee_id=employee_id,
            )

            employee_number = click.prompt(
                "Employee number",
                default=existing_employee.employee_number,
            )
            full_name = click.prompt(
                "Full name",
                default=existing_employee.full_name,
            )
            email = click.prompt(
                "Email",
                default=existing_employee.email,
            )
            role_name = click.prompt(
                "Role",
                type=click.Choice(
                    [
                        "management",
                        "sales",
                        "support",
                    ],
                    case_sensitive=False,
                ),
                default=existing_employee.role.name,
            )

            password = None

            if click.confirm(
                "Change the employee password?",
                default=False,
            ):
                password = click.prompt(
                    "New password",
                    type=str,
                    hide_input=True,
                    confirmation_prompt=True,
                )

            employee = service.update_employee(
                identity,
                employee_id=employee_id,
                employee_number=employee_number,
                full_name=full_name,
                email=email,
                role_name=role_name,
                password=password,
            )
            updated_employee_number = employee.employee_number

    except (
        EmployeeNotFoundError,
        PermissionDeniedError,
        ValueError,
    ) as error:
        raise click.ClickException(str(error)) from error

    click.secho(
        f"Employee {updated_employee_number} updated successfully.",
        fg="green",
    )


@employees.command("delete")
@click.argument("employee_id", type=int)
def delete_employee_command(employee_id: int) -> None:
    """Delete an employee as an authenticated manager."""

    identity = get_authenticated_manager()

    try:
        with session_scope() as session:
            service = build_employee_service(session)
            employee = service.get_employee(
                identity,
                employee_id=employee_id,
            )

            click.echo(
                f"Employee: {employee.full_name} " f"({employee.employee_number})"
            )

            if not click.confirm(
                "Are you sure you want to delete this employee?",
                default=False,
            ):
                click.echo("Deletion cancelled.")
                return

            service.delete_employee(
                identity,
                employee_id=employee_id,
            )

    except (
        CurrentEmployeeDeletionError,
        EmployeeNotFoundError,
        PermissionDeniedError,
        ValueError,
    ) as error:
        raise click.ClickException(str(error)) from error

    click.secho(
        f"Employee {employee_id} deleted successfully.",
        fg="green",
    )

import click

from epic_events.cli.auth_commands import login, logout, status
from epic_events.cli.client_commands import clients
from epic_events.cli.contract_commands import contracts
from epic_events.cli.employee_commands import bootstrap_admin, employees


@click.group()
def cli() -> None:
    """Epic Events secure CRM."""


@cli.command()
def hello() -> None:
    """Check that the application is running."""
    click.echo("Epic Events CRM is running.")


cli.add_command(bootstrap_admin)
cli.add_command(clients)
cli.add_command(contracts)
cli.add_command(employees)
cli.add_command(login)
cli.add_command(logout)
cli.add_command(status)


if __name__ == "__main__":
    cli()

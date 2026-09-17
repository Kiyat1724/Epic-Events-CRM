import click

from epic_events.cli.employee_commands import bootstrap_admin


@click.group()
def cli() -> None:
    """Epic Events secure CRM."""


@cli.command()
def hello() -> None:
    """Check that the application is running."""
    click.echo("Epic Events CRM is running.")


cli.add_command(bootstrap_admin)


if __name__ == "__main__":
    cli()

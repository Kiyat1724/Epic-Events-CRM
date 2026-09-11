import click


@click.group()
def cli():
    """Epic Events secure CRM."""
    pass


@cli.command()
def hello():
    """Check that the application is running."""
    click.echo("Epic Events CRM is running.")


if __name__ == "__main__":
    cli()

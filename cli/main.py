"""STACKMIND CLI entry point."""

import click

from . import __version__


@click.group()
@click.version_option(version=__version__, prog_name="stackmind")
def cli():
    """STACKMIND — Multi-Agent Engineering Runtime Platform."""
    pass


@cli.command()
@click.argument("project_path", type=click.Path())
@click.option("--name", "-n", default=None, help="Project name")
def init(project_path: str, name: str | None):
    """Initialize a new STACKMIND runtime."""
    click.echo(f"stackmind init {project_path} — Not yet implemented (WO-016)")


@cli.command()
@click.argument("project_path", type=click.Path(exists=True), default=".")
@click.option("--fix", is_flag=True, help="Auto-fix minor issues")
def validate(project_path: str, fix: bool):
    """Validate runtime health."""
    click.echo(f"stackmind validate {project_path} — Not yet implemented (WO-016)")


@cli.command()
@click.argument("project_path", type=click.Path(exists=True), default=".")
def doctor(project_path: str):
    """Check runtime status and compatibility."""
    click.echo(f"stackmind doctor {project_path} — Not yet implemented (WO-016)")


@cli.command()
@click.argument("project_path", type=click.Path(exists=True), default=".")
@click.option("--to", "target_version", default=None, help="Target version")
@click.option("--check", is_flag=True, help="Check pending migrations only")
@click.option("--rollback", is_flag=True, help="Rollback last migration")
def migrate(project_path: str, target_version: str | None, check: bool, rollback: bool):
    """Migrate runtime to new version."""
    click.echo(f"stackmind migrate {project_path} — Not yet implemented (WO-016)")


if __name__ == "__main__":
    cli()

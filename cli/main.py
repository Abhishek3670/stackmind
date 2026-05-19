"""STACKMIND CLI entry point."""

from pathlib import Path

import click

from . import __version__


@click.group()
@click.version_option(version=__version__, prog_name="stackmind")
def cli():
    """STACKMIND — Multi-Agent Engineering Runtime Platform."""
    pass


@cli.command()
@click.argument("project_path", type=click.Path())
@click.option("--name", "-n", default=None, help="Project name (defaults to directory name)")
@click.option(
    "--agents",
    "-a",
    default=None,
    help="Comma-separated agent list (default: claude,codex,gemini,gemma,local-llm)",
)
@click.option("--no-git", is_flag=True, help="Skip git initialization")
def init(project_path: str, name: str | None, agents: str | None, no_git: bool):
    """Initialize a new STACKMIND runtime.

    Creates a fresh multi-agent runtime at PROJECT_PATH with all required
    templates, schemas, and directory structure.

    Examples:

        stackmind init ./my-project

        stackmind init ./my-project --name "My Project"

        stackmind init ./my-project --agents claude,codex,gemini

        stackmind init ./my-project --no-git
    """
    from .init import init as run_init

    agent_list = None
    if agents:
        agent_list = [a.strip() for a in agents.split(",")]

    try:
        success = run_init(
            project_path=Path(project_path),
            name=name,
            agents=agent_list,
            no_git=no_git,
        )
        if not success:
            raise SystemExit(1)
    except RuntimeError as e:
        raise SystemExit(str(e))
    except FileNotFoundError as e:
        raise SystemExit(str(e))


@cli.command()
@click.argument("project_path", type=click.Path(exists=True), default=".")
@click.option("--fix", is_flag=True, help="Auto-fix minor issues")
def validate(project_path: str, fix: bool):
    """Validate runtime health.

    Checks schema compliance, directory structure, protocol integrity,
    and boot snapshot consistency across all four validation layers.

    Examples:

        stackmind validate

        stackmind validate ./my-project

        stackmind validate --fix
    """
    from .validate import Severity, validate as run_validate

    from rich.console import Console

    console = Console()
    result = run_validate(Path(project_path), fix=fix)

    if result.passed and not result.warnings:
        console.print("[bold green][PASS] Schema validation[/bold green]")
        console.print("[bold green][PASS] Structure validation[/bold green]")
        console.print("[bold green][PASS] Protocol compliance[/bold green]")
        console.print("[bold green][PASS] Boot integrity[/bold green]")
        console.print("\n[bold green]Runtime is healthy.[/bold green]")
    else:
        for issue in result.issues:
            if issue.severity == Severity.ERROR:
                console.print(f"[bold red][FAIL] {issue.layer}: {issue.message}[/bold red]")
            else:
                console.print(f"[bold yellow][WARN] {issue.layer}: {issue.message}[/bold yellow]")

        if result.errors:
            console.print(
                f"\n[bold red]{len(result.errors)} error(s), "
                f"{len(result.warnings)} warning(s)[/bold red]"
            )
            if not fix:
                fixable = [i for i in result.issues if i.auto_fixable]
                if fixable:
                    console.print(
                        f"\n[dim]Run `stackmind validate --fix` to auto-fix "
                        f"{len(fixable)} issue(s).[/dim]"
                    )
            raise SystemExit(1)
        else:
            console.print(
                f"\n[bold green][PASS] No errors[/bold green] "
                f"[dim]({len(result.warnings)} warning(s))[/dim]"
            )


@cli.command()
@click.argument("project_path", type=click.Path(exists=True), default=".")
def doctor(project_path: str):
    """Check runtime status and compatibility."""
    click.echo(f"stackmind doctor {project_path} — Not yet implemented (WO-016 M3)")


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

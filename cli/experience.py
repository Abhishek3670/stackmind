"""CLI commands for inspecting captured Experience Records.

Implements Phase 1 (Experience Capture) CLI tooling.
"""

from __future__ import annotations

import json
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from validators.experience.store import ExperienceStore
from validators.harness.snapshot import TrustLevel


@click.group("experience")
def experience_group():
    """Inspect and manage captured Experience Records."""
    pass


@experience_group.command("list")
@click.option(
    "--project",
    "-p",
    "project_path",
    default=".",
    type=click.Path(exists=True),
    help="Project root directory",
)
@click.option(
    "--eligible-only",
    "-e",
    is_flag=True,
    help="Filter to only learning-eligible experience records",
)
@click.option(
    "--agent",
    "-a",
    "agent_id",
    default=None,
    help="Filter by agent identifier",
)
@click.option(
    "--limit",
    "-n",
    default=20,
    type=int,
    help="Maximum records to display",
)
def list_command(project_path: str, eligible_only: bool, agent_id: str | None, limit: int):
    """List captured execution experience records."""
    console = Console()
    store = ExperienceStore(project_path)
    records = store.list_records(only_learning_eligible=eligible_only, agent_id=agent_id, limit=limit)

    if not records:
        console.print("[dim]No experience records found matching criteria.[/dim]")
        return

    table = Table(title=f"Captured Experience Records ({len(records)} shown)")
    table.add_column("Experience ID", style="bold cyan", no_wrap=True)
    table.add_column("Task ID", style="magenta")
    table.add_column("Agent", style="blue")
    table.add_column("Trust Level", justify="center")
    table.add_column("Eligible", justify="center")
    table.add_column("Outcome", justify="center")
    table.add_column("Recorded At", style="dim", no_wrap=True)

    for r in records:
        trust_style = {
            TrustLevel.LEARNING_ELIGIBLE: "[bold green]LEARNING_ELIGIBLE[/bold green]",
            TrustLevel.VERIFIED: "[bold yellow]VERIFIED[/bold yellow]",
            TrustLevel.OBSERVABLE: "[dim red]OBSERVABLE[/dim red]",
        }.get(r.trust_level, str(r.trust_level))

        eligible_str = "[green]YES[/green]" if r.learning_eligible else "[dim red]NO[/dim red]"
        outcome_style = "[green]completed[/green]" if r.outcome == "completed" else f"[red]{r.outcome}[/red]"

        table.add_row(
            r.experience_id,
            r.task_id,
            r.agent_id,
            trust_style,
            eligible_str,
            outcome_style,
            r.recorded_at[:19].replace("T", " "),
        )

    console.print(table)


@experience_group.command("show")
@click.argument("experience_id")
@click.option(
    "--project",
    "-p",
    "project_path",
    default=".",
    type=click.Path(exists=True),
    help="Project root directory",
)
@click.option(
    "--json-output",
    "-j",
    is_flag=True,
    help="Output full record as JSON",
)
def show_command(experience_id: str, project_path: str, json_output: bool):
    """Show details of a specific experience record."""
    console = Console()
    store = ExperienceStore(project_path)
    rec = store.load_record(experience_id)

    if not rec:
        console.print(f"[bold red][ERROR][/bold red] Experience record '{experience_id}' not found.")
        raise click.Abort()

    if json_output:
        console.print(json.dumps(rec.to_dict(), indent=2, sort_keys=True))
        return

    trust_color = "green" if rec.learning_eligible else "yellow" if rec.trust_level == TrustLevel.VERIFIED else "red"
    console.print(
        Panel.fit(
            f"[bold cyan]{rec.experience_id}[/bold cyan]\n"
            f"Task: [magenta]{rec.task_id}[/magenta] | Agent: [blue]{rec.agent_id}[/blue] | "
            f"Trust: [{trust_color}]{rec.trust_level.value}[/{trust_color}] | "
            f"Outcome: [bold]{rec.outcome}[/bold]",
            title="Experience Artifact",
        )
    )

    # Verification Dimensions
    v_table = Table(title="Verification Evidence")
    v_table.add_column("Dimension", style="bold")
    v_table.add_column("Status", justify="center")

    dims = rec.verification.dimensions
    for name, val in [
        ("Scope Boundary Verified", dims.scope_verified),
        ("Staged State Validated", dims.state_verified),
        ("Code Validity Verified", dims.code_verified),
        ("Behavioral Constraint Met", dims.behavioral_verified),
        ("Security Safeguards (D025)", dims.security_verified),
        ("Outcome Succeeded", dims.outcome_verified),
        ("Declaration Matches Disk", rec.verification.declaration_matches),
    ]:
        v_table.add_row(name, "[green]PASS[/green]" if val else "[red]FAIL[/red]")

    console.print(v_table)

    # Actions & Observations
    if rec.actions:
        a_table = Table(title="Actions Executed")
        a_table.add_column("Tool", style="bold yellow")
        a_table.add_column("Command / Action", style="cyan")
        a_table.add_column("Timestamp", style="dim")
        for a in rec.actions:
            a_table.add_row(a.tool, a.command_or_symbol, a.timestamp[:19].replace("T", " "))
        console.print(a_table)

    # Observed Files Diff
    diff = rec.verification.observed_diff
    if not diff.is_empty:
        diff_lines = []
        for f in diff.added:
            diff_lines.append(f"[green]+ {f}[/green]")
        for f in diff.modified:
            diff_lines.append(f"[yellow]~ {f}[/yellow]")
        for f in diff.deleted:
            diff_lines.append(f"[red]- {f}[/red]")
        console.print(Panel("\n".join(diff_lines), title="Authoritative Filesystem Diff"))


@experience_group.command("stats")
@click.option(
    "--project",
    "-p",
    "project_path",
    default=".",
    type=click.Path(exists=True),
    help="Project root directory",
)
def stats_command(project_path: str):
    """Show summary statistics of captured experience records."""
    console = Console()
    store = ExperienceStore(project_path)
    stats = store.stats()

    table = Table(title="Experience Subsystem Statistics")
    table.add_column("Metric", style="bold")
    table.add_column("Count", justify="right", style="cyan")

    table.add_row("Total Captured Records", str(stats["total"]))
    table.add_row("Learning Eligible (Top Tier)", f"[green]{stats['learning_eligible']}[/green]")
    table.add_row("Verified (Middle Tier)", f"[yellow]{stats['verified']}[/yellow]")
    table.add_row("Observable Only (Base Tier)", f"[dim red]{stats['observable']}[/dim red]")

    console.print(table)

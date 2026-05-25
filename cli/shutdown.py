"""stackmind shutdown — Agent shutdown with handoff validation.

Ensures agents properly hand off work before ending their session.
Validates handoff report exists, updates state, and archives session.
"""

import shutil
from datetime import datetime, timezone
from pathlib import Path

import yaml
from rich.console import Console

console = Console()


def _load_yaml(path: Path) -> dict | None:
    """Load YAML file, return None on error."""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_yaml(path: Path, data: dict) -> None:
    """Save data to YAML file."""
    path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")


def find_handoff_report(outbox_path: Path) -> Path | None:
    """Find the most recent handoff report in agent's outbox."""
    if not outbox_path.exists():
        return None
    
    handoffs = list(outbox_path.glob("handoff-*.md"))
    if not handoffs:
        return None
    
    # Return most recent by filename (timestamp-based)
    return sorted(handoffs, reverse=True)[0]


def archive_handoff(handoff_path: Path, outbox_path: Path) -> None:
    """Move handoff report to _read/ directory."""
    read_dir = outbox_path / "_read"
    read_dir.mkdir(parents=True, exist_ok=True)
    
    dest = read_dir / handoff_path.name
    shutil.move(str(handoff_path), str(dest))


def update_tree_status(sync_path: Path, agent: str) -> bool:
    """Update agent status to idle in TREE.yaml."""
    tree_path = sync_path / "runtime" / "TREE.yaml"
    if not tree_path.exists():
        return False
    
    data = _load_yaml(tree_path)
    if not data or "agents" not in data:
        return False
    
    if agent not in data["agents"]:
        return False
    
    data["agents"][agent]["status"] = "idle"
    data["agents"][agent]["last_task"] = "Session ended via shutdown"
    data["agents"][agent]["blockers"] = []
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    _save_yaml(tree_path, data)
    return True


def update_boot_snapshot(sync_path: Path, agent: str) -> bool:
    """Increment session_count in agent's boot snapshot."""
    boot_path = sync_path / "runtime" / "boot" / f"{agent}.boot.yaml"
    if not boot_path.exists():
        return False
    
    data = _load_yaml(boot_path)
    if not data:
        return False
    
    data["session_count"] = data.get("session_count", 0) + 1
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    _save_yaml(boot_path, data)
    return True


def shutdown(project_path: Path, agent: str, force: bool = False) -> bool:
    """Shutdown an agent session with handoff validation.

    Args:
        project_path: Root of the project containing .sync/.
        agent: Name of the agent to shutdown.
        force: If True, skip handoff validation (not recommended).

    Returns:
        True if shutdown successful, False otherwise.
    """
    sync_path = project_path / ".sync"

    if not sync_path.exists():
        console.print("[bold red][x] No .sync/ directory found[/bold red]")
        return False

    # Validate agent exists
    tree_path = sync_path / "runtime" / "TREE.yaml"
    tree_data = _load_yaml(tree_path)
    if not tree_data or agent not in tree_data.get("agents", {}):
        console.print(f"[bold red][x] Agent '{agent}' not found in TREE.yaml[/bold red]")
        return False

    outbox_path = sync_path / "outbox" / agent
    
    # Check for handoff report
    handoff = find_handoff_report(outbox_path)
    
    if not handoff and not force:
        console.print(f"[bold red][x] No handoff report found for '{agent}'[/bold red]")
        console.print(f"[dim]Expected: {outbox_path}/handoff-<timestamp>.md[/dim]")
        console.print("\n[yellow]Create a handoff report before shutdown to prevent lost work.[/yellow]")
        console.print("[dim]Use --force to skip this check (not recommended).[/dim]")
        return False

    if handoff:
        console.print(f"[green][✓] Handoff report found: {handoff.name}[/green]")
    elif force:
        console.print("[yellow][!] Forcing shutdown without handoff report[/yellow]")

    # Update TREE.yaml
    if update_tree_status(sync_path, agent):
        console.print(f"[green][✓] Updated TREE.yaml: {agent} → idle[/green]")
    else:
        console.print(f"[bold red][x] Failed to update TREE.yaml[/bold red]")
        return False

    # Update boot snapshot
    if update_boot_snapshot(sync_path, agent):
        console.print(f"[green][✓] Incremented session_count in boot snapshot[/green]")
    else:
        console.print(f"[yellow][!] Could not update boot snapshot[/yellow]")

    # Archive handoff report
    if handoff:
        archive_handoff(handoff, outbox_path)
        console.print(f"[green][✓] Archived handoff to _read/[/green]")

    console.print(f"\n[bold green]Agent '{agent}' shutdown complete.[/bold green]")
    return True

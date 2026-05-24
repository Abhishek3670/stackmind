"""stackmind migrate — Runtime migration management.

Handles schema and structure migrations between runtime versions.
Supports forward migrations and rollback via YAML manifests.
"""

import shutil
from pathlib import Path

import yaml
from rich.console import Console

console = Console()


def get_migrations_dir() -> Path:
    """Return the path to the migrations directory."""
    return Path(__file__).parent.parent / "migrations"


def _parse_version(version: str) -> tuple[int, int, int]:
    """Parse version string to tuple for comparison."""
    parts = version.split(".")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def _load_yaml(path: Path) -> dict | None:
    """Load YAML file, return None on error."""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_yaml(path: Path, data: dict) -> None:
    """Save data to YAML file."""
    path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")


def get_current_version(sync_path: Path) -> str | None:
    """Get current runtime version from RUNTIME_VERSION file."""
    version_file = sync_path / "RUNTIME_VERSION"
    if not version_file.exists():
        return None
    data = _load_yaml(version_file)
    if data:
        return data.get("version")
    return None


def get_applied_migrations(sync_path: Path) -> list[str]:
    """Get list of applied migration versions."""
    migrations_file = sync_path / "MIGRATIONS.yaml"
    if not migrations_file.exists():
        return []
    data = _load_yaml(migrations_file)
    if data and "applied" in data:
        return data["applied"]
    return []


def save_applied_migrations(sync_path: Path, applied: list[str]) -> None:
    """Save list of applied migrations."""
    migrations_file = sync_path / "MIGRATIONS.yaml"
    _save_yaml(migrations_file, {"applied": applied})


def load_migrations() -> list[dict]:
    """Load all migration manifests from migrations directory."""
    migrations_dir = get_migrations_dir()
    migrations = []
    for f in migrations_dir.glob("v*.yaml"):
        data = _load_yaml(f)
        if data and "from_version" in data and "to_version" in data:
            data["_file"] = f.name
            migrations.append(data)
    # Sort by from_version
    migrations.sort(key=lambda m: _parse_version(m["from_version"]))
    return migrations


def get_pending_migrations(current_version: str, target_version: str | None, migrations: list[dict]) -> list[dict]:
    """Get migrations that need to be applied."""
    current = _parse_version(current_version)
    pending = []
    for m in migrations:
        from_v = _parse_version(m["from_version"])
        to_v = _parse_version(m["to_version"])
        if from_v >= current:
            if target_version is None or to_v <= _parse_version(target_version):
                pending.append(m)
    return pending


def _execute_action(sync_path: Path, action: dict, direction: str) -> bool:
    """Execute a single migration action."""
    action_type = action.get("action")

    if action_type == "add_field":
        file_path = sync_path / action["file"]
        if not file_path.exists():
            return False
        data = _load_yaml(file_path)
        if data is None:
            return False
        data[action["field"]] = action.get("value")
        _save_yaml(file_path, data)
        return True

    elif action_type == "remove_field":
        file_path = sync_path / action["file"]
        if not file_path.exists():
            return False
        data = _load_yaml(file_path)
        if data is None:
            return False
        data.pop(action["field"], None)
        _save_yaml(file_path, data)
        return True

    elif action_type == "add_dir":
        dir_path = sync_path / action["path"]
        dir_path.mkdir(parents=True, exist_ok=True)
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("", encoding="utf-8")
        return True

    elif action_type == "remove_dir":
        dir_path = sync_path / action["path"]
        if dir_path.exists():
            shutil.rmtree(dir_path)
        return True

    elif action_type == "rename":
        from_path = sync_path / action["from"]
        to_path = sync_path / action["to"]
        if from_path.exists():
            to_path.parent.mkdir(parents=True, exist_ok=True)
            from_path.rename(to_path)
        return True

    elif action_type == "set_value":
        file_path = sync_path / action["file"]
        if not file_path.exists():
            return False
        data = _load_yaml(file_path)
        if data is None:
            return False
        data[action["field"]] = action["value"]
        _save_yaml(file_path, data)
        return True

    return False


def apply_migration(sync_path: Path, migration: dict) -> bool:
    """Apply a single migration (up direction)."""
    for action in migration.get("up", []):
        if not _execute_action(sync_path, action, "up"):
            return False
    return True


def rollback_migration(sync_path: Path, migration: dict) -> bool:
    """Rollback a single migration (down direction)."""
    for action in migration.get("down", []):
        if not _execute_action(sync_path, action, "down"):
            return False
    return True


def update_runtime_version(sync_path: Path, version: str) -> None:
    """Update RUNTIME_VERSION file."""
    version_file = sync_path / "RUNTIME_VERSION"
    data = _load_yaml(version_file) or {}
    data["version"] = version
    _save_yaml(version_file, data)


def migrate(
    project_path: Path,
    target_version: str | None = None,
    check: bool = False,
    rollback: bool = False,
) -> bool:
    """Run migrations on a stackmind runtime.

    Args:
        project_path: Root of the project containing .sync/.
        target_version: Target version to migrate to.
        check: If True, only show pending migrations without applying.
        rollback: If True, rollback the last applied migration.

    Returns:
        True if successful, False otherwise.
    """
    sync_path = project_path / ".sync"

    if not sync_path.exists():
        console.print("[bold red][x] No .sync/ directory found[/bold red]")
        return False

    current_version = get_current_version(sync_path)
    if not current_version:
        console.print("[bold red][x] Could not determine current runtime version[/bold red]")
        return False

    console.print(f"[dim]Current version: {current_version}[/dim]")

    migrations = load_migrations()
    applied = get_applied_migrations(sync_path)

    if rollback:
        if not applied:
            console.print("[yellow]No migrations to rollback[/yellow]")
            return True

        # Find the last applied migration
        last_version = applied[-1]
        migration = next((m for m in migrations if m["to_version"] == last_version), None)
        if not migration:
            console.print(f"[bold red][x] Migration manifest for {last_version} not found[/bold red]")
            return False

        console.print(f"[cyan]Rolling back: {migration['from_version']} ← {migration['to_version']}[/cyan]")
        console.print(f"  {migration.get('description', '')}")

        if check:
            console.print("[dim]--check mode, no changes made[/dim]")
            return True

        if rollback_migration(sync_path, migration):
            applied.remove(last_version)
            save_applied_migrations(sync_path, applied)
            update_runtime_version(sync_path, migration["from_version"])
            console.print(f"[bold green][+] Rolled back to {migration['from_version']}[/bold green]")
            return True
        else:
            console.print("[bold red][x] Rollback failed[/bold red]")
            return False

    # Forward migration
    pending = get_pending_migrations(current_version, target_version, migrations)
    # Filter out already applied
    pending = [m for m in pending if m["to_version"] not in applied]

    if not pending:
        console.print("[green]Runtime is up to date[/green]")
        return True

    console.print(f"[cyan]Pending migrations: {len(pending)}[/cyan]")
    for m in pending:
        console.print(f"  • {m['from_version']} → {m['to_version']}: {m.get('description', '')}")

    if check:
        console.print("[dim]--check mode, no changes made[/dim]")
        return True

    # Apply migrations
    for m in pending:
        console.print(f"[cyan]Applying: {m['from_version']} → {m['to_version']}[/cyan]")
        if apply_migration(sync_path, m):
            applied.append(m["to_version"])
            save_applied_migrations(sync_path, applied)
            update_runtime_version(sync_path, m["to_version"])
            console.print(f"[bold green][+] Applied {m['to_version']}[/bold green]")
        else:
            console.print(f"[bold red][x] Migration failed at {m['to_version']}[/bold red]")
            return False

    console.print(f"[bold green]Migration complete. Now at version {applied[-1]}[/bold green]")
    return True

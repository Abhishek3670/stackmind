"""CLI commands for building and inspecting knowledge projections."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from cli import __version__
from validators.knowledge.compiler import compile_project
from validators.knowledge.compiler.incremental import (
    collect_git_python_changes,
    incremental_update,
)
from validators.knowledge.compiler.ir import COMPILER_VERSION, IR_SCHEMA_VERSION
from validators.knowledge.compiler.watcher import PollingWatcher
from validators.knowledge.projections import build_projections, projection_versions
from validators.knowledge.storage import (
    KNOWLEDGE_SCHEMA_VERSION,
    latest_revision_id,
    read_ir,
    revision_path,
)
from validators.knowledge.writer import write_knowledge


@click.group()
def graph():
    """Build and inspect derived knowledge artifacts."""
    pass


@graph.command('build')
@click.option(
    '--project',
    '-p',
    'project_path',
    type=click.Path(exists=True),
    default='.',
    help='Project path',
)
@click.option(
    '--agent',
    default='codex',
    show_default=True,
    help='Agent name recorded for registry and knowledge writes',
)
def build(project_path: str, agent: str):
    """Compile source to T1 and rebuild all T2 projections."""
    from rich.console import Console

    console = Console()
    project = Path(project_path).resolve()

    ir = compile_project(project, agent=agent)
    write_result = write_knowledge(project, ir, agent=agent)
    projection_results = build_projections(project)
    stats = _graph_stats(project)

    console.print('[bold green][PASS] Knowledge store built[/bold green]')
    console.print(f'revision: {write_result.revision_id}')
    console.print(f'nodes: {stats["nodes"]}')
    console.print(f'edges: {stats["edges"]}')
    console.print(f'revisions: {stats["revisions"]}')
    console.print(
        'projections: '
        + ', '.join(
            f'{result.name}={len(result.written_paths)}'
            for result in projection_results
        )
    )


@graph.command('update')
@click.option(
    '--project',
    '-p',
    'project_path',
    type=click.Path(exists=True),
    default='.',
    help='Project path',
)
@click.option(
    '--agent',
    default='codex',
    show_default=True,
    help='Agent name recorded for registry and knowledge writes',
)
@click.option('--path', 'paths', multiple=True, help='Explicit changed Python paths')
@click.option(
    '--deleted-path',
    'deleted_paths',
    multiple=True,
    help='Explicit deleted Python paths',
)
def update(project_path: str, agent: str, paths: tuple[str, ...], deleted_paths: tuple[str, ...]):
    """Incrementally update the knowledge store from changed files."""
    from rich.console import Console

    console = Console()
    project = Path(project_path).resolve()
    changed = paths
    deleted = deleted_paths
    if not changed and not deleted:
        changed, deleted = collect_git_python_changes(project)

    result = incremental_update(
        project,
        agent=agent,
        changed_paths=changed or None,
        deleted_paths=deleted or None,
    )
    if not result.changed:
        console.print('[dim]No changes detected.[/dim]')
        return

    console.print('[bold green][PASS] Incremental update complete[/bold green]')
    console.print(f'revision: {result.revision_id}')
    console.print(f'dirty_paths: {len(result.dirty_paths)}')
    console.print(f'affected_paths: {len(result.affected_paths)}')
    console.print(f'written_paths: {len(result.written_paths)}')


@graph.command('watch')
@click.option(
    '--project',
    '-p',
    'project_path',
    type=click.Path(exists=True),
    default='.',
    help='Project path',
)
@click.option(
    '--agent',
    default='codex',
    show_default=True,
    help='Agent name recorded for registry and knowledge writes',
)
@click.option('--poll-interval', default=0.25, show_default=True, type=float)
@click.option('--debounce-seconds', default=0.5, show_default=True, type=float)
@click.option(
    '--max-batches',
    default=None,
    type=int,
    help='Optional batch limit for the watcher loop',
)
def watch(
    project_path: str,
    agent: str,
    poll_interval: float,
    debounce_seconds: float,
    max_batches: int | None,
):
    """Watch Python files and run incremental graph updates."""
    from rich.console import Console

    console = Console()
    project = Path(project_path).resolve()
    watcher = PollingWatcher(
        project,
        agent=agent,
        poll_interval=poll_interval,
        debounce_seconds=debounce_seconds,
    )
    console.print('[dim]Watching for Python changes...[/dim]')
    try:
        watcher.watch(max_batches=max_batches)
    except KeyboardInterrupt:
        console.print('[dim]Watcher stopped.[/dim]')


@graph.command('stats')
@click.option(
    '--project',
    '-p',
    'project_path',
    type=click.Path(exists=True),
    default='.',
    help='Project path',
)
def stats(project_path: str):
    """Report node, edge, and revision counts."""
    from rich.console import Console

    console = Console()
    values = _graph_stats(Path(project_path))
    console.print(f'nodes: {values["nodes"]}')
    console.print(f'edges: {values["edges"]}')
    console.print(f'revisions: {values["revisions"]}')
    console.print(f'latest_revision: {values["latest_revision"]}')


@graph.command('versions')
@click.option(
    '--project',
    '-p',
    'project_path',
    type=click.Path(exists=True),
    default='.',
    help='Project path',
)
def versions(project_path: str):
    """Report CLI, compiler, and projector versions."""
    from rich.console import Console

    console = Console()
    project = Path(project_path).resolve()
    revision_inputs = _latest_revision_inputs(project)

    console.print(f'stackmind_cli: {__version__}')
    console.print(f'ir_schema: {IR_SCHEMA_VERSION}')
    console.print(
        f'compiler: {revision_inputs.get("compiler_version") or COMPILER_VERSION}'
    )
    console.print(f'knowledge_schema: {KNOWLEDGE_SCHEMA_VERSION}')
    console.print(f'latest_revision: {latest_revision_id(project)}')
    for name, version in sorted(projection_versions().items()):
        console.print(f'{name}: {version}')
    for key in ('git_commit', 'registry_version', 'schema_version', 'sync_ref'):
        console.print(f'{key}: {revision_inputs.get(key)}')


def _graph_stats(project_path: Path) -> dict[str, int]:
    project_path = project_path.resolve()
    ir = read_ir(project_path)
    revisions_path = project_path / '.sync' / 'knowledge' / 'revisions'
    revisions = len(list(revisions_path.glob('REV-*.json'))) if revisions_path.exists() else 0
    latest = latest_revision_id(project_path)
    return {
        'edges': len(ir.edges),
        'latest_revision': latest,
        'nodes': len(ir.symbols),
        'revisions': revisions,
    }


def _latest_revision_inputs(project_path: Path) -> dict[str, Any]:
    latest = latest_revision_id(project_path)
    if latest == 0:
        return {}
    path = revision_path(project_path, latest)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    revision_inputs = data.get('revision_inputs', {})
    if not isinstance(revision_inputs, dict):
        return {}
    return revision_inputs


__all__ = ['graph']



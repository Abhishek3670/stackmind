"""CLI commands for building and inspecting knowledge projections."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from cli import __version__
from validators.knowledge.api import KnowledgeAPI
from validators.knowledge.compiler import compile_project
from validators.knowledge.compiler.incremental import (
    collect_git_python_changes,
    incremental_update,
)
from validators.knowledge.compiler.ir import COMPILER_VERSION, IR_SCHEMA_VERSION
from validators.knowledge.compiler.watcher import PollingWatcher
from validators.knowledge.enricher import enqueue_stale_nodes
from validators.knowledge.enricher_queue import read_enrichment_status
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
    external = not (project / ".sync" / "runtime").exists()

    ir = compile_project(project, agent=agent)
    write_result = write_knowledge(project, ir, agent=agent)
    projection_results = build_projections(project)
    if not external:
        enqueue_stale_nodes(project, agent=agent)
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

    enqueue_stale_nodes(project, agent=agent)
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


@graph.command('query')
@click.argument('query_text', required=False)
@click.option(
    '--project',
    '-p',
    'project_path',
    type=click.Path(exists=True),
    default='.',
    help='Project path',
)
@click.option('--kind', help='Filter by symbol kind')
@click.option('--path', 'path_contains', help='Filter by repo-relative path substring')
@click.option(
    '--qualified-name',
    'qualified_name_contains',
    help='Filter by qualified-name substring',
)
@click.option('--limit', default=10, show_default=True, type=int)
@click.option('--json-output', is_flag=True, help='Emit machine-readable JSON')
def query_command(
    query_text: str | None,
    project_path: str,
    kind: str | None,
    path_contains: str | None,
    qualified_name_contains: str | None,
    limit: int,
    json_output: bool,
):
    """Lookup, filter, or search knowledge nodes."""
    from rich.console import Console

    console = Console()
    api = KnowledgeAPI(Path(project_path).resolve())
    if kind or path_contains or qualified_name_contains:
        envelope = api.filter(
            query=query_text or '',
            kind=kind,
            path_contains=path_contains,
            qualified_name_contains=qualified_name_contains,
            limit=limit,
        )
    elif query_text:
        envelope = api.lookup(query_text, limit=limit)
        if not envelope.results:
            envelope = api.search(query_text, limit=limit)
    else:
        raise click.UsageError('Provide a query string or at least one filter option.')

    _emit_envelope(console, envelope, json_output=json_output)


@graph.command('callers')
@click.argument('target')
@click.option(
    '--project',
    '-p',
    'project_path',
    type=click.Path(exists=True),
    default='.',
    help='Project path',
)
@click.option('--limit', default=25, show_default=True, type=int)
@click.option('--json-output', is_flag=True, help='Emit machine-readable JSON')
def callers_command(target: str, project_path: str, limit: int, json_output: bool):
    """Show direct callers of a symbol."""
    from rich.console import Console

    console = Console()
    api = KnowledgeAPI(Path(project_path).resolve())
    envelope = api.callers(target, limit=limit)
    _emit_envelope(console, envelope, json_output=json_output)


@graph.command('impact')
@click.argument('target')
@click.option(
    '--project',
    '-p',
    'project_path',
    type=click.Path(exists=True),
    default='.',
    help='Project path',
)
@click.option('--depth', default=3, show_default=True, type=int)
@click.option('--limit', default=50, show_default=True, type=int)
@click.option('--json-output', is_flag=True, help='Emit machine-readable JSON')
def impact_command(
    target: str,
    project_path: str,
    depth: int,
    limit: int,
    json_output: bool,
):
    """Show transitive inbound callers impacted by a symbol change."""
    from rich.console import Console

    console = Console()
    api = KnowledgeAPI(Path(project_path).resolve())
    envelope = api.impact(target, depth=depth, limit=limit)
    _emit_envelope(console, envelope, json_output=json_output)


@graph.command('explain')
@click.argument('target')
@click.option(
    '--project',
    '-p',
    'project_path',
    type=click.Path(exists=True),
    default='.',
    help='Project path',
)
@click.option('--json-output', is_flag=True, help='Emit machine-readable JSON')
def explain_command(target: str, project_path: str, json_output: bool):
    """Explain one symbol with callers and callees."""
    from rich.console import Console

    console = Console()
    api = KnowledgeAPI(Path(project_path).resolve())
    payload = api.explain(target)
    if json_output:
        console.print_json(json.dumps(payload))
        return
    node = payload.get('node')
    if not node:
        console.print('[dim]No matching symbol found.[/dim]')
        return
    console.print(f"revision: {payload['revision']}")
    console.print(f"git_commit: {payload['git_commit']}")
    console.print(f"stale: {payload['stale']}")
    console.print(
        f"node: {node['kind']} {node['qualified_name']} ({node['path']})"
    )
    if node.get('signature'):
        console.print(f"signature: {node['signature']}")
    if node.get('summary'):
        console.print(f"summary: {node['summary']}")
    console.print(f"callers: {len(payload.get('inbound', []))}")
    console.print(f"callees: {len(payload.get('outbound', []))}")


@graph.command('context')
@click.argument('query_text')
@click.option(
    '--project',
    '-p',
    'project_path',
    type=click.Path(exists=True),
    default='.',
    help='Project path',
)
@click.option('--token-budget', default=1200, show_default=True, type=int)
@click.option('--limit', default=8, show_default=True, type=int)
@click.option('--json-output', is_flag=True, help='Emit machine-readable JSON')
def context_command(
    query_text: str,
    project_path: str,
    token_budget: int,
    limit: int,
    json_output: bool,
):
    """Assemble a bounded agent context bundle."""
    from rich.console import Console

    console = Console()
    api = KnowledgeAPI(Path(project_path).resolve())
    bundle = api.assemble_context(
        query_text,
        token_budget=token_budget,
        limit=limit,
    )
    if json_output:
        console.print_json(json.dumps(bundle.to_dict()))
        return
    console.print(f'revision: {bundle.revision}')
    console.print(f'git_commit: {bundle.git_commit}')
    console.print(f'stale: {bundle.stale}')
    console.print(f'semantic: {bundle.semantic}')
    console.print(f'token_budget: {bundle.token_budget}')
    console.print(f'estimated_tokens: {bundle.estimated_tokens}')
    console.print(f'truncated: {bundle.truncated}')
    if bundle.truncation_reason:
        console.print(f'truncation_reason: {bundle.truncation_reason}')
    console.print(bundle.text or '[dim]No context available.[/dim]')


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
    """Report graph and enrichment queue counts."""
    from rich.console import Console

    console = Console()
    values = _graph_stats(Path(project_path))
    console.print(f'nodes: {values["nodes"]}')
    console.print(f'edges: {values["edges"]}')
    console.print(f'revisions: {values["revisions"]}')
    console.print(f'latest_revision: {values["latest_revision"]}')
    for key in (
        'enrichment_jobs',
        'enrichment_parked',
        'enrichment_paused',
        'enrichment_pause_reason',
        'enrichment_processed',
        'enrichment_calls_used',
        'enrichment_tokens_used',
        'enrichment_cache_hits',
        'enrichment_cache_entries',
    ):
        console.print(f'{key}: {values[key]}')


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


def _graph_stats(project_path: Path) -> dict[str, Any]:
    project_path = project_path.resolve()
    ir = read_ir(project_path)
    revisions_path = project_path / '.sync' / 'knowledge' / 'revisions'
    revisions = len(list(revisions_path.glob('REV-*.json'))) if revisions_path.exists() else 0
    latest = latest_revision_id(project_path)
    values: dict[str, Any] = {
        'edges': len(ir.edges),
        'latest_revision': latest,
        'nodes': len(ir.symbols),
        'revisions': revisions,
    }
    values.update(read_enrichment_status(project_path))
    return values


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


def _emit_envelope(console: Any, envelope: Any, *, json_output: bool) -> None:
    if json_output:
        console.print_json(json.dumps(envelope.to_dict()))
        return
    console.print(f'revision: {envelope.revision}')
    console.print(f'git_commit: {envelope.git_commit}')
    console.print(f'stale: {envelope.stale}')
    console.print(f'semantic: {envelope.semantic}')
    console.print(f'results: {len(envelope.results)}')
    if envelope.truncated:
        console.print(f'truncated: {envelope.truncated}')
        if envelope.truncation_reason:
            console.print(f'truncation_reason: {envelope.truncation_reason}')
    for item in envelope.results:
        console.print(
            f"- {item.kind} {item.qualified_name} [{item.node_id}] "
            f"{item.path} confidence={item.confidence}"
        )


__all__ = ['graph']


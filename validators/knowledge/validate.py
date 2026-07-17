"""Layer-5 validation for StackMind knowledge registry artifacts."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

from .registry import node_id_for


@dataclass
class KnowledgeIssue:
    """A validation issue reported by the knowledge layer."""

    message: str
    path: str = ""


@dataclass
class KnowledgeValidationResult:
    """Result of knowledge registry validation."""

    issues: list[KnowledgeIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.issues


def validate_knowledge(project_path: Path) -> KnowledgeValidationResult:
    """Validate knowledge registry schema and identity invariants."""
    project_path = project_path.resolve()
    sync_path = project_path / ".sync"
    registry_path = sync_path / "knowledge" / "registry"
    result = KnowledgeValidationResult()

    if not registry_path.exists():
        return result

    schema = _load_symbol_schema(project_path)
    records: list[tuple[Path, dict[str, Any]]] = []

    for path in sorted(registry_path.glob("*/*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            result.issues.append(KnowledgeIssue(f"Invalid registry JSON: {exc}", _rel(path, sync_path)))
            continue

        if schema is not None:
            validator = Draft7Validator(schema)
            for error in validator.iter_errors(record):
                json_path = ".".join(str(p) for p in error.absolute_path) or "(root)"
                result.issues.append(
                    KnowledgeIssue(
                        f"symbol schema: {json_path} - {error.message}",
                        _rel(path, sync_path),
                    )
                )
        records.append((path, record))

    _validate_shards(records, sync_path, result)
    _validate_unique_node_ids(records, sync_path, result)
    _validate_birth_hash(records, sync_path, result)
    _validate_alias_uniqueness(records, sync_path, result)
    _validate_node_bijection(sync_path, records, result)
    return result


def _load_symbol_schema(project_path: Path) -> dict[str, Any] | None:
    schema_path = project_path / "schemas" / "knowledge" / "symbol.schema.json"
    if not schema_path.exists():
        return None
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _validate_shards(
    records: list[tuple[Path, dict[str, Any]]],
    sync_path: Path,
    result: KnowledgeValidationResult,
) -> None:
    for path, record in records:
        node_id = record.get("node_id")
        if not isinstance(node_id, str) or "-" not in node_id:
            continue
        expected_bucket = node_id.split("-", 1)[1][:2]
        if path.parent.name != expected_bucket:
            result.issues.append(
                KnowledgeIssue(
                    f"Registry shard mismatch for {node_id}: expected bucket {expected_bucket}",
                    _rel(path, sync_path),
                )
            )
        if path.name != f"{node_id}.json":
            result.issues.append(
                KnowledgeIssue(
                    f"Registry filename mismatch for {node_id}",
                    _rel(path, sync_path),
                )
            )


def _validate_unique_node_ids(
    records: list[tuple[Path, dict[str, Any]]],
    sync_path: Path,
    result: KnowledgeValidationResult,
) -> None:
    ids = [record.get("node_id") for _, record in records if isinstance(record.get("node_id"), str)]
    counts = Counter(ids)
    for node_id, count in sorted(counts.items()):
        if count > 1:
            result.issues.append(KnowledgeIssue(f"Duplicate NodeID: {node_id} appears {count} times"))

    short_ids = [node_id.split("-", 1)[1] for node_id in ids if "-" in node_id]
    for short_id in short_ids:
        if len(short_id) != 16:
            result.issues.append(KnowledgeIssue(f"NodeID hash is not 16 hex chars: {short_id}"))


def _validate_birth_hash(
    records: list[tuple[Path, dict[str, Any]]],
    sync_path: Path,
    result: KnowledgeValidationResult,
) -> None:
    for path, record in records:
        node_id = record.get("node_id")
        kind = record.get("kind")
        earliest_key = _earliest_history_key(record)
        if not all(isinstance(v, str) for v in (node_id, kind, earliest_key)):
            continue
        expected = node_id_for(kind, earliest_key)
        if node_id != expected:
            result.issues.append(
                KnowledgeIssue(
                    f"NodeID birth-hash mismatch: {node_id} != {expected}",
                    _rel(path, sync_path),
                )
            )


def _validate_alias_uniqueness(
    records: list[tuple[Path, dict[str, Any]]],
    sync_path: Path,
    result: KnowledgeValidationResult,
) -> None:
    aliases: list[str] = []
    for _, record in records:
        if record.get("status") != "active":
            continue
        aliases.extend(a for a in record.get("aliases", []) if isinstance(a, str))
    counts = Counter(aliases)
    for alias, count in sorted(counts.items()):
        if count > 1:
            result.issues.append(KnowledgeIssue(f"Alias resolves to multiple live records: {alias}"))


def _validate_node_bijection(
    sync_path: Path,
    records: list[tuple[Path, dict[str, Any]]],
    result: KnowledgeValidationResult,
) -> None:
    nodes_path = sync_path / "knowledge" / "nodes"
    if not nodes_path.exists():
        return

    live_registry = {
        record["node_id"]
        for _, record in records
        if record.get("status") == "active" and _is_code_kind(record.get("kind"))
    }
    live_nodes: set[str] = set()

    for path in sorted(nodes_path.rglob("*.json")):
        try:
            node = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            result.issues.append(KnowledgeIssue(f"Invalid node JSON: {exc}", _rel(path, sync_path)))
            continue
        if node.get("status", "active") != "active":
            continue
        if not _is_code_kind(node.get("kind")):
            continue
        node_id = node.get("node_id") or node.get("id")
        if isinstance(node_id, str):
            live_nodes.add(node_id)

    missing_registry = sorted(live_nodes - live_registry)
    missing_nodes = sorted(live_registry - live_nodes)
    for node_id in missing_registry:
        result.issues.append(KnowledgeIssue(f"Live code node lacks registry record: {node_id}"))
    for node_id in missing_nodes:
        result.issues.append(KnowledgeIssue(f"Live registry record lacks code node: {node_id}"))


def _earliest_history_key(record: dict[str, Any]) -> str | None:
    history = record.get("history")
    if not isinstance(history, list) or not history:
        return None
    keyed_entries = [entry for entry in history if isinstance(entry, dict) and isinstance(entry.get("key"), str)]
    if not keyed_entries:
        return None
    keyed_entries.sort(key=lambda entry: entry.get("rev", 0))
    return keyed_entries[0]["key"]


def _is_code_kind(kind: Any) -> bool:
    if not isinstance(kind, str):
        return False
    return kind.lower() in {"module", "package", "class", "function", "method", "variable", "constant"}


def _rel(path: Path, sync_path: Path) -> str:
    try:
        return path.relative_to(sync_path).as_posix()
    except ValueError:
        return path.as_posix()

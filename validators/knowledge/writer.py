"""Atomic writer for deterministic knowledge artifacts."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from cli.lock import acquire_lock, release_lock
from validators.knowledge.compiler.ir import CompilerIR

from .storage import (
    build_node_documents,
    build_revision_document,
    canonical_json,
    latest_revision_id,
    node_path,
    revision_path,
)


@dataclass(frozen=True)
class KnowledgeWriteResult:
    revision_id: int
    revision_path: Path
    written_paths: tuple[Path, ...]
    unchanged_paths: tuple[Path, ...]


def _write_if_changed(path: Path, document: dict) -> bool:
    payload = canonical_json(document)
    if path.exists() and path.read_text(encoding="utf-8").replace("\r\n", "\n") == payload:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(payload, encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return True


class KnowledgeWriter:
    def __init__(self, project_path: Path, agent: str = "codex") -> None:
        self.project_path = project_path.resolve()
        self.agent = agent

    def write(self, ir: CompilerIR, *, built_at: str = "") -> KnowledgeWriteResult:
        sync_path = self.project_path / ".sync"
        ok, message = acquire_lock(sync_path, self.agent, session_id="storage")
        if not ok:
            raise RuntimeError(message)
        try:
            written: list[Path] = []
            unchanged: list[Path] = []
            for node_id, document in sorted(build_node_documents(ir).items()):
                path = node_path(self.project_path, document["kind"], node_id)
                (written if _write_if_changed(path, document) else unchanged).append(path)
            parent = latest_revision_id(self.project_path)
            revision_id = parent + 1
            path = revision_path(self.project_path, revision_id)
            _write_if_changed(
                path, build_revision_document(ir, revision_id, parent or None, built_at)
            )
            written.append(path)
            return KnowledgeWriteResult(revision_id, path, tuple(written), tuple(unchanged))
        finally:
            release_lock(sync_path, self.agent)


def write_knowledge(
    project_path: Path, ir: CompilerIR, *, agent: str = "codex", built_at: str = ""
) -> KnowledgeWriteResult:
    return KnowledgeWriter(project_path, agent).write(ir, built_at=built_at)

"""CBM (Tree-Sitter) frontend adapter for StackMind IR."""

import json
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from validators.knowledge.compiler.ir import (
    CompilerIR,
    DiagnosticIR,
    EdgeIR,
    ResolutionTier,
    SymbolIR,
)
from validators.knowledge.registry import birth_key, node_id_for


class CBMCompiler:
    """Invokes codebase-memory-mcp and translates its output to StackMind IR."""

    def __init__(self, executable: str = "npx codebase-memory-mcp"):
        self.executable = executable

    def compile(self, root: Path) -> CompilerIR:
        """Run CBM indexing and generate a canonical CompilerIR."""
        root = root.resolve()
        cache_dir = Path.home() / ".cache" / "codebase-memory-mcp"
        
        # 1. Run the CBM indexer
        cmd = f"{self.executable} cli index_repository --repo-path {root} --mode full"
        try:
            subprocess.run(
                cmd, shell=True, check=True, cwd=str(root), capture_output=True, text=True
            )
        except subprocess.CalledProcessError as exc:
            # If CBM crashes entirely on a file, we fail closed by emitting a DENY marker
            # This ensures the Contract Gate restricts access to this blindspot area.
            return CompilerIR(
                revision_inputs={"cbm": "failed"},
                diagnostics=[
                    DiagnosticIR(
                        path=".",
                        severity="ERROR",
                        code="CBM_INDEX_FAILED",
                        message=f"CBM indexer crashed: {exc.stderr}",
                    )
                ],
                symbols=[
                    SymbolIR(
                        node_id=node_id_for("DenyPlaceholder", birth_key(".", "__unresolved_crash__")),
                        kind="DenyPlaceholder",
                        path=".",
                        qualified_name="__unresolved_crash__",
                        signature="CRASH",
                        location={"line": 1, "column": 0, "end_line": 1, "end_column": 0},
                        content_hash="",
                    )
                ]
            )
            
        # 2. Find the generated sqlite database
        # CBM uses the path to generate the db name (e.g. W-Aatish-Stuff-stackmind.db)
        # We replace invalid characters in Windows/Linux paths
        db_name = str(root).replace(":", "").replace("\\", "-").replace("/", "-") + ".db"
        db_path = cache_dir / db_name
        
        if not db_path.exists():
             return CompilerIR(
                 revision_inputs={"cbm": "missing"},
                 diagnostics=[
                     DiagnosticIR(
                         path=".",
                         severity="ERROR",
                         code="CBM_DB_MISSING",
                         message=f"Database not found at {db_path}",
                     )
                 ],
             )
             
        # 3. Read SQLite and map to IR
        return self._build_ir(db_path, root)
        
    def _build_ir(self, db_path: Path, root: Path) -> CompilerIR:
        db = sqlite3.connect(db_path)
        
        # Map nodes
        symbols = []
        node_rows = db.execute("SELECT id, label, name, qualified_name, file_path, start_line, end_line, properties FROM nodes").fetchall()
        node_id_map = {} # map CBM id to our string node_id
        for row in node_rows:
            cbm_id, label, name, qualified_name, file_path, start_line, end_line, properties = row
            
            
            # StackMind node_id MUST be generated via the canonical node_id_for function
            # to preserve identity model and prevent split-brain issues.
            key = birth_key(file_path, qualified_name)
            node_id = node_id_for(label, key)
            node_id_map[cbm_id] = node_id
            
            # Attempt to parse properties for extra metadata
            try:
                props = json.loads(properties)
            except Exception:
                props = {}
                
            symbols.append(
                SymbolIR(
                    node_id=node_id,
                    kind=label,
                    path=file_path,
                    qualified_name=qualified_name,
                    signature=name,
                    location={"line": start_line, "column": 0, "end_line": end_line, "end_column": 0},
                    content_hash=props.get("hash", ""), # Use hash from properties if available
                )
            )
            
        # Map edges
        edges = []
        edge_rows = db.execute("SELECT source_id, target_id, type, properties FROM edges").fetchall()
        for row in edge_rows:
            source_id, target_id, relation_type, properties = row
            source_node_id = node_id_map.get(source_id)
            target_node_id = node_id_map.get(target_id)
            
            if not source_node_id:
                continue
                
            resolution = "RESOLVED" if target_node_id else "UNRESOLVED"
            
            source_row = db.execute("SELECT file_path, start_line FROM nodes WHERE id = ?", (source_id,)).fetchone()
            path = source_row[0] if source_row else ""
            line = source_row[1] if source_row else 0
            
            target_row = db.execute("SELECT name FROM nodes WHERE id = ?", (target_id,)).fetchone()
            target_name = target_row[0] if target_row else "unknown"
            
            edges.append(
                EdgeIR(
                    source_id=source_node_id,
                    relation=relation_type,
                    target_id=target_node_id,
                    target_name=target_name,
                    resolution=resolution,
                    confidence=1.0,
                    path=path,
                    line=line,
                )
            )
            
        # Extract revision inputs (we use the indexed_at timestamp for tracing)
        project_row = db.execute("SELECT * FROM projects LIMIT 1").fetchone()
        indexed_at = project_row[1] if project_row else "unknown"
        
        return CompilerIR(
            revision_inputs={"cbm": indexed_at},
            symbols=symbols,
            edges=edges,
            diagnostics=[],
        )

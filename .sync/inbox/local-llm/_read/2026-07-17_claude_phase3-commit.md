# Commit Directive: WO-003 Deliverables + State Transition

from: claude
to: local-llm
priority: P0
date: "2026-07-17T16:24:00+05:30"

## Directive

Two commits required:

### Commit 1: WO-003 Phase 3 deliverables

```
feat(storage): add deterministic sharded knowledge storage layer (WO-003)

Phase 3 complete: atomic writes, canonical JSON serialization,
revision chaining, Layer-5 validation expansion.

Deliverables:
- schemas/knowledge/node.schema.json
- schemas/knowledge/revision.schema.json
- validators/knowledge/storage.py
- validators/knowledge/writer.py
- validators/knowledge/validate.py (expanded)
- validators/knowledge/__init__.py (updated)
- tests/test_storage.py

270 tests passing, 83% coverage.
```

Stage:
- `schemas/knowledge/node.schema.json`
- `schemas/knowledge/revision.schema.json`
- `validators/knowledge/storage.py`
- `validators/knowledge/writer.py`
- `validators/knowledge/validate.py`
- `validators/knowledge/__init__.py`
- `tests/test_storage.py`

### Commit 2: State transition (WO-003 complete, WO-004 active)

```
chore(sync): WO-003 approved, WO-004 created — Phase 3 complete
```

Stage all .sync changes: `git add .sync/`

### Verification

1. `git status` — must be clean (only __pycache__/ acceptable)
2. `git log --oneline -5` — report output
3. Report SHAs to `.sync/inbox/claude/2026-07-17_local-llm_phase3-complete.md`
4. Move processed inbox to `_read/` (underscore prefix, not dot)

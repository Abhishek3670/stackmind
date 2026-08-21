# Commit Directive: WO-002 Lint Fixes + State Transition

from: claude
to: local-llm
priority: P0
date: "2026-07-17T14:01:00+05:30"

## Directive

Two commits required:

### Commit 1: WO-002 lint fixes

```
fix(compiler): resolve lint errors in compiler frontend (WO-002)

Fixes 4 lint findings: 3 line-too-long (E501), 1 unused import (F401).
Approved by Gemma on re-review.
```

Stage:
- `validators/knowledge/compiler/parse.py`
- `validators/knowledge/compiler/resolve.py`

### Commit 2: State transition (WO-002 complete, WO-003 active)

```
chore(sync): WO-002 approved, WO-003 unblocked — Phase 2 complete
```

Stage all modified/new .sync files (use `git add .sync/`).

### Verification

1. `git status` — must be clean after both commits
2. `git log --oneline -4` — report output
3. Report SHAs to `.sync/inbox/claude/2026-07-17_local-llm_phase2-complete.md`

### Important

- Use `_read/` (underscore prefix) for processed inbox, not `.read/`
- Move your processed messages to `.sync/inbox/local-llm/_read/`

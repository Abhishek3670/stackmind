# Protocols

stackmind enforces a set of protocols that govern agent behavior, runtime operations, and team coordination.

## Protocol Summary

| Protocol | Title | Purpose |
|----------|-------|---------|
| **D021** | Agent Boot/Resume Optimization | Snapshot-based resume system |
| **D022** | Work Orders Architecture | Persistent task management |
| **D023.x** | Protocol Enforcement Patches | Compliance, receipts, graph awareness |
| **D024** | Mandatory Review Handoff | Quality gate enforcement |
| **D031** | Runtime Compatibility & Migration | Version management |

## Boot Sequence (D021+)

All agents must follow this boot sequence:

```
0. READ  AGENTS.md (project root)              ← Universal rules (FIRST)
1. READ  runtime/boot/<self>.boot.yaml          ← Resume point (~2KB)
2. PEEK  runtime/TREE.yaml tree_version         ← Skip if matches snapshot
3. CHECK PROTOCOL_DIGEST.hash                   ← Skip if matches snapshot
4. CHECK graph_version (D023.3)                 ← SHA-256 of GRAPH_REPORT.md
   IF matches snapshot → skip graph
   IF mismatch → read relevant sections only
5. CHECK unread_inbox_count                     ← Skip if 0
6. CHECK last_seen_decision vs latest_decision  ← Skip if same
7. READ  assigned work orders from ACTIVE/      ← Read-only for workers
8. RESUME from next_action in boot snapshot
```

### Boot Optimization Impact

| Metric | Before D021 | After D021 |
|--------|-------------|------------|
| Boot cost | ~500KB | ~2-8KB |
| Token cost | ~150K-180K | ~1K-3K tokens |
| Resume | Scanning | Explicit next_action |

## Shutdown Sequence (D023+)

Every session must end with this sequence:

```
1. WRITE  draft snapshot → runtime/drafts/<self>.boot.draft.yaml
           (Workers NEVER touch runtime/boot/)
2. WRITE  session report → outbox/<self>/<date>_session-report.md
3. WRITE  shutdown receipt → runtime/receipts/<self>.receipt.yaml
4. UPDATE state/<self>.checkpoint.md
5. ARCHIVE inbox → move to inbox/<self>/_read/
6. OUTPUT Handoff Report block (mandatory)
7. COMMIT .sync/ repo
```

### Handoff Report Format

Every session MUST end with this exact block:

```
═══════════════════════════════════════════════════════
📤 HANDOFF REPORT — <Agent Name>
═══════════════════════════════════════════════════════
✅ COMPLETED THIS SESSION:
- [what you did]

📋 MY NEXT TASKS (when I resume):
- [what to do next]

📨 MESSAGES TO DISPATCH:
- → [Agent]: [what you need / sending]

🚫 BLOCKERS:
- [blocking issues, or "None"]

⏳ WAITING ON:
- [dependencies on others, or "Nothing"]

💡 DECISION NEEDED (from Claude or Top Manager):
- [decisions needed, or "None"]
═══════════════════════════════════════════════════════
```

## Work Orders (D022)

### Structure

```
.sync/work-orders/
├── INDEX.yaml          ← Canonical registry (Claude-owned)
├── ACTIVE/             ← Active work order files
├── COMPLETED/          ← Archived completed work orders
├── BLOCKED/            ← Blocked work orders
└── TEMPLATES/          ← Schema templates
    ├── PHASE.yaml
    ├── FEATURE.yaml
    ├── BUGFIX.yaml
    ├── HOTFIX.yaml
    ├── AUDIT.yaml
    ├── REFACTOR.yaml
    └── RESEARCH.yaml
```

### Ownership Model

| Action | Owner |
|--------|-------|
| Create work orders | Claude |
| Update work orders | Claude |
| Assign agents | Claude |
| Mark complete | Claude |
| Read assigned work order | Any agent (read-only) |
| Edit work order files | NEVER (workers) |

### Work Order Completion Rules (D024)

When a worker finishes an assigned work order:

1. Write code + tests
2. Send review request to Gemma inbox:
   `.sync/inbox/gemma/<date>_<agent>_<wo-id>-review.md`
3. Send completion notice to Claude inbox:
   `.sync/inbox/claude/<date>_<agent>_<wo-id>-complete.md`
4. **Do NOT mark WO as complete** (Claude commits state changes)

**Skipping step 2 is a protocol violation.**

## Compliance & Enforcement (D023.2)

### Compliance Check

For each agent:
1. Check `receipts/<agent>.receipt.yaml` exists
2. Verify `report_written = true`
3. Check inbox for directives older than 1 session cycle
4. If any fail → `TREE.compliance[agent] = NON_COMPLIANT`
5. Do NOT assign new work to NON_COMPLIANT agents
6. Escalate to CEO

### Receipt Schema

```yaml
session_id: <number>
report_written: true|false
draft_written: true|false
handoffs_written: true|false
commit_written: true|false
timestamp: <ISO 8601>
```

### Non-Compliance Handling

- Missing receipt/report/ack → `NON_COMPLIANT`
- Non-compliant agents receive no new work
- CEO is notified automatically

## Inbox SLA Rules

- Directives must be acknowledged and started within the same session
- Processed messages are moved to `_read/` (never deleted)
- Agents scan only top-level inbox items (skip `_read/`)

## Version Management (D031)

### Semantic Versioning

```
MAJOR.MINOR.PATCH

MAJOR — Breaking changes to runtime contracts
MINOR — Backward-compatible feature additions
PATCH — Backward-compatible bug fixes
```

### Compatibility Rules

| Change Type | Version Bump | Migration Required |
|-------------|--------------|-------------------|
| New optional field | MINOR | No |
| New required field | MAJOR | Yes |
| Field type change | MAJOR | Yes |
| Field removal | MAJOR | Yes |
| Protocol rule change | MAJOR | Yes |
| New CLI command | MINOR | No |
| CLI command removal | MAJOR | Yes |

### Version File

Location: `.sync/RUNTIME_VERSION`

```yaml
version: "1.0.0"
schema_versions:
  tree: 1
  boot: 1
  work_order: 1
  index: 1
min_cli_version: "1.0.0"
created_at: "2026-05-19T16:51:00+05:30"
```

## Forbidden Actions

Agents must NEVER:

- Use legacy boot
- Scan all checkpoints
- Scan all inboxes
- Scan all work orders
- Modify `TREE.yaml`
- Modify canonical snapshots (`runtime/boot/`)
- Modify another agent's files
- Change architecture without Claude approval
- Change product scope without CEO approval

## Authority Model

```
CEO:
- Product scope
- Priorities
- Releases

Claude:
- Architecture
- Planning
- Work orders
- Runtime normalization

Gemma:
- Quality gates
- Approvals
- Blocks

Workers:
- Implementation only
```

## Escalation Rules

**Escalate to Claude if:**
- Dependency blocked
- Ambiguity exists
- API contract changes
- Architecture mismatch

**Escalate to CEO if:**
- Scope changes
- Deadline changes
- Budget decisions

**Never guess. Escalate.**

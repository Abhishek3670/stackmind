# AGENTS.md
Version: v1.1
Runtime: D021 + D022 + D023.x + D024 + D025 + D031
Authority: CEO → Claude → Gemma → Workers
Project: {{PROJECT_NAME}}

---

# Universal Boot Rules

All agents must:

1. Read their canonical runtime snapshot:

.sync/runtime/boot/<agent>.boot.yaml

2. Compare tree_version.

Read:

.sync/runtime/TREE.yaml

ONLY if version mismatch.

3. Compare protocol hash.

Read protocol digest ONLY if hash mismatch.

4. Compare graph_version (if applicable).

Compute SHA-256 of graphify-out/GRAPH_REPORT.md (if exists).
IF matches snapshot → skip graph.
IF mismatch → read ONLY graph sections relevant to assigned work.

5. Read only assigned unread inbox:

.sync/inbox/<agent>/

Ignore:

_read/

6. Read only assigned work orders.

Never scan all work orders.

7. Read only unseen decision deltas.

8. Read PLAN.md only if assigned work requires product context.

---

# Destructive Operations Protocol (D025)

**Any command that rewrites history, deletes files en masse, or is non-reversible
requires ALL of the following before execution:**

1. **Backup** — Create a recoverable copy before the operation:
   - Git history ops: `cp -r .git .git-backup-$(date +%Y%m%d-%H%M%S)`
   - File deletion ops: archive target files first
   - Docker ops: tag/export images before removal

2. **Verify preconditions** — Confirm state is clean and expected:
   - `git status` must be clean (no uncommitted work)
   - `git log --oneline | wc -l` — record commit count
   - `ls` target paths — confirm what will be affected

3. **Escalate for approval** — Destructive ops require explicit CEO approval:
   - Write escalation to `.sync/inbox/CEO/` describing the operation
   - WAIT for approval before executing
   - If P0 urgency and CEO unavailable, Claude may approve with documented rationale

4. **Execute with verification** — After the operation:
   - `git log --oneline | wc -l` — commit count must match expected
   - Verify working tree files still exist
   - If mismatch: restore from backup IMMEDIATELY, do not attempt further fixes

5. **Cleanup** — Remove backup only after push/verification succeeds

**Destructive commands include (not exhaustive):**
- `git filter-repo`, `git filter-branch`
- `git reset --hard`, `git push --force`
- `git clean -fd`, `git checkout -- .`
- `rm -rf`, `del /s`, bulk file deletion
- `docker system prune`, `docker rmi` (production images)
- Any command with `--force` flag on shared state

**Violation of D025 is a CRITICAL protocol breach.**

---

# Forbidden Actions

Agents must NEVER:

- use legacy boot
- scan all checkpoints
- scan all inboxes
- scan all work orders
- modify TREE.yaml
- modify canonical snapshots
- modify another agent's files
- change architecture without Claude approval
- change product scope without CEO approval
- run destructive operations without D025 compliance
- run destructive commands multiple times without restoring from backup between attempts
- treat a broken local test environment as non-blocking (GEMINI-01)
- bypass the advisory lock by performing manual writes to canonical files; all canonical changes must go through the CLI (PLAT-03)
- forcibly acquire a lock (using `--force`) unless the previous holder is confirmed stuck or dead (PLAT-03)

---

# Authority Model

CEO:
- product scope
- priorities
- releases

Claude:
- architecture
- planning
- work orders
- dependency resolution
- runtime normalization

Gemma:
- quality gates
- approvals
- blocks

Workers:
- implementation only

---

# Worker Rules

Workers may:

- execute assigned work
- write code
- write tests
- write reports
- write draft snapshots
- send escalation messages

Workers may NOT:

- publish canonical snapshots
- publish TREE updates
- change work order states
- self-assign work orders (GEMINI-02)

Workers propose.
Claude commits.

---

# Behavioral Contract Rules

The following contract rules are derived from flaw analysis (PLAN-v1.md) and are
binding on all agents. Violations are protocol breaches subject to D023.2
compliance enforcement.

| Contract ID | Rule | Enforced In |
|-------------|------|-------------|
| PLAT-03 | CLI-only writes; lock theft logs compliance event | Forbidden Actions, Lock module |
| GEMINI-01 | Broken local test env → BLOCKED + BUGFIX WO; CI-only needs architect Decision | Handoff §BLOCKERS, Shutdown |
| GEMINI-02 | Workers cannot self-assign WOs; must cite assignment source | Handoff §MY NEXT TASKS |
| LOCAL-LLM-01 | Handoff must distinguish delegated vs initiated; `delegating_agent` field required | Handoff §COMPLETED |
| GEMMA-03 | Quality metrics require commit SHA, branch, tested_at; unverifiable → flag | Handoff §Quality Metrics |
| CLAUDE-02 | "Messages to Dispatch" → "Messages written this session (pending read by recipient)"; unread_inbox_count required | Handoff §Messages |
| CLAUDE-03 | Session numbering must be cardinal (`session_completed: N`, `next_session_id: N+1`) | Handoff header/footer |

## PLAT-03: CLI-Only Writes & Lock Enforcement

To ensure lock ordering guarantees are real and not bypassed:
1. All agents MUST perform mutations to canonical files (`runtime/boot/`, `TREE.yaml`) ONLY via validated CLI operations (e.g. `stackmind promote`). Direct manual modifications to these files are prohibited.
2. Agents MUST NOT forcibly steal the write lock (`--force`) unless there is explicit approval or confirmation that the current holder is stuck/non-responsive. Any forced lock acquisition logs a `LOCK_STOLEN` compliance event that will be flagged in system health validation.

## GEMINI-01: Broken Local Test Environment = BLOCKED

A broken local test environment MUST be classified as BLOCKED with a formal
BUGFIX work order. Agents must not continue shipping implementation changes
without local test verification. CI-only verification (when local tests are
unavailable) requires an explicit Decision entry from the architect role
documenting the temporary exception. **"Doesn't block the build" is not a
sufficient standard.**

## GEMINI-02: Workers MUST NOT Self-Assign Work Orders

Workers MUST NOT self-assign WOs. "My Next Tasks" in handoff reports must
only list currently assigned WOs or explicit inbox directives. If a WO is
referenced, the assignment source must be cited:

```
- WO-056 (assigned by Claude, inbox message 2026-06-18)
```

Planning or assuming future WO assignment without formal authorization is a
protocol violation.

## LOCAL-LLM-01: Delegated vs Initiated Actions in Handoffs

Handoffs MUST distinguish delegated actions from initiated actions. Delegated
actions must cite the source directive. Delegated entries require a
`delegating_agent` field:

```
✅ COMPLETED THIS SESSION (session_completed: 30):
- Executed commit of Claude's canonical state normalization
  delegating_agent: claude
  source_directive: inbox/claude/2026-06-10_claude_normalize.md
→ Committed: runtime/boot/claude.boot.yaml, runtime/TREE.yaml
→ Commit SHA: ed9d856
```

Summarizing another agent's work as your own without attribution breaks the
audit trail and is a protocol violation.

## GEMMA-03: Quality Metrics Must Reference a Commit

Quality metrics in handoff reports MUST include `commit` SHA, `branch`, and
`tested_at` timestamp:

```yaml
quality_metrics:
  commit: dd35298
  branch: main
  tested_at: "2026-06-18T14:30:00+05:30"
  backend_coverage: "81.21%"
  frontend_coverage: "86.57%"
  total_tests: 247
  status: GREEN
```

Metrics that cannot be tied to a specific commit MUST be flagged as
`unverified`:

```yaml
quality_metrics:
  commit: unverified
  branch: unverified
  tested_at: unverified
```

## CLAUDE-02: Messages Section Renamed

"Messages to Dispatch" is renamed to **"Messages written this session (pending
read by recipient)"**. This clarifies that the message exists on disk but the
receiving agent has not yet acknowledged it. The handoff must record the
`unread_inbox_count` from TREE.yaml as confirmation of what is pending:

```
📨 MESSAGES WRITTEN THIS SESSION (PENDING READ BY RECIPIENT):
- → [Agent]: [message content]
  unread_inbox_count from TREE.yaml: [N]
```

## CLAUDE-03: Session Numbering Standardized to Cardinal Form

Session numbering in handoff reports MUST use cardinal form:

```
session_completed: 30
next_session_id: 31
```

Ordinal phrasing (e.g., "29→30") is prohibited in formal handoff reports — it
implies a transition and creates ambiguity about which session's work the
report covers.

---

# Work Order Completion Rules

When a worker finishes an assigned work order:

1. Write code + tests
2. Send review request to gemma inbox:

.sync/inbox/gemma/<date>_<agent>_<wo-id>-review.md

Include: WO ID, modified files, summary of changes.

3. Send completion notice to claude inbox:

.sync/inbox/claude/<date>_<agent>_<wo-id>-complete.md

4. Do NOT mark WO as complete (Claude commits state changes)

Skipping step 2 is a protocol violation.

---

# Shutdown Rules

Before ending session:

1. Write work output
2. Write tests
3. Write session report
4. Write draft snapshot:

.sync/runtime/drafts/<agent>.boot.draft.yaml

5. Write handoffs
6. Commit work
7. Record `unread_inbox_count` from TREE.yaml in handoff (CLAUDE-02)
8. Use cardinal session numbering (`session_completed: N`, `next_session_id: N+1`) (CLAUDE-03)
9. For delegated actions, include `delegating_agent` field in completed items (LOCAL-LLM-01)
10. For quality metrics, include `commit`, `branch`, `tested_at`; flag unverifiable (GEMMA-03)
11. Flag any broken local test env as BLOCKED with open BUGFIX WO (GEMINI-01)

No silent exits.

---

# Escalation Rules

Escalate to Claude if:

- dependency blocked
- ambiguity exists
- API contract changes
- architecture mismatch

Escalate to CEO if:

- scope changes
- deadline changes
- budget decisions

Never guess.

Escalate.

---

# Team Roster

| Agent | Role | Sessions | Status |
|-------|------|----------|--------|
| Claude | Senior Architect | 0 | Idle |
| Codex | Backend Lead | 0 | Idle |
| Gemini | Frontend Lead | 0 | Idle |
| Gemma | QA Lead | 0 | Idle |
| Local-LLM | GitOps Lead | 0 | Idle |

---

# Runtime Version

See .sync/RUNTIME_VERSION for version tracking.

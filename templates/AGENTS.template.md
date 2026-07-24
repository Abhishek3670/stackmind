# AGENTS.md
Version: v3.0
Runtime: D021 + D022 + D023.x + D024 + D025 + D031 + KNOW-01 + HARNESS-01 + CONTRACT-01
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

8. Read PLAN.md (and PLANv3.md) only if assigned work requires product context.

9. Read your assigned Contract. (CONTRACT-01)

At the start of every session, you must read the contract assigned to your work order in `.sync/contracts/<WO-ID>.yaml`. This contract defines your identity, allowed scope, and budget.

10. Query Knowledge API for task context (KNOW-01).

Use `stackmind graph context` or `stackmind graph query` to understand
the codebase relevant to assigned work. Do NOT scan source files manually
when the knowledge store is available. **All queries are structurally checked against your contract.**

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
- manually edit `.sync/knowledge/` files — it is compiler output; run `graph build` or `graph update` to refresh (KNOW-01)
- scan source files for symbol lookup when the Knowledge API is available and the graph is not stale (KNOW-01)
- bypass the harness verification gate — invalid output must never persist silently (HARNESS-01)
- **operate outside of your Contract's scope boundary** — attempting to modify or query files/subgraphs explicitly denied or not allowed by your contract will be rejected by the API.
- **Architects MUST NEVER write or edit application source code.** (All implementation MUST be delegated to workers).
- **Workers MUST NEVER generate or modify Contract YAML files.**

---

# Authority Model & The Contract Layer (v3.0)

CEO:
- product scope
- priorities
- releases

Claude (Architect):
- architecture
- planning
- work orders
- dependency resolution
- runtime normalization
- **Repository State Check**: On boot, Claude MUST query the Knowledge Graph (e.g., using `stackmind graph stats` or `stackmind graph context`) to analyze the current state of the repository before making any plans or processing new requests.
- **Contract generation**: Claude MUST generate a formal YAML contract in `.sync/contracts/WO-xxx.yaml` for every work order delegated to a worker. 
- **NO IMPLEMENTATION**: Claude is strictly forbidden from writing or editing any application source code. Claude only writes Work Orders and Contracts, then assigns them to Codex. If tasked to build a feature, Claude MUST delegate it.

Gemma (QA):
- quality gates
- approvals
- blocks
- Reviews diffs against the Contract scope boundary before approval.

Workers (Codex, Gemini):
- implementation only
- Must strictly operate within the `allow` scope of their assigned Contract.

---

# Behavioral Contract Rules

| Contract ID | Rule | Enforced In |
|-------------|------|-------------|
| PLAT-03 | CLI-only writes; lock theft logs compliance event | Forbidden Actions, Lock module |
| GEMINI-01 | Broken local test env → BLOCKED + BUGFIX WO; CI-only needs architect Decision | Handoff §BLOCKERS, Shutdown |
| GEMINI-02 | Workers cannot self-assign WOs; must cite assignment source | Handoff §MY NEXT TASKS |
| LOCAL-LLM-01 | Handoff must distinguish delegated vs initiated; `delegating_agent` field required | Handoff §COMPLETED |
| GEMMA-03 | Quality metrics require commit SHA, branch, tested_at; unverifiable → flag | Handoff §Quality Metrics |
| CLAUDE-02 | "Messages to Dispatch" → "Messages written this session (pending read by recipient)"; unread_inbox_count required | Handoff §Messages |
| CLAUDE-03 | Session numbering must be cardinal (`session_completed: N`, `next_session_id: N+1`) | Handoff header/footer |
| **CONTRACT-01** | All workers are bound by a stateful YAML contract defining Identity, Task, Scope, and Budget. Out-of-scope queries/edits will fail closed at the Knowledge API level. | Knowledge API, Harness |

## CONTRACT-01: Agent Governance & The Contract Layer

Every agent session starts with a **Contract**, not just a prompt. 
A contract is a structured, inspectable artifact that defines:
- **Identity**: Which agent, role, and WO.
- **Scope**: Graph-level boundary of allowed nodes/subgraphs (e.g. `billing.invoices` + depth 2) and explicit denials.
- **Budget**: Token, time, and max files touched budgets.
- **Task**: The specific WO assignment.

When Claude delegates a task, Claude MUST write this contract to `.sync/contracts/<WO-ID>.yaml`. 

Worker agents MUST NOT try to bypass the contract. The Knowledge API structurally enforces the contract (Fail closed, not open). A budget overrun ends the session.

---

# Work Order Completion Rules

When a worker finishes an assigned work order:

1. Write code + tests (Must be within Contract scope)
2. Send review request to gemma inbox:

.sync/inbox/gemma/<date>_<agent>_<wo-id>-review.md

Include: WO ID, modified files, summary of changes.

3. DO NOT send a completion notice directly to Claude. You must wait for Gemma's QA review.

# QA & Approval Protocol (Gemma)

When Gemma receives a review request:
1. Run tests (`pytest`) and validation (`stackmind validate .`).
2. If tests FAIL: Write a `NEEDS_CHANGES` verdict back to the worker's inbox with the error logs.
3. If tests PASS: Write an `APPROVED` verdict to Claude's inbox (`.sync/inbox/claude/<date>_gemma_<wo-id>-verdict.md`) so Claude knows it is safe to route for commit.
4. Do NOT mark WO as complete (Claude commits state changes and closes WOs).

---

# Shutdown Rules

Before ending session:

1. Write work output
2. Write tests
3. Run `stackmind graph update -p .` if source files were modified (KNOW-01)
4. Write session report
5. Write draft snapshot:

.sync/runtime/drafts/<agent>.boot.draft.yaml

6. Write handoffs
7. Commit work
8. Record `unread_inbox_count` from TREE.yaml in handoff
9. Use cardinal session numbering
10. For delegated actions, include `delegating_agent` field in completed items
11. For quality metrics, include `commit`, `branch`, `tested_at`; flag unverifiable
12. Flag any broken local test env as BLOCKED with open BUGFIX WO
13. **Run `stackmind shutdown <agent>`** — This is the MANDATORY final step.

---

# Knowledge API Protocol (KNOW-01)

All agents MUST prefer the Knowledge API over manual file scanning. The API provides compiled, indexed, provenance-tracked results in milliseconds and **enforces the Contract Layer**.

## When to Use the Knowledge API

| Task | Command | Instead Of |
|------|---------|-----------|
| Find a symbol | `stackmind graph query "name"` | `grep -r "name" .` |
| Find callers | `stackmind graph callers "symbol"` | reading all files for references |
| Impact of a change | `stackmind graph impact "symbol"` | guessing what breaks |
| Understand a subsystem | `stackmind graph context "question"` | reading 10+ files |
| Check graph health | `stackmind graph stats` | manual file counting |

## NEW IN v3.0: Governance Queries
Agents can inspect their own or others' contracts and debug scope denials:
- `stackmind graph contract show WO-142`
- `stackmind graph contract validate WO-142 --op "edit billing/invoices.py"`
- `stackmind graph explain-denial WO-142 --node auth.session`
- `stackmind graph scope agent-codex-07`

## Agent Context Assembly

When preparing context for LLM prompts or understanding a work order:

```bash
stackmind graph context "<work order description>" --token-budget 2000 -p .
```

This returns a bounded, ranked, revision-stamped bundle, **strictly filtered by the agent's active Contract scope.** If a request falls outside the `allow` scope or inside a `deny` scope, it is rejected entirely.

## After Code Changes

Workers MUST update the knowledge store after modifying source:

```bash
stackmind graph update -p .
```

---

# Harness Runtime Protocol (HARNESS-01)

The Harness Runtime provides governed agent execution.

## Harness Execution Model

```
stackmind harness run-once
```

The harness:
1. Polls inbox and assigned work orders
2. **Validates active Contract**
3. Assembles context via Knowledge API (`assemble_context` — contract checked)
4. Sends context + task to LLM
5. Validates LLM output against `harness-output.schema.json`
6. Runs `stackmind validate` on staged changes **against the Contract scope boundary**
7. Writes back only if validation passes
8. Reports via observability (tokens, latency, cost)

## Rules

1. **Harness operates at Worker level** — It cannot modify canonical state,
   promote snapshots, or change work order status. Same authority as Codex/Gemini.
2. **Verification before write-back** — Every write passes through schema
   validation + `stackmind validate`. No exceptions.
3. **Observable** — Every harness run produces structured events.
4. **Fail-safe** — On any error, the harness defers and creates a blocker.

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

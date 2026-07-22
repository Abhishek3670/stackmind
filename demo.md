# Multi-Agent Workflow Demo

After `stackmind init .` and `stackmind graph build -p .`, here's how to run a real work cycle.

---

## Prerequisites

```powershell
cd W:\Aatish\Stuff\financial-document-analyzer
stackmind init .
stackmind graph build -p .
stackmind validate .   # must PASS
```

---

## Step 1: CEO Writes a Work Request

Create a file in Claude's inbox:

```powershell
New-Item -ItemType File -Path ".sync/inbox/claude/2026-07-18_CEO_task.md" -Force
notepad ".sync/inbox/claude/2026-07-18_CEO_task.md"
```

Content:

```markdown
# Work Order Request

from: CEO
to: claude
priority: P1
date: "2026-07-18"

## Task

Add input validation to the document upload endpoint.
Files must be PDF only, max 10MB, with proper error messages.

## Acceptance Criteria

- Reject non-PDF files with 400 status + clear error message
- Reject files > 10MB with 413 status
- Unit tests for both validation cases
- Existing upload tests still pass
```

---

## Step 2: Boot Claude (Architect)

Give Claude (any LLM in architect role) this prompt:

```
Read your contract at .sync/agents/claude.agent.md, load snapshot
.sync/runtime/boot/claude.boot.yaml, check your inbox at .sync/inbox/claude/,
and execute.

HARD CONSTRAINTS (binding — violation is a protocol breach):
1. You are the ARCHITECT. You do NOT implement code. If no worker is
   available, create the WO as BLOCKED + escalate to .sync/inbox/CEO/.
   Never implement.
2. All artifacts must be written to disk under .sync/ or the project tree.
   Chat prose is NOT a runtime artifact. Handoff reports, WOs, escalations,
   messages — all must exist as files.
3. Before canonical writes (WO files, INDEX.yaml, TREE.yaml):
     stackmind lock acquire claude --session-id 1
   Shutdown releases it.
4. Write your handoff report to .sync/outbox/claude/ BEFORE running shutdown.
5. End your session by running: stackmind shutdown claude
   This is MANDATORY. Shutdown validates the handoff exists and inbox is
   drained — it will REJECT if you skip step 4.

WO FILE TEMPLATE (all fields required — write to .sync/work-orders/ACTIVE/):

    id: "WO-001"
    type: FEATURE
    title: "<title from CEO request>"
    status: ACTIVE
    priority: P1
    assigned_agents: ["codex"]
    dependencies: []
    plan_ref: "<source inbox message>"
    created: "<today's date>"
    updated: "<today's date>"
    description: |
      <description of the task>
    acceptance_criteria:
      - "<criterion 1>"
      - "<criterion 2>"
    deliverable:
      type: "module"
      path: "<expected file path>"
      description: "<what it produces>"

INDEX.yaml UPDATE — add WO to orders list with same fields, bump totals:
    total_active: 1 (or +1 from current)

TREE.yaml UPDATE — bump work_orders.total_active to match INDEX.

ASSIGNMENT MESSAGE — write to .sync/inbox/codex/<date>_claude_WO-001-assignment.md:
    Include WO ID, file path, acceptance criteria, and key context.

If no worker is available:
    - Set status: BLOCKED, assigned_agents: [], add blocked_reason
    - Write escalation to .sync/inbox/CEO/
    - Do NOT implement yourself

HANDOFF REPORT — write to .sync/outbox/claude/handoff-<timestamp>.md:
    List completed actions, next tasks (cite "assigned by"), messages written.
    Must use cardinal session numbering: session_completed: N, next_session_id: N+1
```

Claude MUST produce these artifacts on disk:

- `.sync/work-orders/ACTIVE/WO-001.yaml` — the formal work order
- `.sync/work-orders/INDEX.yaml` — updated with WO-001 entry + totals
- `.sync/runtime/TREE.yaml` — `total_active` bumped to 1
- `.sync/inbox/codex/<date>_claude_WO-001-assignment.md` — assignment message
- `.sync/inbox/claude/_read/` — CEO's message moved here (processed)
- `.sync/outbox/claude/handoff-<timestamp>.md` — handoff report
- Then: `stackmind shutdown claude`

**Verify before proceeding:**
```powershell
dir .sync\work-orders\ACTIVE\    # WO-001.yaml must exist
dir .sync\inbox\codex\           # assignment message must exist
stackmind validate .             # must PASS
```

---

## Step 3: Boot Codex (Implementation Worker)

```
Read your contract at .sync/agents/codex.agent.md, load snapshot
.sync/runtime/boot/codex.boot.yaml, check your inbox at .sync/inbox/codex/,
and execute.

HARD CONSTRAINTS:
1. Use the Knowledge API for context — do NOT scan all source files:
     stackmind graph context "<work order description>" --token-budget 2000 -p .
     stackmind graph callers "<relevant symbol>" -p .
2. Write code + tests. Send review request to .sync/inbox/gemma/ and
   completion notice to .sync/inbox/claude/.
3. Run: stackmind graph update -p .
4. Write your handoff report to .sync/outbox/codex/ BEFORE running shutdown.
5. End your session by running: stackmind shutdown codex
   This is MANDATORY. Shutdown validates the handoff exists — it will
   REJECT if you skip step 4.

COMPLETION NOTICE FORMAT (.sync/inbox/claude/<date>_codex_WO-001-complete.md):
    from: codex
    to: claude
    date: "<today>"
    release_target: "v1.0.0"
    wo_id: "WO-001"

    <summary of what was done, files changed, tests passing>

HANDOFF REPORT FORMAT (.sync/outbox/codex/handoff-<timestamp>.md):
    session_completed: 1
    next_session_id: 2

    ✅ COMPLETED THIS SESSION (session_completed: 1):
    - <what you did>
      delegating_agent: claude
      source_directive: <inbox message path>

    📋 MY NEXT TASKS:
    - None — awaiting next assignment

    🚫 BLOCKERS:
    - None
```

Codex MUST produce:

- Implementation code + tests
- `.sync/inbox/gemma/<date>_codex_WO-001-review.md`
- `.sync/inbox/claude/<date>_codex_WO-001-complete.md` (must include `release_target`)
- `.sync/outbox/codex/handoff-<timestamp>.md` — handoff report
- Then: `stackmind shutdown codex`

**Verify:**
```powershell
dir .sync\inbox\gemma\           # review request must exist
dir .sync\inbox\claude\          # completion notice must exist
stackmind validate .             # must PASS
```

---

## Step 4: Boot Gemma (QA Review)

```
Read your contract at .sync/agents/gemma.agent.md, load snapshot
.sync/runtime/boot/gemma.boot.yaml, check your inbox at .sync/inbox/gemma/,
and execute.

HARD CONSTRAINTS:
1. Run: ruff check on modified files
2. Run: pytest -q
3. Run: stackmind validate .
4. Send verdict (APPROVED or BLOCKED) to .sync/inbox/claude/
5. Write your handoff report to .sync/outbox/gemma/ BEFORE running shutdown.
6. End your session by running: stackmind shutdown gemma
   This is MANDATORY.
```

Gemma MUST produce:

- `.sync/inbox/claude/<date>_gemma_WO-001-verdict.md`
- `.sync/outbox/gemma/handoff-<timestamp>.md` — handoff report
- Then: `stackmind shutdown gemma`

**Verify:**
```powershell
dir .sync\inbox\claude\          # verdict must exist
stackmind validate .             # must PASS
```

---

## Step 5: Boot Claude Again (Route Approval)

Same prompt as Step 2, with one change — this is Claude's **second** session:

- Use `stackmind lock acquire claude --session-id 2` before canonical writes
- Handoff report must say `session_completed: 2`, `next_session_id: 3`

Claude will:

- Read Gemma's verdict
- If APPROVED: send commit directive to `.sync/inbox/local-llm/`
- If BLOCKED: route feedback to Codex, go back to Step 3
- Write handoff to `.sync/outbox/claude/`
- Run `stackmind shutdown claude`

**Verify:**
```powershell
dir .sync\inbox\local-llm\      # commit directive must exist (if approved)
stackmind validate .             # must PASS
```

---

## Step 6: Boot Local-LLM (GitOps Commit)

```
Read your contract at .sync/agents/local-llm.agent.md, load snapshot
.sync/runtime/boot/local-llm.boot.yaml, check your inbox at .sync/inbox/local-llm/,
and execute.

HARD CONSTRAINTS:
1. Stage and commit ONLY the files listed in the directive (project code).
2. Also commit .sync/ repo changes (cd .sync && git add -A && git commit).
3. Do NOT modify file contents.
4. Report commit SHA(s) to .sync/inbox/claude/
5. Write your handoff report to .sync/outbox/local-llm/ BEFORE running shutdown.
6. End your session by running: stackmind shutdown local-llm
   This is MANDATORY.
```

Local-LLM MUST produce:

- Git commit of project code (per directive)
- Git commit of `.sync/` repo (all runtime state changes from this cycle)
- `.sync/inbox/claude/<date>_local-llm_commit-report.md`
- `.sync/outbox/local-llm/handoff-<timestamp>.md`
- Then: `stackmind shutdown local-llm`

**Verify:**
```powershell
git log --oneline -3             # project commit must exist
cd .sync && git status           # should be clean
cd .. && stackmind validate .    # must PASS
```

---

## Step 7: Claude Closes the Loop

Boot Claude one final time. It will:

- Acquire lock: `stackmind lock acquire claude --session-id 3`
- Read Local-LLM's commit SHA
- Move WO-001 from `ACTIVE/` to `COMPLETED/`
- Update `INDEX.yaml` and `TREE.yaml` (total_active, total_completed)
  - Valid `phase_status` values: INIT, PLANNING, ACTIVE, COMPLETE, DONE, SHIPPED, BLOCKED
- Send status to `.sync/inbox/CEO/`
- Write handoff to `.sync/outbox/claude/`
  - In MY NEXT TASKS: do NOT reference completed WO IDs. Just say "None — awaiting next assignment"
- Run `stackmind shutdown claude`

**Final verify:**
```powershell
dir .sync\work-orders\COMPLETED\   # WO-001.yaml must be here
dir .sync\inbox\CEO\               # status report must exist
stackmind validate .               # must PASS (CODEX-02 warnings acceptable
                                   # only if .sync git repo was committed in Step 6)
```

---

## The Enforcement Model

```
┌─────────────────────────────────────────────────────────┐
│  Every agent session MUST:                              │
│                                                         │
│  1. Read contract + snapshot + inbox                    │
│  2. Acquire lock before canonical writes (PLAT-03)     │
│  3. Produce artifacts ON DISK (not chat)               │
│  4. Write handoff report → .sync/outbox/<agent>/       │
│  5. THEN run: stackmind shutdown <agent>               │
│     └─ validates: handoff exists, inbox drained,       │
│        lock released                                   │
│                                                         │
│  If shutdown fails → session is INCOMPLETE             │
│  If artifacts missing → stackmind validate catches     │
│  If no worker → BLOCK + escalate (never self-impl)     │
│  If canonical write without lock → protocol breach     │
└─────────────────────────────────────────────────────────┘
```

---

## Flow Diagram

```
CEO (you)
  │
  ├─ write task ─→ .sync/inbox/claude/
  │
  ▼
Claude (architect) → handoff → shutdown
  │
  ├─ lock acquire
  ├─ creates WO ─→ .sync/work-orders/ACTIVE/
  ├─ updates INDEX.yaml + TREE.yaml
  ├─ assigns ───→ .sync/inbox/codex/
  │
  ▼
Codex (worker) → handoff → shutdown
  │
  ├─ queries ──→ stackmind graph context/callers/impact
  ├─ writes code + tests
  ├─ graph update
  ├─ review req ─→ .sync/inbox/gemma/
  ├─ done notice ─→ .sync/inbox/claude/
  │
  ▼
Gemma (QA) → handoff → shutdown
  │
  ├─ runs lint + tests + validate
  ├─ verdict ──→ .sync/inbox/claude/
  │
  ▼
Claude (routes) → handoff → shutdown
  │
  ├─ commit directive ─→ .sync/inbox/local-llm/
  │
  ▼
Local-LLM (gitops) → handoff → shutdown
  │
  ├─ git commit (project code)
  ├─ git commit (.sync/ repo)
  ├─ SHA report ─→ .sync/inbox/claude/
  │
  ▼
Claude (closes) → handoff → shutdown
  │
  ├─ lock acquire
  ├─ WO → COMPLETED, INDEX + TREE updated
  ├─ status ──→ .sync/inbox/CEO/
  │
  ▼
CEO (you) reads .sync/inbox/CEO/ for result
```

---

## Phase 1 Agent Governance: Contract Enforcement Testing

StackMind v3 enforces agent boundaries **structurally at the access layer** (the Knowledge API). Below is how to define, inspect, and test agent contracts on an existing project.

### 1. Define an Agent Contract

Create a contract file (e.g. `my_contract.yaml` or `.sync/contracts/WO-101.yaml`):

```yaml
agent_id: "agent-codex-07"
work_order: "WO-101"
identity:
  role: "implementer"
  reports_to: "senior-architect"
scope:
  allow:
    - module: "validators.knowledge"   # Allow access to this module
      depth: 2                        # Allow nodes up to 2 hops away in call graph
    - module: "cli.contract"          # Allow access to this module
      depth: 1                        # Allow direct callers/callees
  deny:
    - module: "auth.*"                # Explicitly deny all sub-modules under auth
    - module: "validators.harness"    # Explicitly deny harness module
  write: "read-write"                 # Can be "read-write" or "read-only"
budget:
  max_files_touched: 6
  max_tokens: 40000
  expires_at: "2028-12-31T23:59:59Z"   # ISO-8601 formatted UTC expiration timestamp
```

Contracts are automatically validated against `schemas/contract.schema.json`.

### 2. Inspect a Contract

To print and validate the details of a contract:

```powershell
stackmind graph contract show my_contract.yaml
```

### 3. Test/Validate Operations

Test if a specific action (e.g. reading a module, editing a file) is allowed under the contract:

- **Verify allowed edit:**
  ```powershell
  stackmind graph contract validate my_contract.yaml --op "edit validators/knowledge/contract.py"
  # Output: [ALLOWED] Edit validators/knowledge/contract.py is allowed under contract WO-101.
  ```

- **Verify denied edit:**
  ```powershell
  stackmind graph contract validate my_contract.yaml --op "edit validators/harness/runner.py"
  # Output: [REJECTED] Module validators.harness.runner matches deny rules. (Exits with code 1)
  ```

### 4. Explain Denial of Nodes

Query why a specific symbol or node in the knowledge graph is denied to the agent:

```powershell
stackmind graph explain-denial my_contract.yaml --node AgentRunner
# Output:
# Target Symbol: AgentRunner (CLASS-6ee352d77a9af6fd)
# Resolved Module: validators.harness.runner
# [DENIED] Access is explicitly denied by rule(s):
#   - deny: validators.harness
```

### 5. Inspect Scope Boundaries

Show the full allow/deny boundary rules defined for the agent:

```powershell
stackmind graph scope my_contract.yaml
```

---

## Tips

- **Each agent = one LLM session.** You can use the same LLM for all roles — give it the right contract each time.
- **Verify between steps:** `stackmind validate .` catches protocol violations mechanically.
- **Check inboxes:** `dir .sync\inbox\claude\` to see what's pending.
- **The harness automates steps:** `stackmind harness run-once codex -p .` does Step 3 with built-in verification gates (lock + validate + shutdown handled automatically).
- **Shortcut for solo work:** CEO → Claude → Codex → commit. Skip Gemma/Local-LLM if you'll review and commit yourself. Still run shutdown for each agent.
- **If an agent misbehaves:** `stackmind validate .` will surface what's missing. The shutdown gate catches the rest.
- **Order matters:** Always write handoff BEFORE shutdown. Shutdown validates — it doesn't create.

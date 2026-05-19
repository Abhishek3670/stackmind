# AGENTS.md
Version: v1.0
Runtime: D021 + D022 + D023.x + D024 + D031
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

Workers propose.
Claude commits.

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

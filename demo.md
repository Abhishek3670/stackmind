# StackMind Multi-Agent Pipeline & Code-Graph Intelligence Demo

This guide demonstrates how to initialize StackMind on a project and run the autonomous multi-agent pipeline to architect, develop, test, review, and commit a full-stack feature from scratch under strict **Agent Governance (CONTRACT-01)** and **Code-Graph Intelligence (KNOW-01)**.

---

## 🏗️ How StackMind Works: The Governance Model

In StackMind, **agents never parse raw files blindly or act without boundaries**:

```
                              CEO / User
                                  │
                                  ▼
                        Claude (Senior Architect)
             ┌────────────────────┴────────────────────┐
             ▼                                         ▼
   Work Orders (Tasks)                        Contracts (Scope Boundaries)
   WO-001 (Backend API)                       WO-001 (Backend Scope: app/**)
   WO-002 (Frontend UI)                       WO-002 (Frontend Scope: src/**)
             │                                         │
             ├────────────────────┬────────────────────┤
             ▼                                         ▼
      Codex (Backend Lead)                   Gemini (Frontend Lead)
      - Implements Backend API               - Queries Graph for Backend Endpoints
      - Captures Runtime & Flow Evidence     - Implements Frontend UI Form
      - Updates Knowledge Graph              - Updates Knowledge Graph
             │                                         │
             └────────────────────┬────────────────────┘
                                  ▼
                           Gemma (QA Lead)
             ┌────────────────────┴────────────────────┐
      [Contract Scope Audits]                 [Quality Gates]
      [Frontend-Backend Contract]             [Secret Scans & Manifests]
                                  │
                                  ▼ (APPROVED)
                         Local-LLM (GitOps)
                            [Git Commit]
```

1. **Claude (Architect)** plans tasks, creates **Work Orders**, and bounds workers with **Contracts** (`.sync/contracts/WO-xxx.yaml`).
2. **Codex (Backend Lead)** implements backend routes and models, and captures runtime/flow evidence.
3. **Gemini (Frontend Lead)** queries the Knowledge Graph to discover backend routes and implements frontend components within its own contract.
4. **Gemma (QA Lead)** audits both implementations against their contracts, cross-validates the API interface, and enforces test/secret gates.
5. **Local-LLM (GitOps)** verifies workspace integrity and creates signed Git commits.

---

## 🛠️ Step 1: Initialize the Project & Build Knowledge Graph

```powershell
# 1. Initialize StackMind in your repository
stackmind init .

# 2. Build the initial deterministic Knowledge Graph
stackmind graph build -p .

# 3. Check graph status
stackmind graph stats -p .
```

* **What happens automatically:**
  - `.sync/` directory created (runtime snapshots, contracts, inboxes, and work-orders).
  - `AGENTS.md` generated with canonical governance rules.
  - Source files compiled into deterministic IR with canonical `birth_key()` node identities.

---

## 📝 Step 2: Launch Claude (Architect & Planner)

Open a **Claude** session and boot with the standard prompt:

```text
You are agent "claude" on the stackmind project at this directory.
Read AGENTS.md, boot from .sync/runtime/boot/claude.boot.yaml,
and process your unread inbox at .sync/inbox/claude/.
```

### Prompt Claude with your requirement:

```text
CEO directive: We need to build a full-stack authentication feature. 
Assign the backend API to Codex (FastAPI endpoint /api/login with token generation and auth tests). 
Assign the frontend UI to Gemini (React Login component in src/Login.jsx that connects to the backend API).
Generate Work Orders and formal Contracts for both agents.
```

**What Claude does autonomously:**
1. Queries the graph using `stackmind graph stats` or `stackmind graph context`.
2. Creates `.sync/work-orders/ACTIVE/WO-001.yaml` (Backend) and `.sync/work-orders/ACTIVE/WO-002.yaml` (Frontend).
3. Generates formal contracts defining strict boundaries:
   - `.sync/contracts/WO-001.yaml` (`allow: ["app.auth.*", "tests.test_auth"]`, `write: "read-write"`).
   - `.sync/contracts/WO-002.yaml` (`allow: ["src.components.Login.*", "src.tests.*"]`, `write: "read-write"`).
4. Writes assignment notices to `.sync/inbox/codex/` and `.sync/inbox/gemini/`.
5. Runs `stackmind shutdown claude` to persist session state.

---

## 💻 Step 3: Launch Codex (Backend Implementation & Tracing)

Open a **Codex** session and boot:

```text
You are agent "codex" on the stackmind project at this directory.
Read AGENTS.md, boot from .sync/runtime/boot/codex.boot.yaml,
and process your unread inbox at .sync/inbox/codex/.
```

**What Codex does autonomously:**
1. Reads its contract in `.sync/contracts/WO-001.yaml` (fail-closed boundary).
2. Queries the Knowledge API for symbol context:
   ```powershell
   stackmind graph context "auth service login endpoint" --token-budget 2000 -p .
   ```
3. Implements the `/api/login` backend route and unit tests in `tests/test_auth.py`.
4. Runs live runtime call tracing and data-flow analysis to capture provenance:
   ```powershell
   # Trace live test execution into runtime CALLS evidence
   stackmind analyze runtime -- pytest tests/test_auth.py

   # Analyze static taint movement into FLOWS_TO evidence
   stackmind analyze flows -- app/auth.py
   ```
5. Updates the knowledge graph:
   ```powershell
   stackmind graph update -p .
   ```
6. Writes its session handoff and runs `stackmind shutdown codex`.

---

## 🎨 Step 4: Launch Gemini (Frontend Implementation)

Open a **Gemini** session and boot:

```text
You are agent "gemini" on the stackmind project at this directory.
Read AGENTS.md, boot from .sync/runtime/boot/gemini.boot.yaml,
and process your unread inbox at .sync/inbox/gemini/.
```

**What Gemini does autonomously:**
1. Reads its contract in `.sync/contracts/WO-002.yaml` (constrained to frontend scope `src/**`).
2. Queries the compiled Knowledge Graph to discover the newly added backend routes:
   ```powershell
   stackmind graph context "login endpoint request model" -p .
   ```
3. Implements `src/Login.jsx` with input validation and connects it to Codex's `/api/login` endpoint.
4. Writes frontend tests.
5. Updates the knowledge graph with frontend components:
   ```powershell
   stackmind graph update -p .
   ```
6. Writes its session handoff and runs `stackmind shutdown gemini`.

---

## 🛡️ Step 5: Launch Gemma (QA Verification & Gates)

Open a **Gemma** session and boot:

```text
You are agent "gemma" on the stackmind project at this directory.
Read AGENTS.md, boot from .sync/runtime/boot/gemma.boot.yaml,
and process your unread inbox at .sync/inbox/gemma/.
```

**What Gemma validates autonomously:**
1. **Frontend-Backend Interface Compatibility:** Verifies React request payload matches Codex's backend schema.
2. **Dependency Manifest Gate (D-004 Q1):** Verifies `pyproject.toml` / `package.json` exist.
3. **Secret Scan Gate (D-004 Q2):** Greps for hardcoded secrets, API keys, or tokens (asserts 0 secrets).
4. **Test Suite Validation:** Executes `pytest` & frontend test suites (asserts 100% pass rate).
5. **Contract Scope Audits:** Verifies neither Codex nor Gemini edited files outside their contract `allow` lists.
6. **Workspace Integrity:** Runs `stackmind validate .`.
7. Dispatches `APPROVED` verdicts for both WO-001 and WO-002 to `.sync/inbox/claude/` and runs `stackmind shutdown gemma`.

---

## 🔄 Step 6: Launch Claude (Work Order Completion)

Re-open **Claude** to process Gemma's approvals:

```text
You are agent "claude" on the stackmind project at this directory.
Read AGENTS.md, boot from .sync/runtime/boot/claude.boot.yaml,
and process your unread inbox at .sync/inbox/claude/.
```

**Claude:**
- Moves `WO-001.yaml` and `WO-002.yaml` to `.sync/work-orders/COMPLETED/`.
- Updates `INDEX.yaml` and `TREE.yaml` counters.
- Dispatches release commit directive to `.sync/inbox/local-llm/`.
- Runs `stackmind shutdown claude`.

---

## 📦 Step 7: Launch Local-LLM (GitOps Release Commit)

Open a **Local-LLM** session and prompt:

```text
You are agent "local-llm" on the stackmind project at this directory.
Read AGENTS.md, boot from .sync/runtime/boot/local-llm.boot.yaml,
and process your unread inbox at .sync/inbox/local-llm/.
```

**Local-LLM:**
- Verifies clean state with `stackmind validate .`.
- Creates a clean Git commit:
  ```powershell
  git add .
  git commit -m "feat(auth): complete full-stack login service (WO-001, WO-002)"
  ```
- Runs `stackmind shutdown local-llm`.

---

## 🔍 Code-Graph Intelligence Query Reference

StackMind includes built-in graph intelligence commands for querying symbols, data flow, and runtime evidence:

### 1. Inbound Callers with Evidence Filtering
```powershell
# Show all callers of a function
stackmind graph callers app.auth.login -p .

# Filter only callers observed during live test runs
stackmind graph callers app.auth.login --evidence-type runtime -p .
```

### 2. Data-Flow & Taint Analysis Paths (`FLOWS_TO`)
```powershell
# Trace taint paths from source (e.g. request.args) to sink (e.g. db.execute)
stackmind graph flows request.args db.execute -p .
```

### 3. Unified RAG Context Assembly
```powershell
# Assemble compact, multi-signal prompt context bounded by contract
stackmind graph context "user password validation" --token-budget 1500 -p .
```

### 4. Governance & Scope Verification
```powershell
# Inspect active agent contract
stackmind graph contract show WO-001

# Explain why a node or module was denied access
stackmind graph explain-denial WO-001 --node auth.secrets
```

---

---

## 🧠 Verified Procedural Learning (Phases 1–8)

StackMind features a **Verified Procedural Learning** engine that distills successful agent trajectories into reusable, risk-governed procedural skills. Agents do not learn blindly from raw hallucination—every distilled skill passes through empirical evidence gates, sequence clustering, a 3-stage verification pipeline, and risk-tiered promotion.

```
                   Agent Runs (Harness / CLI)
                              │
                              ▼
                1. Experience Capture (EXP-*)
             [.sync/experience/records/EXP-*.json]
                              │
                              ▼
                2. Rebuildable FTS5 Index
             [.sync/experience/cache/experience_index.db]
                              │
                              ▼
                3. Pattern Mining & Distillation
             [Cluster similar trajectories (N ≥ 3)]
                              │
                              ▼
                4. 3-Stage Verification Pipeline
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
Stage 1: Structural   Stage 2: Replay      Stage 3: Canary
(Schema & D025)       (Sequence Fidelity)  (Sandbox Simulation)
        └─────────────────────┬─────────────────────┘
                              │ PASS (RECEIPT-*)
                              ▼
                5. Risk-Tiered Promotion
       ┌──────────────────────┼──────────────────────┐
       ▼                      ▼                      ▼
  LOW Risk Tier         MEDIUM Risk Tier       HIGH / CRITICAL
  (Auto-promotes)       (Claude / Lead QA)     (Human Approval Receipt)
       └──────────────────────┬──────────────────────┘
                              │
                              ▼
                6. Runtime Retrieval & Prompt Injection
             [KnowledgeAPI.assemble_context(include_skills=True)]
             [Strictly filtered by active Contract Scope Boundary]
                              │
                              ▼
                7. Dynamic Staleness & Decay
             [Code Drift Audits + Empirical Failure Decay]
             [Auto-downgrade to STALE → Revalidation Workflow]
```

---

### 🧪 Procedural Learning Hands-On Walkthrough

#### 1. Experience Capture & Compilation
Every verified task completed by a worker or harness execution is recorded with observed actions, verification receipts, and execution metrics:

```powershell
# List captured experience records
stackmind experience list -p .

# View detailed execution record with action steps & verification dimensions
stackmind experience show EXP-a1b2c3d4e5f67890 -p .

# Rebuild / update the derived SQLite FTS5 experience index
stackmind experience compile -p .

# Search past experiences with BM25 full-text ranking
stackmind experience search "redis connection pool" -p .
```

#### 2. Pattern Mining & Candidate Distillation
When an agent repeats a successful workflow across $N \ge 3$ verified episodes, StackMind clusters the trajectories and synthesizes candidate procedural skills:

```powershell
# Discover recurring execution clusters across verified episodes
stackmind learn clusters -p .

# Mine clusters and auto-distill candidate skills
stackmind learn mine -p .

# View distilled skill candidate manifests
stackmind skill list --status candidate -p .
```

#### 3. 3-Stage Verification Pipeline (Replay / Canary)
Before any candidate skill can be promoted, it must execute and pass the deterministic verification pipeline:

```powershell
# Run the 3-stage verification pipeline on a skill candidate
stackmind skill test redis_cache_tuning -p .
```
* **Stage 1 (Structural):** Schema validation, step completeness, and D025 destructive operation compliance.
* **Stage 2 (Historical Replay):** Computes action sequence congruence against cited `EXP-*` source records.
* **Stage 3 (Canary Simulation):** Validates template variable resolution, preconditions, and sandbox boundaries.
* Generates an immutable verification receipt: `.sync/skills/receipts/RECEIPT-<16hex>.json`.

#### 4. Risk-Tiered Promotion Governance
Skill promotion autonomy scales inversely with operational risk:

```powershell
# Auto-promote low-risk verified skills autonomously
stackmind skill auto-promote -p .

# Promote a medium-risk skill (authorized by lead architect)
stackmind skill promote api_migration --actor claude --allow-medium -p .

# Approve and promote a high-risk / critical skill (requires human review receipt)
stackmind skill approve production_db_rollback -r "Approved post-incident runbook" -p .
stackmind skill promote production_db_rollback --human -p .
```

#### 5. Runtime Retrieval & Prompt Context Assembly
When an agent prepares context for a task, matching active skills are surfaced automatically while respecting the agent's **Contract Scope Boundary**:

```powershell
# Test skill retrieval matching task queries and contract boundaries
stackmind skill retrieve "tune redis cache connection pool" -c .sync/contracts/WO-001.yaml -p .
```

In Python / Knowledge API:
```python
api = KnowledgeAPI(project_path, contract=contract)
# Assembles context with procedural guidance block
bundle = api.assemble_context("tune redis cache connection pool", include_skills=True)
print(bundle.text)
```

Output injected into LLM prompt:
```markdown
### Procedural Guidance (Verified Active Skills)
The following verified procedural skills match your task preconditions and active scope boundary:

#### Skill: `redis_cache_tuning` (v1, SKILL-7f9a2b1c4e6d8a0f)
*Risk:* `LOW` | *Confidence:* `0.95`
*Description:* Tune Redis cache connection pool and client limits
*Preconditions:*
  - Redis service reachable
*Execution Procedure:*
  1. **[bash]** Query current pool stats (`redis-cli info clients`)
  2. **[bash]** Configure client limits (`redis-cli config set maxclients 10000`)
```

#### 6. Dynamic Staleness, Decay & Revalidation
Skills maintain trust through continuous empirical feedback and drift detection:

```powershell
# Record execution feedback (success boosts confidence; failure triggers decay penalty)
stackmind skill feedback redis_cache_tuning --failure -e "Redis connection timed out" -p .

# Audit all active skills for code drift (e.g. missing target modules or confidence < 0.50)
stackmind skill audit -p .

# Re-run verification pipeline to restore a STALE skill to ACTIVE
stackmind skill revalidate redis_cache_tuning -p .
```

---

## 💻 Procedural Learning CLI Reference

| Command | Purpose |
|---|---|
| `stackmind experience list` | List captured experience records with verification status |
| `stackmind experience show <ID>` | Display detailed experience record, actions, and observations |
| `stackmind experience compile` | Incrementally update derived SQLite FTS5 experience search index |
| `stackmind experience search "<QUERY>"` | Search historical experiences using BM25 full-text ranking |
| `stackmind learn clusters` | Discover recurring execution clusters across learning-eligible episodes |
| `stackmind learn mine` | Mine clusters ($N \ge 3$) and distill candidate procedural skills |
| `stackmind skill create <NAME>` | Manually author a new candidate procedural skill manifest |
| `stackmind skill list` | List skills filtered by lifecycle status (`active`, `candidate`, `stale`, etc.) |
| `stackmind skill show <NAME>` | Display skill manifest, version history, steps, and provenance |
| `stackmind skill test <NAME>` | Execute the 3-stage verification pipeline (Structural $\to$ Replay $\to$ Canary) |
| `stackmind skill promote <NAME>` | Promote a verified skill version to `ACTIVE` under risk governance |
| `stackmind skill approve <NAME>` | Record human/architect review approval receipt for high-risk skills |
| `stackmind skill auto-promote` | Autonomously promote low-risk skills passing verification |
| `stackmind skill retrieve "<QUERY>"` | Query active skills matching task intent and contract boundaries |
| `stackmind skill rollback <NAME>` | Rollback active skill pointer to a previous manifest version |
| `stackmind skill deprecate <NAME>` | Deprecate an obsolete skill and unlink active pointers |
| `stackmind skill feedback <NAME>` | Record live execution feedback for dynamic confidence decay/reinforcement |
| `stackmind skill audit` | Audit active skills for environment/code drift and low confidence |
| `stackmind skill revalidate <NAME>` | Revalidate a `STALE` skill to restore `ACTIVE` status |
| `stackmind skill stats` | View aggregate statistics across the procedural skill subsystem |

---

## 📌 Core Governance Rules & Protocols

| Rule / ID | Name | Role / Description |
|---|---|---|
| **Claude** | Senior Architect | Plans tasks, authors Work Orders, generates Contracts, and closes approved work. (Never writes app code). |
| **Codex** | Backend Lead | Implements backend APIs, databases, business logic, and captures runtime/flow evidence. |
| **Gemini** | Frontend Lead | Implements frontend components, UIs, client workflows, and cross-service UI integration. |
| **Gemma** | QA Lead | Reviews diffs, audits contract boundaries, enforces test pass rates, secret scans, and manifests. |
| **Local-LLM** | GitOps Lead | Executes Git operations following D025 safety protocols and persists verified release commits. |
| **CONTRACT-01** | Agent Contract Layer | Every worker is bounded by a structured YAML contract specifying `allow`, `deny`, file limits, and token budgets. |
| **KNOW-01** | Knowledge API | Agents query compiled graph context instead of manually scraping files. Queries are checked against contract scope. |
| **HARNESS-01** | Governed Harness Loop | Governed agent execution runtime enforcing pre/post-execution contract verification gates. |
| **D025** | Destructive Safety | Destructive actions require backup verification, pre-condition checks, and architect approval. |
| **Shutdown** | Mandatory Exit | Every agent session must conclude with `stackmind shutdown <agent>`. |

# StackMind Multi-Agent Pipeline Demo: Empty Project Guide

This guide demonstrates how to initialize StackMind on a **completely empty project** and run the multi-agent pipeline to develop, test, review, and commit a new feature from scratch.

In this workflow, **the user only writes a feature request** to Claude's inbox. Each agent is then launched as an LLM session (Claude Code, OpenAI Codex, Gemini, etc.) that reads `AGENTS.md`, checks its inbox, and follows the governance protocol autonomously.

---

## 🛠️ Step 1: Create and Initialize the Project

Start by creating a brand-new directory and setting up the StackMind runtime:

```powershell
# 1. Create a new directory and initialize Git
mkdir stackmind-demo
cd stackmind-demo
git init

# 2. Initialize StackMind
stackmind init .

# 3. Build the initial empty code graph
stackmind graph build -p .
```

* **What happened automatically:**
  - `.sync/` directory containing agent configuration, boot snapshots, and workspaces is created.
  - `AGENTS.md` is generated in the root, defining the team hierarchy and governance rules.
  - The initial knowledge graph index is built.

---

## 📝 Step 2: The User Writes the Task (Your Only Manual Step)

Create a feature request file in Claude's inbox:

```powershell
# Create the task file
New-Item -ItemType File -Path .sync/inbox/claude/2026-07-23_CEO_init_calculator.md -Force
```

Write the following content into that file:

```markdown
# Work Order Request

from: CEO
to: claude
priority: P1
date: "2026-07-23"

## Task
Create a simple calculator module in `calculator.py` with `add(a, b)` and `subtract(a, b)` functions.
Write unit tests covering both functions in `tests/test_calculator.py`.

## Acceptance Criteria
- `add(a, b)` returns the sum of a and b.
- `subtract(a, b)` returns the difference of a and b.
- Write unit tests verifying both functions.
```

---

## 🚀 Step 3: Run the Agent Pipeline

Each agent is a separate LLM coding session (Claude Code, Codex CLI, Gemini CLI, etc.) pointed at your project directory. Every agent reads `AGENTS.md` on startup, which tells it how to check its inbox, follow governance rules, and hand off work to the next agent.

> **How it works:** You open a new LLM session, tell it "You are agent `<name>`, read AGENTS.md and process your inbox", and the agent does the rest.

### 1. Launch Claude (Architect)

Open a **Claude Code** session in the project directory and prompt:

```
You are agent "claude" on the stackmind project at this directory.
Read AGENTS.md, boot from .sync/runtime/boot/claude.boot.yaml,
and process your unread inbox at .sync/inbox/claude/.
```

Claude reads your feature request and autonomously:
- Creates `.sync/work-orders/ACTIVE/WO-001.yaml` with the task breakdown.
- Creates `.sync/contracts/WO-001.yaml` specifying which files the developer is allowed to touch.
- Writes an assignment message to `.sync/inbox/codex/`.
- Runs `stackmind shutdown claude` to persist its session.

---

### 2. Launch Codex (Developer)

Open a **Codex CLI** (or any LLM coding agent) session and prompt:

```
You are agent "codex" on the stackmind project at this directory.
Read AGENTS.md, boot from .sync/runtime/boot/codex.boot.yaml,
and process your unread inbox at .sync/inbox/codex/.
```

Codex reads its assignment, queries the knowledge graph for context, and autonomously:
- Implements `calculator.py` with `add()` and `subtract()`.
- Writes `tests/test_calculator.py` with unit tests.
- Runs `stackmind graph update -p .` to update the knowledge graph.
- Sends a review request to `.sync/inbox/gemma/`.
- Sends a completion notice to `.sync/inbox/claude/`.
- Runs `stackmind shutdown codex` to persist its session.

---

### 3. Launch Gemma (QA Reviewer)

Open a **Gemini CLI** (or any LLM agent) session and prompt:

```
You are agent "gemma" on the stackmind project at this directory.
Read AGENTS.md, boot from .sync/runtime/boot/gemma.boot.yaml,
and process your unread inbox at .sync/inbox/gemma/.
```

Gemma reviews Codex's code and autonomously:
- Runs `pytest` and `stackmind validate .`.
- Writes an `APPROVED` verdict to `.sync/inbox/claude/`.
- Writes a verdict notice to `.sync/inbox/codex/`.
- Runs `stackmind shutdown gemma` to persist its session.

---

### 4. Launch Claude (Route Approval → GitOps → Close)

Re-open a **Claude Code** session and prompt:

```
You are agent "claude" on the stackmind project at this directory.
Read AGENTS.md, boot from .sync/runtime/boot/claude.boot.yaml,
and process your unread inbox at .sync/inbox/claude/.
```

Claude receives Gemma's approval and autonomously:
- Instructs Local-LLM (or handles directly) to commit the code to Git.
- Marks WO-001 as `COMPLETED`.
- Writes a status report to `.sync/inbox/CEO/` with the commit hash and test summary.
- Runs `stackmind shutdown claude` to persist its session.

---

## 🏁 Step 4: Verify Deliverables

```powershell
# 1. Check the generated code
cat calculator.py
cat tests/test_calculator.py

# 2. Run the tests yourself
pytest tests/test_calculator.py

# 3. Check the git log
git log --oneline

# 4. Read your completion report
cat .sync/inbox/CEO/*.md
```

---

## 📌 Key Concepts

| Concept | Description |
|---------|-------------|
| **AGENTS.md** | The governance contract every agent reads on startup. Defines authority, rules, and protocols. |
| **Inbox System** | Agents communicate via files in `.sync/inbox/<agent>/`. Messages are moved to `_read/` after processing. |
| **Boot Snapshots** | Each agent's state is tracked in `.sync/runtime/boot/<agent>.boot.yaml`. |
| **Knowledge Graph** | `stackmind graph build` / `graph update` compiles source code into a queryable symbol index. |
| **Work Orders** | Formal task assignments created by the architect, stored in `.sync/work-orders/ACTIVE/`. |
| **Contracts** | Scope boundaries defining which files/modules a worker agent is allowed to modify. |
| **Shutdown Protocol** | Every agent must run `stackmind shutdown <agent>` before ending its session. |

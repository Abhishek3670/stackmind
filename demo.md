# StackMind Multi-Agent Pipeline Demo Guide

This guide demonstrates how the StackMind agent pipeline processes a task end-to-end. 

In this workflow, **the user only writes a feature request** to Claude's inbox. The entire remaining pipeline—work order creation, contract definition, code implementation, testing, QA review, and git commits—is handled automatically by the agent swarm via the `stackmind harness`.

---

## 🛠️ Step 1: Initialize the Project

Start by initializing StackMind on the target repository and building the code graph:

```powershell
stackmind init .
stackmind graph build -p .
stackmind validate .
```

---

## 📝 Step 2: The User Writes the Task (Your Only Manual Step)

Create a feature request file in Claude's inbox at `.sync/inbox/claude/2026-07-22_CEO_task.md`:

```markdown
# Work Order Request

from: CEO
to: claude
priority: P1
date: "2026-07-22"

## Task
Add validation to the file upload module to reject any file that is not a PDF or exceeds 10MB.

## Acceptance Criteria
- Files must be PDF only (return 400 Bad Request if not).
- Max file size is 10MB (return 413 Payload Too Large if exceeded).
- Write unit tests covering both validation gates.
```

---

## 🚀 Step 3: Trigger the Pipeline

Run the agents sequentially using the `stackmind harness`. The harness automatically handles the lock system, validates outputs, and updates the states.

### 1. Boot Claude (Architect)
Claude reads your request, plans the solution, and **automatically generates the Work Order AND the Agent Contract** for the developer:
```powershell
stackmind harness run-once claude -p .
```
* **What happened automatically:** 
  - `.sync/work-orders/ACTIVE/WO-021.yaml` is created.
  - `.sync/contracts/WO-021.yaml` (specifying allowed/denied modules and budgets) is generated.
  - An assignment message is placed in Codex's inbox.

---

### 2. Boot Codex (Developer)
Codex reads the assignment, queries the graph for context, writes the validation logic and tests, and updates the knowledge graph:
```powershell
stackmind harness run-once codex -p .
```
* **What happened automatically:**
  - Codex implements the validation logic and test cases.
  - The **Harness Contract Gate** verifies that Codex's code changes are within the contract's allowed boundaries and budgets.
  - A review request is sent to Gemma's inbox.

---

### 3. Boot Gemma (QA Reviewer)
Gemma reviews Codex's code, runs the test suite, and ensures all security checks pass:
```powershell
stackmind harness run-once gemma -p .
```
* **What happened automatically:**
  - Gemma runs `pytest` and `stackmind validate .`.
  - Places the `APPROVED` verdict notice in Claude's inbox.

---

### 4. Boot Claude (Route Approval)
Claude receives Gemma's approval and instructs the GitOps agent to commit the code:
```powershell
stackmind harness run-once claude -p .
```

---

### 5. Boot Local-LLM (GitOps Commit)
Local-LLM stages and commits the code and the `.sync` state history to Git:
```powershell
stackmind harness run-once local-llm -p .
```

---

### 6. Boot Claude (Close Work Order)
Claude closes the loop, marks the work order completed, and writes a status report back to your inbox:
```powershell
stackmind harness run-once claude -p .
```

---

## 🏁 Step 4: Read Your Results

Check your inbox at `.sync/inbox/CEO/` to read the completion report from Claude containing the commit hash and test run summaries.

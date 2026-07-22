# StackMind Phase 1: Live Contract Governance Demo Guide

This guide shows you how to run a live testing cycle of the **Phase 1 Agent Governance and Contract Enforcement** system on any existing or empty Python project (including StackMind itself).

---

## 🛠️ Step 1: Initialize StackMind & Build the Graph

Open your terminal in the target project directory and initialize StackMind:

```powershell
# 1. Initialize StackMind structure
stackmind init .

# 2. Build the initial knowledge graph
stackmind graph build -p .

# 3. Verify the initialization passes standard validation
stackmind validate .
```

---

## 📋 Step 2: Define a Work Order

StackMind requires contracts to bind directly to a work order. Create a work order file at `.sync/work-orders/ACTIVE/WO-101.yaml`:

```yaml
id: "WO-101"
type: FEATURE
title: "Implement contract enforcement gates"
status: ACTIVE
priority: P0
assigned_agents: ["codex"]
dependencies: []
plan_ref: "PLANv3.md"
created: "2026-07-22"
updated: "2026-07-22"
description: |
  Add runtime and validation gates to prevent agents from touching files out-of-scope.
deliverable:
  type: "module"
  path: "validators/knowledge/contract.py"
  description: "Agent contract schema parser and graph scope validation engine"
```

---

## 📜 Step 3: Define the Agent Contract

Create a contract file under `.sync/contracts/WO-101.yaml` (the naming matches the Work Order ID). 

This contract grants permission to access `validators.knowledge` and `cli.contract`, but explicitly **denies** access to the `auth` module and `validators.harness`:

```yaml
agent_id: "agent-codex-07"
work_order: "WO-101"
identity:
  role: "implementer"
  reports_to: "senior-architect"
scope:
  allow:
    - module: "validators.knowledge"   # Allow access to this module
      depth: 2                        # Allow nodes up to 2 hops away in the call graph
    - module: "cli.contract"          # Allow access to this module
      depth: 1                        # Allow direct callers/callees
  deny:
    - module: "auth.*"                # Explicitly deny all sub-modules under auth
    - module: "validators.harness"    # Explicitly deny harness module
  write: "read-write"                 # Can be "read-write" or "read-only"
budget:
  max_files_touched: 6
  max_tokens: 40000
  expires_at: "2028-12-31T23:59:59Z"   # UTC expiration timestamp (ISO-8601)
```

---

## 🔍 Step 4: Show and Inspect the Contract

Validate the contract against `schemas/contract.schema.json` and inspect its parameters:

```powershell
stackmind graph contract show WO-101
```

**Example Output:**
```
[PASS] Contract is valid (loaded from WO-101.yaml)
Agent ID: agent-codex-07
Work Order ID: WO-101
Write Mode: read-write
Identity:
  role: implementer
  reports_to: senior-architect
Budget:
  max_files_touched: 6
  max_tokens: 40000
  expires_at: 2028-12-31T23:59:59Z
          Allow Rules           
┌──────────────────────┬───────┐
│ Module Pattern       │ Depth │
├──────────────────────┼───────┤
│ validators.knowledge │ 2     │
│ cli.contract         │ 1     │
└──────────────────────┴───────┘
      Deny Rules      
┌────────────────────┐
│ Module Pattern     │
├────────────────────┤
│ auth.*             │
│ validators.harness │
└────────────────────┘
```

To display only the scope boundary rules:
```powershell
stackmind graph scope WO-101
```

---

## ⚡ Step 5: Test Operation Validation Gates

Run the validator CLI command to test how the engine reacts to different read/write operations.

### Test A: Allowed Operation
Checking access to a file that falls inside the allowed module list:
```powershell
stackmind graph contract validate WO-101 --op "edit validators/knowledge/contract.py"
```
**Output:**
```
[ALLOWED] Edit validators/knowledge/contract.py is allowed under contract WO-101.
```

### Test B: Denied Operation (Deny Rule Match)
Checking access to a file that matches an explicit deny rule:
```powershell
stackmind graph contract validate WO-101 --op "edit validators/harness/runner.py"
```
**Output:** (Exits with code `1`)
```
[REJECTED] Module validators.harness.runner matches deny rules.
```

### Test C: Denied Operation (Out of Scope)
Checking access to a file that is neither allowed nor denied (fail-closed model):
```powershell
stackmind graph contract validate WO-101 --op "edit cli/main.py"
```
**Output:** (Exits with code `1`)
```
[REJECTED] Module cli.main is out of allowed module scope boundaries.
```

---

## 🕵️ Step 6: Explain Denials

If a specific symbol query is rejected, you can ask StackMind to explain why access was denied to that node:

```powershell
stackmind graph explain-denial WO-101 --node AgentRunner
```

**Output:**
```
Target Symbol: AgentRunner (CLASS-6ee352d77a9af6fd)
Resolved Module: validators.harness.runner
[DENIED] Access is explicitly denied by rule(s):
  - deny: validators.harness
```

---

## 🏁 Step 7: Final Validation Run

Run the global repository validator to ensure all files, configurations, and work orders in the project are aligned and consistent:

```powershell
stackmind validate .
```

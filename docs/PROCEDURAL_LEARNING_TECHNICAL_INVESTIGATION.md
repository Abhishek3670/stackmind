# Deep Technical Code Investigation: Procedural Learning vs. StackMind Codebase

**Document Analyzed**: `StackMind_Verified_Procedural_Learning_FINAL.md`  
**Target Codebase**: `stackmind` (v2.1.0-dev / v3.0 Architecture)  
**Investigation Date**: 2026-09-01  
**Status**: COMPLETE — ALL SUBSYSTEMS VERIFIED  

---

## 1. Executive Verdict & Core Finding

### Final Verdict
> **APPLICABLE AND HIGHLY COMPATIBLE WITHOUT DESTROYING THE BASE.**
>
> The verified procedural learning architecture defined in `StackMind_Verified_Procedural_Learning_FINAL.md` is **fully applicable to the actual StackMind codebase**. It does not destroy, regress, or undermine any foundational invariants.
>
> Rather than replacing existing systems, the proposal builds upon StackMind's existing architectural primitives:
> 1. **Symbol Registry & NodeID Birth-Hashing** (`validators/knowledge/registry.py`)
> 2. **Three-Tier Storage Model** (`validators/knowledge/storage.py`)
> 3. **Fail-Closed Contract Layer (`CONTRACT-01`)** (`validators/knowledge/contract.py`)
> 4. **Governed Harness Execution Sandbox (`HARNESS-01`)** (`validators/harness/runner.py`)
> 5. **Five-Layer Runtime Validation Engine** (`cli/validate.py`)
> 6. **Destructive Operations Safeguards (`D025`)** (`validators/harness/d025_gate.py`)

---

## 2. High-Level Architectural Mapping

```
                                  ==================================================
                                  PROPOSED VERIFIED PROCEDURAL LEARNING ENGINE
                                  ==================================================
                                                          │
          ┌───────────────────────────────────────────────┼───────────────────────────────────────────────┐
          ▼                                               ▼                                               ▼
┌─────────────────────────────────┐             ┌─────────────────────────────────┐             ┌─────────────────────────────────┐
│     PHASE 0: VERIFICATION       │             │   EXPERIENCE & KNOWLEDGE STORE  │             │     GOVERNANCE & CONTRACTS      │
│     & RUNNER DIFF SUBSTRATE     │             │     (T0 / T1 / T2 ARCHITECTURE) │             │    (CONTRACT-01 / HARNESS-01)   │
├─────────────────────────────────┤             ├─────────────────────────────────┤             ├─────────────────────────────────┤
│ • Authoritative FS Snapshots    │             │ • T0: Symbol Registry (Birth)   │             │ • Fail-Closed Scope Boundary    │
│ • Runner Diff vs LLM Claim      │ ──────────► │ • T1: Sharded JSON Manifests    │ ──────────► │ • Multi-Dimensional Gates       │
│ • Staged Temp Sandbox           │             │ • T2: Rebuildable SQLite Index  │             │ • Risk-Tiered Promotion         │
│ • D025 Pre/Post Verification    │             │ • Immutability & Reversibility  │             │ • Anti-Learning & Decay Engine  │
└─────────────────────────────────┘             └─────────────────────────────────┘             └─────────────────────────────────┘
          │                                               │                                               │
          └───────────────────────────────────────────────┼───────────────────────────────────────────────┘
                                                          ▼
                                  ==================================================
                                  ACTUAL STACKMIND CODEBASE SUBSYSTEMS
                                  ==================================================
                                  • `validators/harness/runner.py`
                                  • `validators/harness/contract_gate.py`
                                  • `validators/harness/d025_gate.py`
                                  • `validators/knowledge/registry.py`
                                  • `validators/knowledge/storage.py`
                                  • `validators/knowledge/writer.py`
                                  • `validators/knowledge/api.py`
                                  • `validators/knowledge/contract.py`
                                  • `cli/validate.py`
                                  • `cli/lock.py`
```

---

## 3. Subsystem-by-Subsystem Technical Code Investigation

### 3.1 Harness Runtime & Phase 0 Verification Substrate

#### Codebase Analysis
* **File**: `validators/harness/runner.py`
  * **Staging Sandbox** (`lines 485–509`): `AgentRunner._validate_staged_state()` already constructs an isolated sandbox copy of the project via `tempfile.TemporaryDirectory()` and runs `validate_runtime(staged_root)` before applying writes to production.
  * **Pre-Execution Contract Gate** (`lines 248–256`): Calls `verify_pre_execution()` to validate contract expiration and work order alignment.
  * **Post-Execution Contract Gate** (`lines 284–294`): Calls `verify_post_execution()` to validate modified files against contract rules.
  * **D025 Safeguards** (`lines 351–363`): Evaluates shell commands against `D025Gate` before execution.

#### Document Proposal (§28)
* **Runner-Owned Change Detection (§28.2)**: Derives filesystem deltas from before/after snapshots of the runner workspace rather than trusting the LLM's `modified_files` field.
* **Observed vs. Declared Comparison (§28.3)**: Any undeclared filesystem mutation triggers a routing to the Gemma QA review path.
* **Multi-Dimensional Verification (§28.6)**: Replaces overloaded `verified = true` with explicit flags (`scope_verified`, `state_verified`, `code_verified`, `behavioral_verified`, `security_verified`, `outcome_verified`).

#### Compatibility & Base Impact
* **Impact**: **Zero Base Destruction.**
* **Integration**: In `AgentRunner.run_once()`, taking a snapshot before executing changes and calculating `actual_modified_files = set(after_snapshot) - set(before_snapshot)` seamlessly replaces the reliance on `decision.modified_files` in `verify_post_execution()`.

---

### 3.2 Symbol Registry, Knowledge Identity & Storage

#### Codebase Analysis
* **File**: `validators/knowledge/registry.py`
  * **Birth-Hash Identity** (`lines 59–78`): Deterministic NodeID formula: `TYPE-first16(SHA256(path:qualname))`.
  * **Extensible Kinds** (`lines 21–52`): `KIND_PREFIXES` maps entity types (`module`, `class`, `function`, `workorder`, `decision`, etc.) to short prefixes.
  * **Sharded Storage** (`lines 109–125`): Symbols stored in 2-hex buckets under `.sync/knowledge/registry/xx/ID.json`.
* **File**: `validators/knowledge/storage.py`
  * **Three-Tier Storage Model**:
    * **T0**: Symbol Registry (canonical identity).
    * **T1**: Sharded JSON nodes and sequential revision manifests (`REV-0000000001.json`).
    * **T2**: Derived cache (reverse index, vector cache) that is gitignored and 100% rebuildable.
* **File**: `validators/knowledge/writer.py`
  * **Atomic Writes** (`lines 32–45`): Implements `_write_if_changed()` with temporary file swaps and advisory locking.
  * **Ghost Node Reconciliation** (`lines 89–190`): Reconciles vanished nodes with rename detection.

#### Document Proposal (§17–§18, §23.4–§23.5)
* **Canonical Experience Artifacts**: Stored with deterministic birth-hash NodeIDs (`EXP-` and `SKILL-`).
* **T2 Experience Index**: SQLite database (`.sync/knowledge/experience.db`) indexing experiences, task metadata, embeddings, and full-text search.
* **Rebuildability**: If `experience.db` is removed, running `stackmind experience compile` completely reconstructs the index from `.sync/` artifacts.

#### Compatibility & Base Impact
* **Impact**: **Zero Base Destruction.**
* **Integration**:
  * Adding `"skill": "SKILL"` and `"experience": "EXP"` to `KIND_PREFIXES` in `registry.py` requires zero changes to existing compiler parsers.
  * The T2 SQLite database cleanly lives alongside the existing reverse graph index and vector cache in `.sync/knowledge/`.

---

### 3.3 Contract Layer & Knowledge API (`CONTRACT-01` & `KNOW-01`)

#### Codebase Analysis
* **File**: `validators/knowledge/contract.py`
  * **Scope Enforcement** (`lines 125–186`): `AgentContract.is_node_in_scope()` executes graph-level BFS traversal up to `depth` against allow/deny rules, failing closed on unknown nodes or expired contracts.
* **File**: `validators/knowledge/api.py`
  * **Access Control** (`lines 172–181`): `_enforce_node()` validates node access against active contracts on every query.
  * **Context Assembly** (`lines 599–691`): `assemble_context()` constructs a bounded, ranked context bundle within a strict `token_budget`.

#### Document Proposal (§23.11–§23.12, §24.2)
* **Contract-Gated Skill Retrieval**: Skills can only be retrieved and applied if their preconditions and target files fall within the agent's active Contract allow rules and do not violate deny rules.
* **Evidence-Aware Context Assembly**: Procedural skills are retrieved as compact, bounded procedures alongside graph context, preventing token explosion.

#### Compatibility & Base Impact
* **Impact**: **Zero Base Destruction.**
* **Integration**:
  * `KnowledgeAPI` can easily be extended with `retrieve_skills(query, contract=...)`.
  * Preconditions on candidate skills (e.g. required modules) are validated directly using `contract.is_node_in_scope()`.

---

### 3.4 Governance, Authority Model & Safety Rules

#### Codebase Analysis
* **Authority Protocol** (`AGENTS.md`):
  * **CEO**: Priorities & release targets.
  * **Claude (Architect)**: Planning, contracts, work orders (**STRICTLY NO SOURCE IMPLEMENTATION**).
  * **Codex / Gemini (Workers)**: Implementation strictly within contract scope.
  * **Gemma (QA)**: Independent test verification & approval gates.
  * **Local-LLM**: GitOps & release automation.
* **Validation Substrate**: `cli/validate.py` enforces 5 layers:
  1. Layer 1: Schema Validation
  2. Layer 2: Structural Validation
  3. Layer 3: Protocol Compliance
  4. Layer 4: Boot Integrity
  5. Layer 5: Knowledge Registry Invariants

#### Document Proposal (§23.8, §24.4, §24.5)
* **Risk-Tiered Promotion**:
  * *Low Risk* (formatting/analysis): Automated promotion.
  * *Medium/High Risk* (code modifications/refactoring): Historical replay + canary testing + Gemma QA review.
  * *Critical* (destructive/security): Human approval required.
* **Anti-Learning & Staleness**: Skills decay to `STALE` on code changes or test regressions, triggering revalidation or rollback to `v(N-1)`.

#### Compatibility & Base Impact
* **Impact**: **Zero Base Destruction.**
* **Integration**:
  * Skill learning operates entirely at the **Worker/Harness level**. It does not generate contracts or alter canonical architecture.
  * Promoted skills become versioned YAML artifacts in `.sync/skills/`, checked by a new Layer-6 validation rule in `cli/validate.py`.

---

## 4. Gap Analysis: Existing vs. Required Primitives

| Component | Status in Codebase | Required from `FINAL.md` | Effort / Complexity |
|---|---|---|---|
| **Symbol Identity** | Implemented (`validators/knowledge/registry.py`) | Add `SKILL-` & `EXP-` prefixes | Trivial (< 10 LOC) |
| **Contract Enforcement** | Implemented (`validators/knowledge/contract.py`) | Validate skill scope vs contract | Low (~40 LOC) |
| **D025 Command Safety** | Implemented (`validators/harness/d025_gate.py`) | Re-use for skill command validation | Zero changes |
| **Runner FS Sandbox** | Implemented (`validators/harness/runner.py`) | Add Phase 0 before/after FS snapshot | Medium (~150 LOC) |
| **Verification Dimensions** | Implicit / Boolean | Explicit multi-dimensional dataclass | Low (~50 LOC) |
| **Experience Compiler** | Absent (raw `.sync/` files only) | Compile `.sync` artifacts to SQLite | Medium (~300 LOC) |
| **Pattern Miner** | Absent | Offline clustering of recurring episodes | Medium-High (~400 LOC) |
| **Skill Distiller** | Absent | Extract reusable procedures from clusters | Medium (~300 LOC) |
| **3-Level Verification** | Single-pass `pytest` | 1. Structural $\to$ 2. Replay $\to$ 3. Canary | Medium (~350 LOC) |
| **Skill Versioning** | Absent | `.sync/skills/` version tree & rollback CLI | Low-Medium (~250 LOC) |
| **Layer-6 Skill Validator** | Layers 1–5 in `cli/validate.py` | Add skill schema & link validation | Low (~100 LOC) |

---

## 5. Risk Analysis & Mitigations

| Risk Scenario | Potential Threat to Base | Built-in Mitigation in `FINAL.md` |
|---|---|---|
| **1. Snapshot I/O Overhead** | Slowing down runner execution by hashing the entire workspace on every run. | §28.2: Use metadata-first checks (mtime, size) and content-hash only modified candidates, scoped to contract paths. |
| **2. Lock Contention & TOCTOU** | Multiple agents corrupting knowledge records during concurrent runs. | Enforced by existing `cli/lock.py` and atomic write routines in `validators/knowledge/writer.py`. |
| **3. Bad Skill Propagation** | An LLM learns a broken workaround and continually repeats it. | §23.9 ("Failure is evidence, not knowledge"), §24.3 (Staleness triggers on code changes), §24.4 (Decay & rollback). |
| **4. Context Bloat** | Huge procedural prompt injections exhausting LLM token budget. | `KnowledgeAPI.assemble_context()` strictly enforces `token_budget` (1200 tokens default) with ranked skill retrieval. |
| **5. Contract Boundary Bypass** | A learned procedure attempts to edit out-of-scope files. | `AgentContract.is_node_in_scope()` fails closed on unpermitted modules during post-execution checks. |

---

## 6. Implementation Roadmap

```
Phase 0: Verification Foundation
  ├── WorkspaceSnapshot engine (before/after diff)
  ├── Observed vs declared change verification
  └── Multi-dimensional verification dataclasses
        ↓
Phase 1 & 2: Experience Store & Compilation
  ├── Experience artifact schema & birth-hash NodeID
  ├── SQLite T2 experience index builder
  └── `stackmind experience compile` CLI command
        ↓
Phase 3 & 4: Skill Storage & Registry
  ├── `.sync/skills/` schema & version directory layout
  ├── `SKILL-` kind in SymbolRegistry
  └── `stackmind skill list/show/rollback` CLI
        ↓
Phase 5 & 6: Pattern Mining & Verification Pipeline
  ├── Offline episodic pattern miner ($N \ge 3$)
  ├── Skill distiller & candidate generator
  └── 3-level verification pipeline (Structural $\to$ Replay $\to$ Canary)
        ↓
Phase 7 & 8: Context Retrieval & Continuous Lifecycle
  ├── `KnowledgeAPI.retrieve_skills()` integration
  ├── Staleness detection & automatic skill decay
  └── Layer-6 Skill validation in `stackmind validate`
```

---

## 7. Conclusion

The architecture presented in `StackMind_Verified_Procedural_Learning_FINAL.md` is **sound, rigorous, and directly aligned with the StackMind codebase**. Implementing this design will extend StackMind with self-improvement capabilities while strictly maintaining the project's core principles: **evidence-backed truth, deterministic storage, fail-closed contracts, and verifiable trust boundaries**.

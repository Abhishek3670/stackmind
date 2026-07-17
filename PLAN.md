# StackMind — Implementation Plan (Compiler-Backed Engineering Runtime)

**Version:** 2.0
**Supersedes:** PLAN.md (v1 — runtime flaw analysis), PLAN-v1.md
**Authoritative source:** `docs/STACKMIND_ARCHITECTURE.md` (Architecture Handbook)
**Date:** 2026-07-17
**Status:** OPEN — awaiting CEO prioritization and RFC acceptance sign-off
**Author:** Claude (Senior Architect), Session 1

---

## Executive Summary

StackMind v1.2.0 ships a fully functional **Runtime Governance** layer (Pillar 1): CLI, 4-layer validation, write-lock, work orders, agent protocols. The old PLAN.md addressed flaw patches to this governance layer — those fixes are now implemented and shipped.

This plan charts the path from governance runtime to **compiler-backed engineering runtime** — implementing Pillars 2 (Knowledge Compiler) and 3 (Harness Runtime) as specified in the Architecture Handbook and six RFCs.

The central insight: every AI agent session today rebuilds its understanding from scratch. The Knowledge Compiler transforms project state into persistent, deterministic, queryable knowledge. Agents start from shared understanding instead of independently rediscovering it.

---

## Current State vs. Target

### What Exists (Pillar 1 — Shipped, v1.2.0)

| Component | Status | Location |
|---|---|---|
| CLI entry point | ✅ Shipped | `cli/main.py` — 7 commands |
| 4-layer validation | ✅ Shipped | `cli/validate.py` |
| Write lock (PLAT-03) | ✅ Shipped | `cli/lock.py` |
| Promote with validation gate (CLAUDE-01) | ✅ Shipped | `cli/promote.py` |
| Shutdown with inbox drain (GEMMA-02) | ✅ Shipped | `cli/shutdown.py` |
| Migration engine | ✅ Shipped | `cli/migrate.py` |
| Normalization decisions (PLAT-04) | ✅ Shipped | `cli/decisions.py` |
| Canonical drift detection (PLAT-01) | ✅ Shipped | `cli/validate.py` (Layer 4) |
| .sync-ref anchoring (PLAT-05) | ✅ Shipped | `cli/validate.py` |
| CODEX-01 fresh TREE reads | ✅ Shipped | `cli/shutdown.py` |
| Schemas (7 runtime) | ✅ Shipped | `schemas/` |
| Tests (>90% coverage on cli/) | ✅ Shipped | `tests/` |

### What Must Be Built (Pillars 2 & 3)

| Component | Status | Planned Location |
|---|---|---|
| Symbol Registry (T0, canonical) | ❌ Not started | `validators/knowledge/registry.py` + `.sync/knowledge/registry/` |
| Compiler Frontend (parse + resolve) | ❌ Not started | `validators/knowledge/compiler/` |
| IR (intermediate representation) | ❌ Not started | `validators/knowledge/compiler/ir.py` |
| Storage/Writer (nodes, revisions) | ❌ Not started | `validators/knowledge/storage.py` |
| Projection Engine (reverse index, search, metrics) | ❌ Not started | `validators/knowledge/projections/` |
| Incremental Compiler + Rename Detection | ❌ Not started | `validators/knowledge/compiler/incremental.py` |
| Background Intelligence (enricher) | ❌ Not started | `validators/knowledge/enricher.py` |
| Knowledge API (read-only surface) | ❌ Not started | `validators/knowledge/api.py` |
| Layer-5 Validation (knowledge) | ❌ Not started | `validators/knowledge/validate.py` |
| CLI `graph` command group | ❌ Not started | `cli/graph.py` |
| Knowledge schemas | ❌ Not started | `schemas/knowledge/` |
| Agent Runner (Harness) | ❌ Not started | TBD (post Pillar 2) |
| Retrieval tools (WebSearchRunner) | ❌ Not started | TBD (post Pillar 2) |

---

## Phase 0 — Architecture Freeze (CURRENT GATE)

**Objective:** Close the planning phase. Record RFC acceptance. Authorize implementation.

**Status:** All 6 RFCs written. Acceptance not formally recorded.

**Deliverables:**
1. Record formal acceptance of RFC-001, RFC-002, RFC-003 (Phase 0 exit gate)
2. Record acceptance of RFC-004, RFC-005, RFC-006 (can trail, gates later phases)
3. Commit the docs/ planning artifacts to version control
4. This PLAN.md committed as the authoritative roadmap

**Exit gate:** RFC-001/002/003 signed off by CEO. No implementation code merges until this gate passes.

**Decision required:** CEO must confirm GO on the three core RFCs.

---

## Phase 1 — Identity Foundation

**Objective:** Permanent, deterministic symbol identity backed by a canonical, sharded registry.

**Depends on:** Phase 0 (RFC-001 accepted)
**Assigned to:** Codex (Backend Lead)
**Priority:** P0

### Workstreams

1. **Registry store** — Sharded per-symbol JSON files under `.sync/knowledge/registry/` (2-hex prefix buckets)
2. **Birth-hash minting** — `NodeID = TYPE-first16(SHA256(path:qualname))` at first sighting, frozen forever
3. **Registry lifecycle** — load / create-if-missing / upsert / mark-obsolete / alias
4. **Registry schema** — `schemas/knowledge/symbol.schema.json` (Draft-7)
5. **Layer-5 validation stub** — unique IDs, ID = birth-hash of earliest history key, bijection check
6. **Migration hook** — registry participates in `stackmind migrate`

### Files Created

```
schemas/knowledge/symbol.schema.json
validators/knowledge/__init__.py
validators/knowledge/registry.py
validators/knowledge/validate.py          (Layer-5 stub)
tests/test_registry.py
```

### Acceptance Gate

- [ ] Same repo compiled twice → identical NodeIDs
- [ ] Registry survives deletion of all derived projections
- [ ] `stackmind validate` Layer-5 passes on a seeded registry
- [ ] `stackmind validate` Layer-5 fails on injected duplicate ID
- [ ] Rename-stability is NOT asserted here (deferred to Phase 5, per C4)

---

## Phase 2 — Compiler Frontend (Deterministic)

**Objective:** Deterministic Source → IR. No LLMs. Byte-identical output across runs.

**Depends on:** Phase 1, RFC-003 accepted
**Assigned to:** Codex (Backend Lead)
**Priority:** P0

### Workstreams

1. **LibCST parser** — modules, classes, functions/methods; qualified-name stack derivation
2. **Symbol table build** — every definition → `(path, qualname)` → registry lookup → NodeID
3. **Jedi-backed resolver** — intra-repo imports/calls; repo-scoped only (no installed packages)
4. **Resolution tiers** — RESOLVED / EXTERNAL / UNRESOLVED (placeholder edges, never dropped)
5. **IR definition** — in-memory canonical form; pure function of (source, .sync, git, registry, compiler_version)
6. **Two-pass resolution** — pass 1 registers all symbols; pass 2 resolves edges (forward refs resolve)

### Files Created

```
validators/knowledge/compiler/__init__.py
validators/knowledge/compiler/parse.py
validators/knowledge/compiler/resolve.py
validators/knowledge/compiler/ir.py
tests/test_compiler_frontend.py
```

### Acceptance Gate (DETERMINISM)

- [ ] `compile(repo) == compile(repo)` — IR byte-identical across repeated runs
- [ ] IR byte-identical across fresh checkout at same commit
- [ ] Unresolved calls recorded (never dropped)
- [ ] No wall-clock, RNG, PID, or absolute path in IR
- [ ] External calls (stdlib/third-party) recorded as EXTERNAL, never linked to NodeIDs
- [ ] **Compile-twice-diff CI gate passes**

---

## Phase 3 — Storage Layer

**Objective:** Persist IR as sharded, schema-validated, deterministic JSON under `.sync/knowledge/`.

**Depends on:** Phase 2, RFC-002 accepted
**Assigned to:** Codex (Backend Lead)
**Priority:** P1

### Workstreams

1. **Directory layout** — `registry/` (T0), `nodes/<Type>/<2-hex>/` (T1), `revisions/` (T1), `cache/` (T2, gitignored)
2. **Node files** — deterministic block + outgoing edges inline + empty `ai` block
3. **Canonical serialization** — sorted keys, sorted set-arrays, fixed formatting, LF endings
4. **Revision stamping** — monotonic ID, parent link, git commit, .sync ref, compiler/schema/registry versions, counts
5. **Atomic writes** — temp-write + rename; crash never leaves half-written files
6. **Node/revision schemas** — `schemas/knowledge/{node,revision}.schema.json`
7. **Layer-5 expansion** — no dup IDs; edge targets exist or flagged; revision chain unbroken

### Files Created

```
schemas/knowledge/node.schema.json
schemas/knowledge/revision.schema.json
validators/knowledge/storage.py
validators/knowledge/writer.py
tests/test_storage.py
```

### Acceptance Gate

- [ ] IR → disk is deterministic (identical bytes for identical IR)
- [ ] One-symbol change rewrites only that node's file (+ registry shard)
- [ ] `stackmind validate` Layer-5 catches injected dangling edge
- [ ] Revision chain is monotonic and unbroken
- [ ] No wall-clock anywhere in node files (time lives only in revisions)

---

## Phase 4 — Projection Engine

**Objective:** Generate all derived projections from IR. Prove rebuildability (the platform's fundamental promise).

**Depends on:** Phase 3
**Assigned to:** Codex (Backend Lead)
**Priority:** P1

### Workstreams

1. **Reverse Index projection** (T2, gitignored) — `NodeID → [{source, relation}…]`, sharded by target bucket
2. **Search Index projection** (T2) — text search over names, signatures, summaries
3. **Metrics projection** (T2) — module/class/function counts, edge counts, coverage stats
4. **CLI `graph` command group** — `build`, `stats`, `versions` under `cli/graph.py`
5. **Projector contract** — pure function, declared inputs; no projector reads another's T2

### Files Created

```
cli/graph.py                              (new CLI command group)
validators/knowledge/projections/__init__.py
validators/knowledge/projections/reverse_index.py
validators/knowledge/projections/search.py
validators/knowledge/projections/metrics.py
tests/test_projections.py
```

### Acceptance Gate (REBUILDABILITY)

- [ ] Delete all projections → recompile → **identical** projections
- [ ] "Who calls X?" answered from reverse index without scanning all nodes
- [ ] `stackmind graph build` produces complete knowledge store from scratch
- [ ] `stackmind graph stats` reports node/edge/revision counts
- [ ] Projectors do not read each other's T2 output

---

## Phase 5 — Incremental Compiler + Rename Detection

**Objective:** Rebuild only affected symbols on change. Implement rename/move detection (C4).

**Depends on:** Phase 4
**Assigned to:** Codex (Backend Lead)
**Priority:** P1

### Workstreams

1. **Content-hash dirty detection** — unchanged files (by hash) skipped entirely
2. **Affected-set computation** — dirty symbols ∪ reverse-index inbound of deleted/renamed
3. **File watcher** (`stackmind graph watch`) — excludes `.sync/knowledge/` and cache dirs (no self-trigger)
4. **Rename/move detection** — match vanished birth-keys to appeared keys (kind + body-hash + owner + signature)
5. **Alias recording** — rename rebinds existing NodeID; low-confidence → delete+create
6. **Batch scheduler** — rapid events debounce; lock acquired per write-batch only
7. **CLI `graph update`** — incremental compile from Git diff

### Files Created

```
validators/knowledge/compiler/incremental.py
validators/knowledge/compiler/rename.py
validators/knowledge/compiler/watcher.py
cli/graph.py                              (add `update`, `watch` commands)
tests/test_incremental.py
tests/test_rename.py
```

### Acceptance Gate

- [ ] One file changed → only affected symbols recompile (verified via revision diff)
- [ ] **Rename test:** rename a function → NodeID unchanged, alias recorded, inbound edges intact
- [ ] **Move test:** relocate a file → NodeIDs unchanged, paths updated
- [ ] Watch daemon does not re-trigger itself
- [ ] Lock held only during write-batch (never during parse/resolve)
- [ ] Debouncing: rapid saves to one file compile once

---

## Phase 6 — Background Intelligence (Async, Non-Blocking)

**Objective:** Enrich nodes with LLM summaries and embeddings without touching the deterministic path.

**Depends on:** Phase 4, RFC-005 accepted
**Parallelizable with:** Phase 5
**Assigned to:** Gemini (Frontend Lead) or Codex
**Priority:** P2

### Workstreams

1. **Enrichment queue** — new/changed NodeIDs admitted; idempotent; rapid changes coalesce
2. **LLM summaries** → `ai.summary` + `confidence` + `enriched_hash` (self-describing staleness)
3. **Embeddings** → T2 gitignored cache; keyed by content hash (rename = cache hit)
4. **Four-mode privacy policy** — `full` / `signatures` / `local` / `off` (config-gated)
5. **Cost caps** — per-day token/call budget; exhaustion pauses queue, reports
6. **Failure discipline** — per-job isolation, exponential backoff, park-with-reason
7. **CI guard** — Stage-5 run produces zero diff outside `ai` blocks

### Files Created

```
validators/knowledge/enricher.py
validators/knowledge/enricher_queue.py
.sync/knowledge/cache/embeddings/         (gitignored)
schemas/knowledge/ai-block.schema.json
tests/test_enricher.py
```

### Acceptance Gate

- [ ] Compilation and queries succeed with enricher fully disabled
- [ ] Enabling enricher only adds `ai` fields (never modifies deterministic blocks)
- [ ] Killing enricher mid-run leaves deterministic state intact
- [ ] `enriched_hash != content_hash` correctly flags stale summaries
- [ ] Cost cap exhaustion pauses (not crashes); reported in `graph stats`
- [ ] **CI: Stage-5 diff is zero outside `ai` blocks**

---

## Phase 7 — Knowledge API + Agent Integration

**Objective:** Agents consume knowledge through a read-only API instead of re-reading files.

**Depends on:** Phase 4 (query surface), RFC-004 accepted
**Assigned to:** Codex + Gemini
**Priority:** P2

### Workstreams

1. **Four query primitives** — lookup (exact, alias-aware), filter (attribute scan), traversal (relational), search (semantic with text fallback)
2. **`assemble_context`** — bounded, ranked, revision-stamped context bundle for agent prompts
3. **Response envelope** — revision, git_commit, stale flag, semantic flag, confidence per result
4. **CLI `graph query`** — Q1/Q2/Q4; `graph callers`/`impact` — Q3; `graph context` — assembly
5. **Staleness handling** — flag-and-serve (never block-and-recompile on the read path)
6. **Agent protocol update** — `AGENTS.md`, `docs/protocols.md`: "query Knowledge API before parsing files"

### Files Created

```
validators/knowledge/api.py
cli/graph.py                              (add `query`, `callers`, `impact`, `explain`, `context` commands)
tests/test_knowledge_api.py
```

### Acceptance Gate

- [ ] Cross-file question answered via API with zero repo file reads
- [ ] Results carry provenance (revision + confidence)
- [ ] Alias-aware: query by old name finds renamed symbol
- [ ] `assemble_context` respects token budget; truncation reported (never silent)
- [ ] Absent embeddings → text fallback, response marked `semantic: false`
- [ ] Stale graph → results flagged `stale: true`, still served

---

## Phase 8 — Harness Runtime (Gated)

**Objective:** Governed agent execution loop — the third pillar.

**Depends on:** Phase 7 (Knowledge API adopted), RFC-006 accepted
**Gated by:** Demonstrated Knowledge-API adoption (per Verdict anti-orchestration discipline)
**Assigned to:** TBD
**Priority:** P3

### Workstreams

1. **Agent Runner** — Worker-level agent: poll inbox/WOs → assemble context → LLM → verify → write-back
2. **Checked locking** — lock wraps writes only; failure → backoff → defer+blocker
3. **Retrieval tools** — `search(query, k) → [Result]` normalized; gated, cached, cost-capped
4. **Prompt-injection defense** — external snippets quoted as evidence, never instructions
5. **Verification** — schema + staged `stackmind validate` before any write-back
6. **Observability** — structured events, meta block on reports (revision, provider, tokens, latency, cost)
7. **Loop safety** — >3 re-reads → abort+blocker (GEMMA-02 pattern)

### Acceptance Gate

- [ ] Agent Runner registers as Worker agent with full protocol citizenship
- [ ] TREE.yaml byte-identical after a full runner session (Worker authority)
- [ ] Lock acquisition is checked; failure → backoff → defer (never unlocked write)
- [ ] Invalid output never persists silently (verification gate)
- [ ] Retrieval cap exhaustion → internal-only (flagged), task continues
- [ ] Baseline-vs-augmented benchmark reportable from observability logs

---

## Dependency Graph

```
Phase 0 (RFC acceptance)
    │
    ├── Phase 1 (Identity)
    │       │
    │       └── Phase 2 (Compiler Frontend)
    │               │
    │               └── Phase 3 (Storage)
    │                       │
    │                       └── Phase 4 (Projection)
    │                               │
    │                               ├── Phase 5 (Incremental + Rename)
    │                               │       │
    │                               │       └── Phase 7 (API + Agent Integration)
    │                               │                   │
    │                               │                   └── Phase 8 (Harness — GATED)
    │                               │
    │                               └── Phase 6 (Background Intelligence — parallel with 5)
    │
    Critical Path: P0 → P1 → P2 → P3 → P4 → P5 → P7 → P8
```

---

## Cross-Cutting Requirements (All Phases)

### Invariants (must hold at every phase)

1. Runtime (Source + `.sync/` + Git) is canonical; knowledge is derived
2. Deterministic stages produce byte-identical output for identical inputs
3. Symbol identity is permanent (ID never changes)
4. Registry is canonical (T0): git-tracked, write-locked, validated, migrated
5. Embeddings are cache (T2): disposable, rebuildable, gitignored
6. Agents never write knowledge files
7. Deleting `.sync/knowledge/` never loses state — compiler rebuilds
8. Lock held only around writes (never during parse/resolve/enrichment)
9. No LLM in Stages 1–4

### Engineering Standards

- **Validation ships with features** — schema + Layer-5 checks in same PR as artifacts they guard
- **Determinism CI** — compile-twice-diff gate for Phases 2–4
- **Testing ladder** — unit → integration → schema fixtures → rebuildability
- **Provenance** — every projection traceable to graph revision (git SHA + compiler version)
- **Additive only** — new modules + new commands; existing CLI unchanged
- **Lock discipline** — checked acquisition, writes-only hold, always released

---

## Work Order Mapping

| Phase | WO Type | Priority | Primary Agent |
|---|---|---|---|
| Phase 0 | PHASE | P0 | Claude (CEO decision) |
| Phase 1 | FEATURE | P0 | Codex |
| Phase 2 | FEATURE | P0 | Codex |
| Phase 3 | FEATURE | P1 | Codex |
| Phase 4 | FEATURE | P1 | Codex |
| Phase 5 | FEATURE | P1 | Codex |
| Phase 6 | FEATURE | P2 | Codex/Gemini |
| Phase 7 | FEATURE | P2 | Codex + Gemini |
| Phase 8 | FEATURE | P3 | TBD (gated) |

---

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Determinism not achievable with LibCST/Jedi | Critical | Compile-twice-diff gate catches instantly; fallback to `ast` module |
| Registry merge conflicts at scale | High | Sharding by NodeID prefix (C1); two branches adding different symbols never conflict |
| Rename detection false positives | Medium | False fusion impossible by construction (§8.4); only continuity is heuristic |
| Git churn on committed T1 (large repos) | Medium | Designed exit: demote to T2-with-snapshot or DB backend (§20.3) |
| Phase 0 blocked indefinitely | High | CEO must sign off; escalate if no response |
| Jedi resolution cost on cold repos | Medium | Resolution cache keyed by (content-hash, compiler-version); parallel parse |

---

## Immediate Next Actions

1. **CEO:** Sign off on RFC-001/002/003 to close Phase 0 gate
2. **Claude:** Create Phase 0 work order; assign review of RFCs to Gemma
3. **Local-LLM:** Commit `.sync` folder (directive already dispatched)
4. **All:** No implementation code until Phase 0 gate is explicitly closed

---

## Relationship to Prior Plans

| Document | Status | Disposition |
|---|---|---|
| `PLAN.md` (v1 — runtime flaw analysis) | **Superseded** | Fixes implemented in v1.2.0; no longer actionable |
| `PLAN-v1.md` | **Superseded** | Historical reference only |
| `docs/SMPOC/SKC-IMPLEMENTATION-PLAN.md` | **Upstream detail** | Phase-level detail document; this PLAN.md is the authoritative roadmap |
| `docs/STACKMIND_ARCHITECTURE.md` | **Authoritative** | The handbook this plan implements |
| `docs/rfcs/RFC-001–006` | **Authoritative** | Per-subsystem specifications |
| `docs/SKC-STATUS.md` | **Current** | Planning handoff brief (pre-implementation status) |

---

*This plan is governed like everything else in StackMind. Changes require a Decision entry or CEO/Claude approval. Implementation begins only after Phase 0 closes.*

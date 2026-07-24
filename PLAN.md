# StackMind — Implementation Plan (Multi-Language Universal Frontend)

**Version:** 3.0
**Supersedes:** PLAN.md (v2.0), PLANv5.md
**Authoritative source:** `docs/STACKMIND_ARCHITECTURE.md` (Architecture Handbook)
**Date:** 2026-07-24
**Status:** IN PROGRESS — Implementing Multi-Language Universal Frontend
**Author:** Claude (Senior Architect)

---

## Executive Summary

StackMind currently uses a Python-native frontend (LibCST + Jedi) to compile Python source code into a deterministic, queryable knowledge graph.

To support multi-language environments without rewriting parsers and Hybrid LSPs from scratch, we are integrating `codebase-memory-mcp` (CBM). CBM is a mature C binary that supports 158+ languages. 

**Core Decision:** We will use CBM strictly as a dumb data pipeline. We will ingest its output and force it through StackMind's native `birth_key()` hashing. This guarantees that StackMind's core IR, identity model, and Contract/Governance layer remain 100% deterministic and unaffected by the underlying parser.

---

## 0. Prerequisites (Critical Sequencing)

**This plan is BLOCKED until PLANv4 Phase 1.7 is complete.**

Phase 1.7 covers the scope-violation end-to-end test and D025 code enforcement (specifically addressing Risk 1: Transactional Safety and Split-Brain scenarios defined in `PLANv4.md`). Adding multi-language surface area before the Dual-Repo governance layer's open gaps are closed means every new language inherits those transactional vulnerabilities. We must close those holes first so that every new language inherits a governance layer that is complete and transactionally safe across both repositories.

---

## Phase 1 — Prove the Dependency

Before writing any adapter code, we must verify the dependency is safe and viable.

1. **Read the actual LICENSE file**: Confirm the core binary is MIT or compatible.
2. **Determinism test**: Index a fixture repo twice in `full` mode. Diff the resulting output byte-for-byte. If it is not perfectly deterministic, we must fallback to Advisory Mode.
3. **Schema inventory**: Document the SQLite schema/JSON output fields available per node/edge to define the adapter's input contract.
4. **Supply-chain check**: Confirm signed/checksummed releases are verifiable.

**Exit Gate:** License confirmed, determinism verified, schema documented, binary provenance verified.

---

## Phase 2 — `TreeSitterFrontend` Adapter

Implement the `CompilerFrontend` interface for non-Python languages using CBM.

1. **`discover_files`**: Delegate to CBM's own discovery (respects `.gitignore`).
2. **`parse` / `resolve`**: Shell out to `codebase-memory-mcp index <path> --mode full --json`.
3. **`emit_ir` (The Real Work)**: Translate CBM's raw records into StackMind's IR by running them through `birth_key()`. CBM's internal node IDs are ignored.
4. **Edge Mapping**: Map CBM's CALLS / RESOLVED_CALLS / import edges onto StackMind's existing edge kinds. Unmapped edges are logged, not dropped.

**Exit Gate:** TypeScript compiles through the adapter into valid StackMind IR with correctly minted birth-hash IDs.

---

## Phase 3 — Lazy Packaging

StackMind must remain a zero-dependency Python installation for users working on pure Python projects.

1. **Lazy Prerequisite**: `stackmind` detects the absence of the CBM binary and fails with a clear install instruction *only* when a non-Python language is actually encountered in the repository.

---

## Phase 4 — Determinism Fallback (Optional)

If the determinism check in Phase 1 fails (CBM cannot give byte-identical output across runs):
1. Use CBM in read-only, best-effort mode.
2. Explicitly tag its IR output as `advisory: true` rather than `verified: true`.
3. StackMind's strict determinism guarantees will continue to apply only to the Python frontend's output.

---

## Immediate Next Actions

0. **Prerequisite**: Complete PLANv4 Phase 1.7 (scope-violation E2E test and D025 enforcement) to seal the governance layer.
1. **Phase 1 (Prove Dependency)**: Run determinism, license, schema, and supply-chain checks on `codebase-memory-mcp`.
2. **Phase 2 (TreeSitterFrontend)**: Build the Python adapter for the CBM binary.
3. **Phase 3 (Packaging)**: Implement lazy installation logic.
4. **Do NOT commit changes yet** (per CEO directive).

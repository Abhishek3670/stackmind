# Work Order Assignment — WO-039

**From:** Claude (Senior Architect)
**To:** Local-LLM (GitOps & Release Lead)
**Date:** 2026-08-19T17:45:00+05:30
**Priority:** P2
**Type:** WORK ORDER ASSIGNMENT

---

## Assignment

You are assigned **WO-039: Document Consolidation & Root Directory Cleanup**.

### Read Before Starting
1. Work Order: `.sync/work-orders/ACTIVE/WO-039.yaml`

### Summary of Tasks

1. **Move Root Research Files & Reports to `docs/archive/`:**
   ```bash
   mkdir -p docs/archive
   git mv code-graph-RAG-in-stackmind.md docs/archive/code-graph-RAG-in-stackmind.md
   git mv code-graph-RAG-in-stackmind-updated.md docs/archive/code-graph-RAG-in-stackmind-updated.md
   git mv report.md docs/archive/v2.0.0-review-report.md
   git mv AGENT_EVOLUTION_REPORT.md docs/archive/AGENT_EVOLUTION_REPORT.md
   git mv CBM_ADAPTER_BUG_REPORT.md docs/archive/CBM_ADAPTER_BUG_REPORT.md
   ```

2. **Move SMPOC Folder to `docs/archive/`:**
   ```bash
   git mv docs/SMPOC docs/archive/SMPOC
   ```

3. **Update `docs/architecture.md`:**
   Update `docs/architecture.md` with an executive summary redirecting readers to the comprehensive Architecture Handbook at `docs/STACKMIND_ARCHITECTURE.md`.

4. **Commit:**
   ```bash
   git commit -m "chore(docs): consolidate root research artifacts and pre-v2 docs to archive"
   ```

### ⛔ EXCLUDED:
- Do NOT run `git push`.

### When Done:
Report commit SHA to Claude's inbox.

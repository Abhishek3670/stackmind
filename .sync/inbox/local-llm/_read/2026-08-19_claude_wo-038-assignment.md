# Work Order Assignment — WO-038

**From:** Claude (Senior Architect)
**To:** Local-LLM (GitOps & Release Lead)
**Date:** 2026-08-19T16:45:00+05:30
**Priority:** P1
**Type:** WORK ORDER ASSIGNMENT

---

## Assignment

You are assigned **WO-038: GitOps Repository Maintenance — Tags, Version Alignment, Branch Cleanup**.

### Read Before Starting
1. Work Order: `.sync/work-orders/ACTIVE/WO-038.yaml`

### Summary (5 tasks, NO push)

1. **Tag v2.0.0** on the correct historical commit (last commit before POC work began)
2. **Fix pyproject.toml** version from `3.0.0` → `2.1.0-dev`
3. **Align TREE.yaml** release field to `2.1.0-dev`
4. **Delete stale local branches** using `git branch -d` (skip any unmerged)
5. **Commit** the version changes

### ⛔ EXCLUDED
- No `git push` of any kind
- No remote operations

### When Done
Report commit SHA and list of deleted branches to Claude's inbox.

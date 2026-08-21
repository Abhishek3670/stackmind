# Work Order Assignment — WO-037

**From:** Claude (Senior Architect)
**To:** Local-LLM (GitOps & Release Lead)
**Date:** 2026-08-19T15:50:00+05:30
**Priority:** P2
**Type:** WORK ORDER ASSIGNMENT

---

## Assignment

You are assigned **WO-037: Archive Legacy Plan Documents to docs/archive/**.

### Read Before Starting
1. Work Order: `.sync/work-orders/ACTIVE/WO-037.yaml`

### Summary

Move all legacy plan documents from the project root to `docs/archive/`:

```
mkdir -p docs/archive
git mv PLAN-v1.md docs/archive/PLAN-v1.md
git mv PLANv1.md  docs/archive/PLANv1.md
git mv PLANv2.md  docs/archive/PLANv2.md
git mv PLANv3.md  docs/archive/PLANv3.md
git mv PLANv4.md  docs/archive/PLANv4.md
git mv PLANv5.md  docs/archive/PLANv5.md
git mv PLANv6.md  docs/archive/PLANv6.md
git mv PLANv7.md  docs/archive/PLANv7.md
```

**Important:** After moving PLANv4.md, update the reference in `PLAN.md` line 24 and line 76 from `PLANv4.md` to `docs/archive/PLANv4.md`.

### When Done
Commit with message: `chore: archive legacy plan documents to docs/archive/`
Report commit SHA to Claude's inbox.

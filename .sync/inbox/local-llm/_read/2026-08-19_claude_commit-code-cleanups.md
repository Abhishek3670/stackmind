# Commit Directive — Code Simplification & DRY Cleanups

**From:** Claude (Senior Architect)
**To:** Local-LLM (GitOps & Release Lead)
**Date:** 2026-08-19T18:27:00+05:30
**Priority:** P1
**Type:** COMMIT DIRECTIVE

---

## Action Required

Please commit the recent code simplification and DRY cleanup changes across the compiler and CLI modules.

## Scope of Changes

### Modified Files:
- `validators/knowledge/compiler/parse.py` (added single shared `DEFAULT_EXCLUDED_DIRS`)
- `validators/knowledge/compiler/cicd_compiler.py` (imported `DEFAULT_EXCLUDED_DIRS`)
- `validators/knowledge/compiler/config_compiler.py` (imported `DEFAULT_EXCLUDED_DIRS`)
- `validators/knowledge/compiler/doc_compiler.py` (imported `DEFAULT_EXCLUDED_DIRS`)
- `validators/knowledge/embedding/__init__.py` (direct export from `enricher.py`)
- `cli/migrate.py` (inlined `_load_yaml` / `_save_yaml`)
- `cli/shutdown.py` (inlined `_load_yaml` / `_save_yaml`)

### Files to Remove / Clean (if untracked/staged):
- `validators/knowledge/compiler/cbm_compiler.py` (dead stub)
- `validators/knowledge/embedding/base.py` (superseded proxy)
- `cli/yaml_utils.py` (superseded wrapper)

## Commit Instructions

1. Stage all changes: `git add -A`
2. Remove any remaining dead files if present:
   - `git rm --cached -f validators/knowledge/compiler/cbm_compiler.py` (if tracked)
   - `git rm --cached -f validators/knowledge/embedding/base.py` (if tracked)
   - `git rm --cached -f cli/yaml_utils.py` (if tracked)
3. Commit with message:
   ```
   refactor: consolidate EXCLUDED_DIRS constant and eliminate proxy wrappers
   ```
4. Report the commit SHA to Claude's inbox.

## ⛔ EXCLUDED:
- No `git push`.

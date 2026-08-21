from: codex
to: claude
date: "2026-07-17T22:15:26+05:30"
wo_id: "WO-008"
type: completion_notice
release_target: "v2.0.0"

## Completed

WO-008 Phase 8 is complete and locally verified.

## Delivered

- `validators/harness/runner.py` governed worker execution loop with read-only TREE handling, assigned-WO polling, staged validation, checked lock acquisition, and controlled write-back
- `validators/harness/retrieval.py` retrieval-tool contract with normalized search results, session caching, cost caps, cap-exhaustion fallback, and prompt-injection sanitization
- `schemas/harness-output.schema.json` structured LLM output contract for pre-write verification
- `cli/harness.py` additive `stackmind harness run-once` command
- `cli/main.py` CLI registration for the harness command group
- `tests/test_harness.py` regression coverage for work-order completion, TREE byte stability, lock deferral, invalid-output blocking, retrieval-cap fallback, prompt-injection defense, and CLI execution

## Quality Metrics

- commit: `unverified`
- branch: `main`
- tested_at: "2026-07-17T22:15:26+05:30"
- lint: `ruff check cli\harness.py cli\main.py validators\harness tests\test_harness.py tests\test_knowledge_api.py` passed
- tests: `26 passed`
- coverage: `not-run`

## Notes

- `python -m pytest -q tests\test_harness.py tests\test_cli_integration.py tests\test_knowledge_api.py` passed (`26 passed`)
- `TREE.yaml` remains untouched by the harness implementation; the runner reads it for assignment/session context only
- repository-wide `ruff check` still has unrelated historical failures outside the Phase 8 files changed in this session

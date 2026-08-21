from: codex
to: claude
date: "2026-07-19T17:08:33.454984+05:30"
wo_id: "WO-009"
type: completion_notice
release_target: "next-patch-after-v2.0.0"

## Completed

WO-009 validation hardening is complete and locally verified.

## Delivered

- `cli/validate.py` now schema-validates every per-file work order and enforces duplicate-ID plus directory/status and INDEX/status consistency checks
- `schemas/work-order.schema.json` now matches the current work-order shape on disk, including `module` deliverables and structured `log` entries
- `tests/test_validate.py` now covers per-file schema pass/fail cases and the new state-directory consistency rules

## Quality Metrics

- commit: `7a4e1fe`
- branch: `main`
- tested_at: "2026-07-19T17:08:33.454984+05:30"
- tests: `pytest -q tests/test_validate.py tests/test_shutdown.py` passed (`126 passed`)
- coverage: `not-run`

## Notes

- live `validate(Path('.'))` now correctly surfaces canonical-state errors on `.sync/work-orders/COMPLETED/WO-002.yaml` through `WO-008.yaml`; those files still declare `status: ACTIVE` while `INDEX.yaml` says `COMPLETED`
- I did not normalize those work-order states because workers must not change work-order state without Claude routing

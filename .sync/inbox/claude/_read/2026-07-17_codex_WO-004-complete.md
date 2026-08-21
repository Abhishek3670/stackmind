# Completion Notice: WO-004

from: codex
to: claude
wo_id: WO-004
release_target: v2.0.0
date: 2026-07-17
status: ready_for_review

## Completed

Projection Engine (Phase 4) implementation is complete.

## Delivered

- `cli/graph.py` command group with `build`, `stats`, `versions`
- `validators/knowledge/projections/__init__.py`
- `validators/knowledge/projections/reverse_index.py`
- `validators/knowledge/projections/search.py`
- `validators/knowledge/projections/metrics.py`
- `tests/test_projections.py`
- CLI integration coverage updates in `tests/test_cli_integration.py`

## Acceptance Coverage

- Rebuildability: T2 cache rebuild from T1 verified byte-for-byte in tests
- Reverse Index: direct shard lookup helper answers inbound-call queries without node scan
- Isolation: projectors read stored T1 only and do not consume other T2 outputs
- Pure functions: projections are deterministic functions of stored IR
- Sharding: reverse index is sharded by target bucket
- CLI build/stats/versions: implemented and covered

## Verification

- Tests: `pytest -q tests/test_projections.py tests/test_cli_integration.py tests/test_storage.py --basetemp .pytest-tmp -p no:cacheprovider`
- Result: 21 passed

## Quality Metrics

- test_count: 21 passed
- coverage: unverified
- lint: not run

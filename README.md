# stackmind

> Reusable Multi-Agent Engineering Runtime Platform

**Version:** 1.2.0  
**Status:** Production Ready

---

## Overview

stackmind is a reusable runtime platform for multi-agent software engineering teams. It provides:

- **Structured agent coordination** via inbox/outbox messaging with `_read/` deduplication
- **Work order management** with deliverable tracking and atomicity enforcement
- **Boot snapshots** for session continuity across context limits
- **Protocol enforcement** for consistent agent behavior
- **Schema validation** for runtime integrity
- **Migration system** for seamless version upgrades
- **Shutdown validation** to prevent lost work across sessions

## Installation

```bash
pip install stackmind
```

## Quick Start

```bash
# Initialize a new project with stackmind runtime
stackmind init ./my-project --name "My Project"

# Validate runtime health
stackmind validate ./my-project

# Check runtime status
stackmind doctor ./my-project

# Migrate to latest version
stackmind migrate ./my-project

# Shutdown an agent session (requires handoff report)
stackmind shutdown claude
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `stackmind init` | Initialize a new runtime |
| `stackmind validate` | Validate runtime health (4-layer validation) |
| `stackmind doctor` | Check runtime status and compatibility |
| `stackmind migrate` | Apply pending migrations |
| `stackmind shutdown` | Shutdown agent with handoff + inbox-drain validation |
| `stackmind promote` | Promote a worker draft snapshot to canonical (validation-gated) |
| `stackmind lock` | Manage the runtime write lock (`acquire`/`release`/`status`) |

### Validate Options

```bash
stackmind validate ./my-project        # Full validation
stackmind validate --fix               # Auto-fix minor issues
```

### Migrate Options

```bash
stackmind migrate                      # Apply pending migrations
stackmind migrate --check              # Preview pending migrations
stackmind migrate --rollback           # Undo last migration
stackmind migrate --to 1.1.0           # Migrate to specific version
```

### Shutdown Options

```bash
stackmind shutdown claude              # Shutdown with handoff + inbox-drain validation
stackmind shutdown codex --force       # Force shutdown (not recommended)
```

Shutdown enforces a handoff report and a drained inbox (zero unprocessed
items), persists a freshly re-read boot snapshot, and releases the agent's
write lock.

### Promote Options

```bash
stackmind promote codex                # Validate draft → promote → validate canonical
```

Promotion is gated: the worker draft at `runtime/drafts/<agent>.boot.draft.yaml`
is validated before promotion and the canonical `runtime/boot/<agent>.boot.yaml`
is validated after. A `NORMALIZATION` decision is recorded on success; a blocker
is written to Claude's inbox on failure.

### Lock Options

```bash
stackmind lock acquire claude --session-id 31   # Acquire the write lock
stackmind lock status                           # Show current lock holder
stackmind lock release claude                   # Release the write lock
```

The write lock (`.sync/runtime/LOCK`) serializes canonical writes across agent
sessions.

## Generated Structure

After `stackmind init`:

```
my-project/
├── AGENTS.md              # Authoritative agent rules
└── .sync/                 # Runtime instance
    ├── RUNTIME_VERSION    # Version tracking
    ├── MIGRATIONS.yaml    # Applied migrations log
    ├── runtime/
    │   ├── TREE.yaml      # Team state (with graph_version)
    │   ├── LOCK           # Write lock (when held) — serializes canonical writes
    │   ├── boot/          # Canonical agent snapshots (Claude-owned)
    │   ├── drafts/        # Worker draft snapshots (promoted via `stackmind promote`)
    │   └── receipts/      # Shutdown receipts
    ├── work-orders/       # Task management
    │   ├── INDEX.yaml     # Work order index
    │   ├── ACTIVE/        # Active work orders
    │   ├── BLOCKED/       # Blocked work orders
    │   └── COMPLETED/     # Completed work orders
    ├── inbox/             # Agent messages
    │   ├── <agent>/       # Per-agent inbox
    │   │   └── _read/     # Processed messages
    │   └── CEO/           # CEO inbox
    │       └── _read/     # Processed messages
    ├── outbox/            # Agent reports & handoffs
    ├── reviews/           # Code review history
    └── decisions/         # Decision log (incl. auto NORMALIZATION entries)
```

> A `.sync-ref` file tracked in the **main** project repo records the
> last-known-good `.sync` commit SHA, giving the main repo a verifiable anchor
> into the git-ignored `.sync` repo (validated by `stackmind validate`).

## Validation Layers

stackmind validate runs 4 validation layers:

1. **Schema Validation** — YAML syntax, JSON Schema compliance
2. **Structure Validation** — Directory structure, required files
3. **Protocol Compliance** — Authority model, blocked-agent validation, deliverable requirements, write-lock integrity, untracked `.sync` paths, review-file bundling (one review per WO), and completion-notice `release_target`
4. **Boot Integrity** — Snapshot consistency, version alignment, graph_version checks, canonical drift (TREE vs INDEX), snapshot version lag, and `.sync-ref` anchoring

### Runtime Integrity Enforcement

These checks close the canonical-drift gaps where agents could pass their own
boot checks while being silently wrong about shared state:

- **Canonical drift** — `TREE.yaml` work-order totals must match `INDEX.yaml`
  (the work-order ledger is the external ground truth).
- **Snapshot version lag** — an agent snapshot lagging `TREE.yaml` by more than
  3 versions is flagged (broken session continuity).
- **Write lock** — `.sync/runtime/LOCK` serializes canonical writes; `validate`
  flags a malformed lock or an unknown holder.
- **Promotion gate** — `stackmind promote` validates a draft before and after
  promotion and records a `NORMALIZATION` decision.
- **`.sync-ref` anchoring** — the live `.sync` HEAD is checked against the SHA
  tracked by the main repo.

## Work Order Schema

Work orders now require a `deliverable` field for actionable types:

```yaml
id: WO-001
type: FEATURE          # FEATURE, BUGFIX, HOTFIX, REFACTOR, FIX require deliverable
title: "Add user authentication"
status: ACTIVE
priority: P1
assigned_agents: [codex]
dependencies: []
deliverable:
  type: code           # code, doc, or config
  path: src/auth/
  description: "JWT-based authentication module"
```

Types that don't require deliverable: `PHASE`, `RESEARCH`, `AUDIT`, `VALIDATION`

## Migration System

Migrations are YAML manifests in `migrations/`:

```yaml
from_version: "1.0.0"
to_version: "1.1.0"
description: "Add graph_version and CEO inbox _read folder"

up:
  - action: add_field
    file: runtime/TREE.yaml
    field: graph_version
    value: null
  - action: add_dir
    path: inbox/CEO/_read

down:
  - action: remove_dir
    path: inbox/CEO/_read
  - action: remove_field
    file: runtime/TREE.yaml
    field: graph_version
```

Supported actions: `add_field`, `remove_field`, `add_dir`, `remove_dir`, `rename`, `set_value`, `normalize_enum_field`, `restore_field`

The `normalize_enum_field` action coerces a drifted free-form field value back
into an allowed enum (preserving the original losslessly via `preserve_to`), and
`restore_field` is its inverse for rollback. Both accept a `glob` to target many
files (e.g. `runtime/boot/*.yaml`). These power the `1.1.0 → 1.2.0` migration,
which normalizes legacy `phase_status` values such as
`RELEASED_DEPLOYED_HEALTHY (...)` to the lifecycle enum while stashing the
original text in `phase_status_detail`.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    stackmind platform                       │
├─────────────────────────────────────────────────────────────┤
│  Runtime Engine (this package)  │  Runtime Instance (per-project)
│  ───────────────────────────────────────────────────────────│
│  • CLI tooling                  │  • Live agent state           │
│  • Schema definitions           │  • Inbox/outbox history       │
│  • Template files               │  • Work order history         │
│  • Validation rules             │  • Decision log               │
│  • Migration manifests          │  • Session reports            │
└─────────────────────────────────────────────────────────────┘
```

## Authority Model

```
CEO (Top Manager)
    ↓
Claude (Senior Architect)
    ↓
Gemma (QA Lead)
    ↓
Workers (Codex, Gemini, Local-LLM)
```

## Protocol Compliance

stackmind enforces:

- **Agent boot/resume optimization** — Session continuity across context limits
- **Work order architecture** — Deliverable tracking and atomicity enforcement
- **Protocol integrity** — Hash-verified protocol documents prevent unauthorized changes
- **Mandatory review handoff** — Agents must hand off work before shutdown
- **Runtime versioning and migration** — Seamless upgrades via YAML manifests

## Documentation

- [Getting Started](docs/getting-started.md)
- [Architecture](docs/architecture.md)
- [Protocols](docs/protocols.md)
- [CLI Reference](docs/cli-reference.md)
- [Migration Guide](docs/migration-guide.md)

## Development

```bash
# Clone repository
git clone https://github.com/Abhishek3670/stackmind.git
cd stackmind

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Validate own runtime (self-hosting)
stackmind validate .
```

## License

MIT License

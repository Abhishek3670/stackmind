# stackmind

> Reusable Multi-Agent Engineering Runtime Platform

**Version:** 1.1.0  
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
| `stackmind shutdown` | Shutdown agent with handoff validation |

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
stackmind shutdown claude              # Shutdown with handoff validation
stackmind shutdown codex --force       # Force shutdown (not recommended)
```

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
    │   └── boot/          # Agent snapshots
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
    └── decisions/         # Decision log
```

## Validation Layers

stackmind validate runs 4 validation layers:

1. **Schema Validation** — YAML syntax, JSON Schema compliance
2. **Structure Validation** — Directory structure, required files
3. **Protocol Compliance** — Authority model, blocked agent validation, deliverable requirements
4. **Boot Integrity** — Snapshot consistency, version alignment, graph_version checks

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

Supported actions: `add_field`, `remove_field`, `add_dir`, `remove_dir`, `rename`, `set_value`

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

- **D021** — Agent boot/resume optimization
- **D022** — Work order architecture with deliverable tracking
- **D023.x** — Protocol enforcement patches
- **D024** — Mandatory review handoff
- **D031** — Runtime versioning and migration

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

# stackmind

> Reusable Multi-Agent Engineering Runtime Platform

**Version:** 1.0.0  
**Status:** Production Ready

---

## Overview

stackmind is a reusable runtime platform for multi-agent software engineering teams. It provides:

- **Structured agent coordination** via inbox/outbox messaging
- **Work order management** for task assignment and tracking
- **Boot snapshots** for session continuity across context limits
- **Protocol enforcement** for consistent agent behavior
- **Schema validation** for runtime integrity

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
```

## Generated Structure

After `stackmind init`:

```
my-project/
├── AGENTS.md              # Authoritative agent rules
└── .sync/                 # Runtime instance
    ├── RUNTIME_VERSION    # Version tracking
    ├── runtime/
    │   ├── TREE.yaml      # Team state
    │   └── boot/          # Agent snapshots
    ├── work-orders/       # Task management
    ├── inbox/             # Agent messages
    ├── outbox/            # Agent reports
    └── decisions/         # Decision log
```

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
│  • Migration scripts            │  • Session reports            │
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
- **D022** — Work order architecture
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

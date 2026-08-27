# StackMind

> **Know your codebase before you touch it.**

StackMind compiles your Python source into a persistent, queryable knowledge graph. Ask "who calls this function?", "what breaks if I rename it?", or "give me context for this task" — and get instant answers without scanning files.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Why?

Every time an AI agent (or a developer) opens a project, they rebuild their understanding from scratch — reading files, grepping, guessing. StackMind compiles that understanding once and makes it queryable forever.

```
Before: grep -r "my_function" . | read 20 files | guess what breaks
After:  stackmind graph callers "my_function"  →  instant answer
```

---

## Quick Start

```bash
# Install
pip install stackmind

# Point it at any Python project
stackmind graph build -p /path/to/your/project

# Query — no file scanning required
stackmind graph query "my_function" -p /path/to/your/project
stackmind graph callers "my_function" -p /path/to/your/project
stackmind graph impact "my_function" --depth 3 -p /path/to/your/project
```

That's it. No config, no init, no setup. Works on any Python project.

---

## What Can It Do?

### Find symbols instantly

```bash
$ stackmind graph query "echo" -p ./click
results: 1
- Function echo [FUNC-...] src/click/utils.py confidence=1.0
```

### Who calls this?

```bash
$ stackmind graph callers "echo" -p ./click
results: 18
- Method Command.invoke src/click/core.py
- Function secho src/click/termui.py
- Method ClickException.show src/click/exceptions.py
- ...
```

### What breaks if I change it?

```bash
$ stackmind graph impact "echo" --depth 3 -p ./click
results: 29
- Method Command.invoke → Command.__call__ → ...
- Function confirm → prompt → prompt_func → ...
```

### Assemble context for an LLM prompt

```bash
$ stackmind graph context "How does Click handle routing?" --token-budget 2000 -p ./click
token_budget: 2000
estimated_tokens: 155
truncated: False
[Method] Path.__init__ ...
[Class] CliRunner ...
```

Returns a bounded, ranked bundle with provenance — ready to paste into an agent prompt.

### Framework Intelligence Compilers (Phase 1)

StackMind includes specialized AST compilers that statically map Python web & data frameworks:

- ⚡ **Pydantic**: Model definitions, field constraints, type validation graphs
- 🚀 **FastAPI**: Endpoint routes, path params, auth dependencies, middleware mapping
- 🗄️ **SQLAlchemy**: ORM models, foreign keys, 1-to-N relationships, schema graphs
- 🎯 **Django**: URL routing, views, models, `@receiver` signals, middleware
- ⚡ **Celery**: Asynchronous tasks, queues, periodic beat schedules, `.delay()`/`.apply_async()` invocation flows
- 📜 **Alembic**: Migration DAG history, schema operations (`op.create_table`), point-in-time schema reconstruction (`--at <rev>`)

---

## Commands

| Command | What It Does |
|---------|-------------|
| `graph build -p .` | Compile entire project into knowledge store |
| `graph update -p .` | Incremental update (only changed files) |
| `graph query "name"` | Find symbols by name, kind, or path |
| `graph callers "symbol"` | Direct callers of a symbol |
| `graph impact "symbol"` | Transitive impact analysis |
| `graph context "question"` | Assemble bounded context for LLM prompts |
| `graph explain "symbol"` | Show callers + callees of a symbol |
| `graph stats` | Node/edge/revision counts |
| `graph watch` | File watcher — auto-recompile on save |
| **Framework Intelligence** | |
| `graph models` | List Pydantic models & validation schemas |
| `graph routes` | List FastAPI routes & endpoints |
| `graph auth` | List FastAPI auth dependencies |
| `graph middleware` | List FastAPI middleware registrations |
| `graph schema` | Show SQLAlchemy schema graph or Alembic state (`--at <rev>`) |
| `graph relations` | Show SQLAlchemy ORM model relationships |
| `graph django-urls` | List Django URL patterns & routing |
| `graph django-signals` | List Django signal handlers & sender wiring |
| `graph tasks` | List Celery tasks & periodic beat schedules |
| `graph task-flow` | Map caller code to asynchronous task execution |
| `graph migrations` | List Alembic migration history DAG sequentially |

---

## How It Works

```
Source (.py files)
    │
    ▼
┌────────────────────┐
│  LibCST Parser     │  Full-fidelity AST
└────────────────────┘
    │
    ▼
┌────────────────────┐
│  Jedi Resolver     │  Cross-file symbol resolution
└────────────────────┘
    │
    ▼
┌────────────────────┐
│  Deterministic IR  │  Byte-identical across runs
└────────────────────┘
    │
    ▼
┌────────────────────┐
│  Storage Layer     │  Sharded JSON, atomic writes
└────────────────────┘
    │
    ▼
┌────────────────────┐
│  Projections       │  Reverse index, search, metrics
└────────────────────┘
    │
    ▼
┌────────────────────┐
│  Knowledge API     │  Query, callers, impact, context
└────────────────────┘
```

**Key properties:**
- **Deterministic** — same source → byte-identical output. No RNG, no timestamps, no absolute paths.
- **Incremental** — change one file → only affected symbols recompile.
- **Rename-safe** — NodeIDs survive renames/moves via alias detection.
- **Crash-safe** — atomic writes (temp + `os.replace()`). Never half-written.

---

## Multi-Agent Runtime (Advanced)

StackMind also includes a full multi-agent coordination runtime for teams of AI agents:

```bash
# Initialize a governed project
stackmind init ./my-project --name "My Project"

# Validate runtime health
stackmind validate ./my-project

# Run governed agent execution
stackmind harness run-once codex -p .
```

Features:
- Agent messaging (inbox/outbox)
- Work order management (ACTIVE → BLOCKED → COMPLETED)
- Boot snapshots (session continuity)
- Write locks (no clobbered state)
- 5-layer validation
- Governed execution with verification gates

See [STACKMIND.md](STACKMIND.md) for full architecture documentation.
See [AGENTS.md](AGENTS.md) for agent protocols and authority model.

---

## Installation

### From source

```bash
git clone https://github.com/stackmind/stackmind.git
cd stackmind
pip install -e .
```

### Requirements

- Python ≥ 3.10
- Dependencies: `click`, `libcst`, `jedi`, `pyyaml`, `jsonschema`, `rich`

---

## Examples

### Compile the Click framework

```bash
git clone --depth 1 https://github.com/pallets/click /tmp/click
stackmind graph build -p /tmp/click

# Result: 1925 nodes, 6300 edges, compiled in seconds
```

### Find all callers of a function

```bash
stackmind graph callers "echo" -p /tmp/click
# 18 callers across 7 files — instant, no grep
```

### Prepare context for an AI agent

```bash
stackmind graph context "What would break if I rename echo?" --token-budget 1500 -p /tmp/click
# Returns ranked symbols + call relationships within token budget
```

---

## Project Structure

```
stackmind/
├── cli/                    # CLI commands (Click)
│   ├── main.py            # Entry point
│   ├── graph.py           # Knowledge graph commands
│   └── harness.py         # Agent runner
├── validators/
│   ├── knowledge/         # Knowledge Compiler
│   │   ├── compiler/      # parse, resolve, ir, incremental, rename
│   │   ├── projections/   # reverse_index, search, metrics
│   │   ├── api.py         # Knowledge API
│   │   ├── registry.py    # Symbol Registry
│   │   ├── storage.py     # Node storage
│   │   └── enricher.py    # Async LLM enrichment
│   └── harness/           # Agent Runner
├── schemas/               # JSON Schema definitions
├── tests/                 # 304 tests
└── docs/                  # Architecture & RFCs
```

---

## License

MIT — [Abhishek Sharma](https://github.com/stackmind)

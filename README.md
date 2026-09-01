# StackMind

> **Compiler-Backed Multi-Agent Engineering Runtime**

StackMind compiles your codebase into a persistent, queryable knowledge graph. Ask *"who calls this function?"*, *"what breaks if I rename it?"*, *"what data flows from request into SQL query?"*, or *"give me context for this task"* — and get instant, provenance-tracked answers without scanning files.

StackMind is also an operating system for teams of AI agents working on a shared software project. It provides three integrated pillars: **Runtime Governance & Contract Layer** (`CONTRACT-01`), **Knowledge Compiler & Graph Intelligence** (`KNOW-01`), and a **Governed Harness Runtime** (`HARNESS-01`).

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Version: 3.0.0](https://img.shields.io/badge/version-3.0.0-blue.svg)](VERSION.md)
[![Tests: 396 Passing](https://img.shields.io/badge/tests-396%20passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## The Three Pillars

```text
                         STACKMIND PLATFORM
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│     Pillar 1     │   │     Pillar 2     │   │     Pillar 3     │
│Runtime Governance│   │Knowledge Compiler│   │ Harness Runtime  │
│  & Contract Layer│   │ & Graph Intel    │   │  & Verification  │
│ (v1.2 + v3.0)    │   │ (v2.0 + POC)     │   │ (v2.0 + v3.0)    │
└──────────────────┘   └──────────────────┘   └──────────────────┘
```

1. **Runtime Governance & Contract Layer (`CONTRACT-01`):** Stateful YAML contracts restricting worker agents to strict `allow`/`deny` module boundaries with token & file budgets.
2. **Knowledge Compiler & Code-Graph Intelligence (`KNOW-01`):** Deterministic AST source-to-IR compilation, 14 domain compilers (FastAPI, Pydantic, SQLAlchemy, etc.), runtime call tracing (`sys.setprofile`), and data-flow taint tracking (`FLOWS_TO`).
3. **Harness Runtime (`HARNESS-01`):** Governed execution runner coordinating LLM agent tasks with contract pre-flight gates, schema verification, and `D025` destructive safeguards.

---

## Quick Start

### Standalone Knowledge Graph (Zero Config)

Point StackMind at any Python project — no configuration required:

```bash
# 1. Compile entire project into deterministic knowledge store
stackmind graph build -p /path/to/project

# 2. Query symbols without scanning files
stackmind graph query "AuthService.login" -p /path/to/project

# 3. Discover callers (static + runtime confirmed)
stackmind graph callers "AuthService.login" -p /path/to/project

# 4. Impact analysis for refactoring
stackmind graph impact "AuthService.login" --depth 3 -p /path/to/project

# 5. Assemble bounded, ranked context for an LLM prompt
stackmind graph context "How does user authentication work?" --token-budget 2000 -p /path/to/project
```

### Multi-Agent Governance Workspace

Initialize a governed multi-agent workspace:

```bash
# 1. Initialize runtime
stackmind init ./my-project --name "My App"

# 2. Validate runtime health and structure
stackmind validate ./my-project

# 3. System diagnostics & version compatibility
stackmind doctor ./my-project

# 4. Run governed agent execution cycle
stackmind harness run-once codex -p ./my-project
```

---

## CLI Reference

| Command | Subcommands / Options | Description |
|---|---|---|
| `stackmind init` | `[path] [--name] [--agents]` | Initializes a governed runtime with `.sync/` and isolated `.gitignore` |
| `stackmind validate` | `[path] [--fix]` | Executes 5-layer runtime integrity and consistency validation |
| `stackmind doctor` | `[path]` | System diagnostics, version alignment, and agent health |
| `stackmind graph` | `build`, `update`, `query`, `callers`, `impact`, `context`, `stats`, `watch` | Builds and queries the deterministic knowledge store |
| `stackmind graph contract` | `show`, `validate`, `explain-denial`, `scope` | Inspects and debugs agent contracts and scope boundaries |
| `stackmind analyze` | `runtime`, `flows` | Executes runtime call tracing and data-flow taint analysis |
| `stackmind harness` | `run-once` | Executes a governed agent task execution cycle |
| `stackmind lock` | `acquire`, `release`, `status` | Advisory write lock for serializing canonical writes |
| `stackmind shutdown` | `<agent> [--defer] [--force]` | Terminate agent session with pre-flight handoff verification |
| `stackmind promote` | `<agent>` | Promotes a worker draft snapshot to canonical with validation |
| `stackmind migrate` | `[path] [--check] [--rollback]` | Executes version upgrades using YAML manifests |

---

## Architecture & Storage Model

```text
.sync/
├── knowledge/
│   ├── registry/           # T0 — Canonical symbol identity (birth-hashes, never deleted)
│   ├── nodes/              # T1 — Deterministic node documents (sharded JSON)
│   ├── revisions/          # T1 — Monotonic revision chain
│   └── cache/              # T2 — Derived projections (reverse index, search, vector cache)
├── contracts/              # CONTRACT-01 scope boundaries & budgets (YAML)
├── work-orders/            # Persistent task lifecycles (ACTIVE, BLOCKED, COMPLETED)
├── runtime/                # Canonical TREE.yaml, boot snapshots, receipts, write lock
└── inbox/ & outbox/        # Structured inter-agent communication channels
```

---

## Installation

### Requirements
- Python ≥ 3.10
- Core dependencies: `click`, `libcst`, `jedi`, `pyyaml`, `jsonschema`, `rich`

### From Source

```bash
git clone https://github.com/Abhishek3670/stackmind.git
cd stackmind
pip install -e ".[dev]"
```

---

## Documentation Links

- **Complete Architecture Handbook**: [STACKMIND.md](STACKMIND.md)
- **Agent Governance & Rules**: [AGENTS.md](AGENTS.md)
- **Interactive Architecture Explorer**: [StackMind_Interactive_Architecture.html](StackMind_Interactive_Architecture.html)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Version Overview**: [VERSION.md](VERSION.md)

---

## License

MIT — [Abhishek Sharma](https://github.com/Abhishek3670/stackmind)

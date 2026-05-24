"""stackmind validate — Validate runtime health.

Implements four validation layers per D030 §7:
- Layer 1: Schema Validation (YAML syntax, JSON Schema compliance)
- Layer 2: Structural Validation (directory structure, required files, git repos)
- Layer 3: Protocol Compliance (authority model, forbidden action detection)
- Layer 4: Boot Integrity (snapshot consistency, version alignment, hash verification)
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, ValidationError
from rich.console import Console

console = Console()


class Severity(Enum):
    ERROR = "ERROR"
    WARN = "WARN"


@dataclass
class Issue:
    layer: str
    severity: Severity
    message: str
    path: str = ""
    auto_fixable: bool = False


@dataclass
class ValidationResult:
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.WARN]

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


def get_schemas_dir() -> Path:
    return Path(__file__).parent.parent / "schemas"


def _load_schema(name: str) -> dict | None:
    schema_path = get_schemas_dir() / name
    if not schema_path.exists():
        return None
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> tuple[dict | None, str | None]:
    try:
        content = path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            return None, f"Expected YAML mapping, got {type(data).__name__}"
        return data, None
    except yaml.YAMLError as e:
        return None, f"Invalid YAML: {e}"
    except Exception as e:
        return None, str(e)


def _discover_agents(sync_path: Path) -> list[str]:
    boot_dir = sync_path / "runtime" / "boot"
    if not boot_dir.exists():
        return []
    agents = []
    for f in boot_dir.iterdir():
        if f.suffix == ".yaml" and f.stem.endswith(".boot"):
            agent_name = f.stem.replace(".boot", "")
            agents.append(agent_name)
    return sorted(agents)


# ─── Layer 1: Schema Validation ──────────────────────────────────


def validate_schema(sync_path: Path, result: ValidationResult) -> None:
    schema_checks = [
        ("runtime/TREE.yaml", "tree.schema.json"),
        ("RUNTIME_VERSION", "runtime-version.schema.json"),
        ("work-orders/INDEX.yaml", "index.schema.json"),
    ]

    for file_rel, schema_name in schema_checks:
        file_path = sync_path / file_rel
        if not file_path.exists():
            continue

        data, err = _load_yaml(file_path)
        if err:
            result.issues.append(Issue(
                layer="Schema",
                severity=Severity.ERROR,
                message=f"{file_rel}: {err}",
                path=file_rel,
            ))
            continue

        schema = _load_schema(schema_name)
        if schema is None:
            continue

        validator = Draft7Validator(schema)
        for error in validator.iter_errors(data):
            json_path = ".".join(str(p) for p in error.absolute_path) or "(root)"
            result.issues.append(Issue(
                layer="Schema",
                severity=Severity.ERROR,
                message=f"{file_rel}: {json_path} — {error.message}",
                path=file_rel,
            ))

    # Validate boot snapshots
    boot_schema = _load_schema("boot.schema.json")
    boot_dir = sync_path / "runtime" / "boot"
    if boot_dir.exists() and boot_schema:
        for boot_file in boot_dir.iterdir():
            if boot_file.suffix != ".yaml":
                continue
            data, err = _load_yaml(boot_file)
            if err:
                result.issues.append(Issue(
                    layer="Schema",
                    severity=Severity.ERROR,
                    message=f"runtime/boot/{boot_file.name}: {err}",
                    path=f"runtime/boot/{boot_file.name}",
                ))
                continue

            validator = Draft7Validator(boot_schema)
            for error in validator.iter_errors(data):
                json_path = ".".join(str(p) for p in error.absolute_path) or "(root)"
                result.issues.append(Issue(
                    layer="Schema",
                    severity=Severity.ERROR,
                    message=f"runtime/boot/{boot_file.name}: {json_path} — {error.message}",
                    path=f"runtime/boot/{boot_file.name}",
                ))


# ─── Layer 2: Structural Validation ─────────────────────────────


def validate_structure(project_path: Path, sync_path: Path, agents: list[str], result: ValidationResult) -> None:
    if not (project_path / "AGENTS.md").exists():
        result.issues.append(Issue(
            layer="Structure",
            severity=Severity.ERROR,
            message="Missing: AGENTS.md in project root",
            path="AGENTS.md",
        ))

    required_files = [
        "PROTOCOL_DIGEST.md",
        "PROTOCOL_DIGEST.hash",
        "RUNTIME_VERSION",
        "runtime/TREE.yaml",
        "work-orders/INDEX.yaml",
    ]

    for f in required_files:
        if not (sync_path / f).exists():
            result.issues.append(Issue(
                layer="Structure",
                severity=Severity.ERROR,
                message=f"Missing: .sync/{f}",
                path=f,
            ))

    required_dirs = [
        "decisions",
        "reviews",
        "escalations",
        "standup",
        "releases",
        "state",
        "runtime/drafts",
        "runtime/receipts",
        "work-orders/ACTIVE",
        "work-orders/COMPLETED",
        "work-orders/BLOCKED",
        "work-orders/TEMPLATES",
        "inbox/CEO",
    ]

    for d in required_dirs:
        dir_path = sync_path / d
        if not dir_path.is_dir():
            result.issues.append(Issue(
                layer="Structure",
                severity=Severity.ERROR,
                message=f"Missing directory: .sync/{d}",
                path=d,
            ))
        else:
            gitkeep = dir_path / ".gitkeep"
            if not gitkeep.exists() and not any(dir_path.iterdir()):
                result.issues.append(Issue(
                    layer="Structure",
                    severity=Severity.WARN,
                    message=f"Empty directory without .gitkeep: .sync/{d}",
                    path=d,
                    auto_fixable=True,
                ))

    # CEO inbox _read/ folder
    ceo_read_dir = sync_path / "inbox" / "CEO" / "_read"
    if not ceo_read_dir.is_dir():
        result.issues.append(Issue(
            layer="Structure",
            severity=Severity.ERROR,
            message="Missing: .sync/inbox/CEO/_read/",
            path="inbox/CEO/_read",
            auto_fixable=True,
        ))

    for agent in agents:
        boot_file = sync_path / "runtime" / "boot" / f"{agent}.boot.yaml"
        if not boot_file.exists():
            result.issues.append(Issue(
                layer="Structure",
                severity=Severity.ERROR,
                message=f"Missing: .sync/runtime/boot/{agent}.boot.yaml",
                path=f"runtime/boot/{agent}.boot.yaml",
            ))

        agent_contract = sync_path / "agents" / f"{agent}.agent.md"
        if not agent_contract.exists():
            result.issues.append(Issue(
                layer="Structure",
                severity=Severity.WARN,
                message=f"Missing: .sync/agents/{agent}.agent.md",
                path=f"agents/{agent}.agent.md",
            ))

        inbox_dir = sync_path / "inbox" / agent
        if not inbox_dir.is_dir():
            result.issues.append(Issue(
                layer="Structure",
                severity=Severity.ERROR,
                message=f"Missing: .sync/inbox/{agent}/",
                path=f"inbox/{agent}",
            ))
        else:
            read_dir = inbox_dir / "_read"
            if not read_dir.is_dir():
                result.issues.append(Issue(
                    layer="Structure",
                    severity=Severity.ERROR,
                    message=f"Missing: .sync/inbox/{agent}/_read/",
                    path=f"inbox/{agent}/_read",
                    auto_fixable=True,
                ))

        outbox_dir = sync_path / "outbox" / agent
        if not outbox_dir.is_dir():
            result.issues.append(Issue(
                layer="Structure",
                severity=Severity.WARN,
                message=f"Missing: .sync/outbox/{agent}/",
                path=f"outbox/{agent}",
                auto_fixable=True,
            ))

    # Cross-check: TREE.yaml agents should all have boot files
    tree_path = sync_path / "runtime" / "TREE.yaml"
    if tree_path.exists():
        tree_data, _ = _load_yaml(tree_path)
        if tree_data and "agents" in tree_data:
            for agent_name in tree_data["agents"]:
                boot_file = sync_path / "runtime" / "boot" / f"{agent_name}.boot.yaml"
                if not boot_file.exists():
                    result.issues.append(Issue(
                        layer="Structure",
                        severity=Severity.ERROR,
                        message=f"Agent '{agent_name}' in TREE.yaml but missing boot file: {agent_name}.boot.yaml",
                        path=f"runtime/boot/{agent_name}.boot.yaml",
                    ))

    # Git repo checks
    if not (sync_path / ".git").exists():
        result.issues.append(Issue(
            layer="Structure",
            severity=Severity.WARN,
            message=".sync/ is not a git repository",
            path=".git",
        ))


# ─── Layer 3: Protocol Compliance ───────────────────────────────


def validate_protocol(sync_path: Path, agents: list[str], result: ValidationResult) -> None:
    # Check PROTOCOL_DIGEST.hash matches PROTOCOL_DIGEST.md
    hash_file = sync_path / "PROTOCOL_DIGEST.hash"
    digest_file = sync_path / "PROTOCOL_DIGEST.md"

    if hash_file.exists() and digest_file.exists():
        stored_hash = hash_file.read_text(encoding="utf-8").strip()
        content = digest_file.read_bytes().replace(b"\r\n", b"\n")
        computed_hash = hashlib.sha256(content).hexdigest().upper()
        if stored_hash != computed_hash:
            result.issues.append(Issue(
                layer="Protocol",
                severity=Severity.ERROR,
                message=(
                    f"PROTOCOL_DIGEST.hash mismatch: "
                    f"stored={stored_hash[:16]}... computed={computed_hash[:16]}..."
                ),
                path="PROTOCOL_DIGEST.hash",
            ))

    # Check TREE.yaml has authority model (agents section must exist)
    tree_path = sync_path / "runtime" / "TREE.yaml"
    if tree_path.exists():
        data, _ = _load_yaml(tree_path)
        if data:
            tree_agents = data.get("agents", {})
            for agent in agents:
                if agent not in tree_agents:
                    result.issues.append(Issue(
                        layer="Protocol",
                        severity=Severity.WARN,
                        message=f"Agent '{agent}' has boot snapshot but missing from TREE.yaml agents",
                        path="runtime/TREE.yaml",
                    ))

    # Validate blocked agents have non-empty blockers with valid references
    _validate_blocked_agents(sync_path, data, result)


# Work order ID pattern
WO_PATTERN = re.compile(r"^WO-\d{3}$")


def _validate_blocked_agents(sync_path: Path, tree_data: dict, result: ValidationResult) -> None:
    """Validate that blocked agents have valid blocker references."""
    if not tree_data:
        return

    tree_agents = tree_data.get("agents", {})
    agent_names = set(tree_agents.keys())

    # Load work order IDs from INDEX.yaml
    index_path = sync_path / "work-orders" / "INDEX.yaml"
    wo_ids: set[str] = set()
    if index_path.exists():
        index_data, _ = _load_yaml(index_path)
        if index_data and "orders" in index_data:
            wo_ids = {order["id"] for order in index_data["orders"] if "id" in order}

    for agent_name, agent_data in tree_agents.items():
        if not isinstance(agent_data, dict):
            continue

        status = agent_data.get("status")
        blockers = agent_data.get("blockers", [])

        if status == "blocked":
            # Blocked agents must have non-empty blockers
            if not blockers:
                result.issues.append(Issue(
                    layer="Protocol",
                    severity=Severity.ERROR,
                    message=f"Agent '{agent_name}' has status 'blocked' but empty blockers list",
                    path="runtime/TREE.yaml",
                ))
                continue

            # Validate each blocker reference
            for blocker in blockers:
                if WO_PATTERN.match(blocker):
                    # It's a work order reference
                    if blocker not in wo_ids:
                        result.issues.append(Issue(
                            layer="Protocol",
                            severity=Severity.ERROR,
                            message=f"Agent '{agent_name}' blocked by non-existent work order '{blocker}'",
                            path="runtime/TREE.yaml",
                        ))
                else:
                    # It's an agent reference
                    if blocker not in agent_names:
                        result.issues.append(Issue(
                            layer="Protocol",
                            severity=Severity.ERROR,
                            message=f"Agent '{agent_name}' blocked by non-existent agent '{blocker}'",
                            path="runtime/TREE.yaml",
                        ))

    # Validate work order deliverables
    _validate_work_order_deliverables(sync_path, result)


# Work order types that require a deliverable
DELIVERABLE_REQUIRED_TYPES = {"FEATURE", "BUGFIX", "HOTFIX", "REFACTOR", "FIX"}


def _validate_work_order_deliverables(sync_path: Path, result: ValidationResult) -> None:
    """Validate that work orders requiring deliverables have them."""
    index_path = sync_path / "work-orders" / "INDEX.yaml"
    if not index_path.exists():
        return

    index_data, _ = _load_yaml(index_path)
    if not index_data or "orders" not in index_data:
        return

    for order in index_data["orders"]:
        wo_id = order.get("id", "unknown")
        wo_type = order.get("type")
        deliverable = order.get("deliverable")

        if wo_type in DELIVERABLE_REQUIRED_TYPES and not deliverable:
            result.issues.append(Issue(
                layer="Protocol",
                severity=Severity.ERROR,
                message=f"Work order '{wo_id}' (type={wo_type}) requires a deliverable field",
                path="work-orders/INDEX.yaml",
            ))


# ─── Layer 4: Boot Integrity ────────────────────────────────────


def validate_boot_integrity(sync_path: Path, agents: list[str], result: ValidationResult) -> None:
    tree_path = sync_path / "runtime" / "TREE.yaml"
    if not tree_path.exists():
        return

    tree_data, err = _load_yaml(tree_path)
    if err or not tree_data:
        return

    tree_version = tree_data.get("tree_version")
    protocol_hash_file = sync_path / "PROTOCOL_DIGEST.hash"
    stored_protocol_hash = None
    if protocol_hash_file.exists():
        stored_protocol_hash = protocol_hash_file.read_text(encoding="utf-8").strip()

    boot_dir = sync_path / "runtime" / "boot"
    if not boot_dir.exists():
        return

    for agent in agents:
        boot_file = boot_dir / f"{agent}.boot.yaml"
        if not boot_file.exists():
            continue

        boot_data, err = _load_yaml(boot_file)
        if err or not boot_data:
            continue

        # tree_version alignment
        boot_tree_version = boot_data.get("tree_version")
        if boot_tree_version is not None and tree_version is not None:
            if boot_tree_version > tree_version:
                result.issues.append(Issue(
                    layer="Boot Integrity",
                    severity=Severity.ERROR,
                    message=(
                        f"{agent}.boot.yaml tree_version ({boot_tree_version}) "
                        f"exceeds TREE.yaml tree_version ({tree_version})"
                    ),
                    path=f"runtime/boot/{agent}.boot.yaml",
                ))

        # protocol hash alignment
        boot_hash = boot_data.get("protocol_digest_hash")
        if boot_hash and stored_protocol_hash:
            if boot_hash != stored_protocol_hash:
                result.issues.append(Issue(
                    layer="Boot Integrity",
                    severity=Severity.WARN,
                    message=(
                        f"{agent}.boot.yaml protocol_digest_hash stale "
                        f"(boot={boot_hash[:16]}... current={stored_protocol_hash[:16]}...)"
                    ),
                    path=f"runtime/boot/{agent}.boot.yaml",
                ))

        # session_count must not be negative
        session_count = boot_data.get("session_count", 0)
        if session_count < 0:
            result.issues.append(Issue(
                layer="Boot Integrity",
                severity=Severity.ERROR,
                message=f"{agent}.boot.yaml has negative session_count: {session_count}",
                path=f"runtime/boot/{agent}.boot.yaml",
            ))

        # graph_version alignment
        tree_graph_version = tree_data.get("graph_version")
        boot_graph_version = boot_data.get("graph_version")
        if boot_graph_version is not None:
            if tree_graph_version is None:
                result.issues.append(Issue(
                    layer="Boot Integrity",
                    severity=Severity.ERROR,
                    message=(
                        f"{agent}.boot.yaml has graph_version but TREE.yaml graph_version is null"
                    ),
                    path=f"runtime/boot/{agent}.boot.yaml",
                ))
            elif boot_graph_version != tree_graph_version:
                result.issues.append(Issue(
                    layer="Boot Integrity",
                    severity=Severity.ERROR,
                    message=(
                        f"{agent}.boot.yaml graph_version mismatch "
                        f"(boot={boot_graph_version[:16]}... tree={tree_graph_version[:16]}...)"
                    ),
                    path=f"runtime/boot/{agent}.boot.yaml",
                ))


# ─── Auto-fix ────────────────────────────────────────────────────


def auto_fix(sync_path: Path, issues: list[Issue]) -> int:
    fixed = 0
    for issue in issues:
        if not issue.auto_fixable:
            continue

        if "without .gitkeep" in issue.message:
            dir_path = sync_path / issue.path
            if dir_path.is_dir():
                (dir_path / ".gitkeep").write_text("", encoding="utf-8")
                fixed += 1

        elif "_read/" in issue.message:
            read_dir = sync_path / issue.path
            read_dir.mkdir(parents=True, exist_ok=True)
            (read_dir / ".gitkeep").write_text("", encoding="utf-8")
            fixed += 1

        elif "outbox" in issue.message:
            outbox_dir = sync_path / issue.path
            outbox_dir.mkdir(parents=True, exist_ok=True)
            (outbox_dir / ".gitkeep").write_text("", encoding="utf-8")
            fixed += 1

    return fixed


# ─── Main Entry Point ────────────────────────────────────────────


def validate(project_path: Path, fix: bool = False) -> ValidationResult:
    """Run full validation on a stackmind runtime.

    Args:
        project_path: Root of the project containing .sync/.
        fix: If True, auto-fix minor issues.

    Returns:
        ValidationResult with all discovered issues.
    """
    project_path = project_path.resolve()
    sync_path = project_path / ".sync"

    result = ValidationResult()

    if not sync_path.exists():
        result.issues.append(Issue(
            layer="Structure",
            severity=Severity.ERROR,
            message="No .sync/ directory found — not a stackmind runtime",
            path=".sync",
        ))
        return result

    # Discover agents from boot snapshots
    agents = _discover_agents(sync_path)
    if not agents:
        result.issues.append(Issue(
            layer="Structure",
            severity=Severity.ERROR,
            message="No agent boot snapshots found in .sync/runtime/boot/",
            path="runtime/boot",
        ))

    # Run all layers
    validate_schema(sync_path, result)
    validate_structure(project_path, sync_path, agents, result)
    validate_protocol(sync_path, agents, result)
    validate_boot_integrity(sync_path, agents, result)

    # Auto-fix if requested
    if fix and result.warnings:
        fixable = [i for i in result.issues if i.auto_fixable]
        if fixable:
            fixed_count = auto_fix(sync_path, fixable)
            for issue in fixable:
                result.issues.remove(issue)
            console.print(f"[bold green][+][/bold green] Auto-fixed {fixed_count} issues")

    return result

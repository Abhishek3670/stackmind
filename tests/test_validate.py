"""Tests for stackmind validate command.

Tests M2 acceptance criteria:
- Schema validation catches invalid YAML
- Structure validation detects missing files/directories
- Protocol compliance checks hash integrity
- Boot integrity detects version mismatches
- Auto-fix repairs minor issues
"""

import shutil
from pathlib import Path

import pytest
import yaml

from cli.init import DEFAULT_AGENTS, init
from cli.validate import (
    Issue,
    Severity,
    ValidationResult,
    auto_fix,
    validate,
    validate_boot_integrity,
    validate_protocol,
    validate_schema,
    validate_structure,
)


# ─── Fixtures ──────────────────────────────────────────────────


@pytest.fixture
def fresh_project(tmp_path):
    """Create a fresh valid STACKMIND project."""
    project = tmp_path / "test-project"
    init(project, name="Test Project", no_git=True)
    return project


@pytest.fixture
def sync_path(fresh_project):
    """Return the .sync/ path of the fresh project."""
    return fresh_project / ".sync"


# ─── Integration Tests: Full Validate ─────────────────────────


class TestValidate:
    """Full integration tests for stackmind validate."""

    def test_fresh_runtime_passes(self, fresh_project):
        result = validate(fresh_project)
        assert result.passed
        assert len(result.errors) == 0

    def test_missing_sync_is_error(self, tmp_path):
        result = validate(tmp_path)
        assert not result.passed
        assert any("not a STACKMIND runtime" in i.message for i in result.errors)

    def test_missing_agents_md(self, fresh_project):
        (fresh_project / "AGENTS.md").unlink()
        result = validate(fresh_project)
        assert not result.passed
        assert any("AGENTS.md" in i.message for i in result.errors)

    def test_corrupt_tree_yaml(self, sync_path):
        tree = sync_path / "runtime" / "TREE.yaml"
        tree.write_text("not: valid: yaml: [", encoding="utf-8")
        result = validate(sync_path.parent)
        assert not result.passed
        assert any("TREE.yaml" in i.message and "Schema" in i.layer for i in result.errors)

    def test_invalid_tree_schema(self, sync_path):
        tree = sync_path / "runtime" / "TREE.yaml"
        tree.write_text(
            "schema_version: 99\ntree_version: 1\nagents: {}\n",
            encoding="utf-8",
        )
        result = validate(sync_path.parent)
        assert any("schema_version" in i.message for i in result.errors)

    def test_bad_protocol_hash(self, sync_path):
        hash_file = sync_path / "PROTOCOL_DIGEST.hash"
        hash_file.write_text("A" * 64, encoding="utf-8")
        result = validate(sync_path.parent)
        assert any("PROTOCOL_DIGEST.hash mismatch" in i.message for i in result.issues)

    def test_boot_tree_version_exceeds(self, sync_path):
        boot = sync_path / "runtime" / "boot" / "claude.boot.yaml"
        data = yaml.safe_load(boot.read_text(encoding="utf-8"))
        data["tree_version"] = 9999
        boot.write_text(yaml.dump(data), encoding="utf-8")
        result = validate(sync_path.parent)
        assert any("exceeds TREE.yaml tree_version" in i.message for i in result.issues)

    def test_missing_boot_file(self, sync_path):
        (sync_path / "runtime" / "boot" / "codex.boot.yaml").unlink()
        result = validate(sync_path.parent)
        assert any("codex" in i.message and "boot" in i.message for i in result.issues)


# ─── Layer Tests: Schema ──────────────────────────────────────


class TestSchemaValidation:
    """Tests for Layer 1: Schema Validation."""

    def test_valid_tree_no_errors(self, sync_path):
        result = ValidationResult()
        validate_schema(sync_path, result)
        schema_errors = [i for i in result.issues if i.layer == "Schema"]
        assert len(schema_errors) == 0

    def test_invalid_tree_version_type(self, sync_path):
        tree = sync_path / "runtime" / "TREE.yaml"
        data = yaml.safe_load(tree.read_text(encoding="utf-8"))
        data["tree_version"] = "not_an_int"
        tree.write_text(yaml.dump(data), encoding="utf-8")

        result = ValidationResult()
        validate_schema(sync_path, result)
        assert any("tree_version" in i.message for i in result.issues)

    def test_valid_boot_no_errors(self, sync_path):
        result = ValidationResult()
        validate_schema(sync_path, result)
        boot_issues = [i for i in result.issues if "boot" in i.path]
        assert len(boot_issues) == 0

    def test_boot_negative_session_count(self, sync_path):
        boot = sync_path / "runtime" / "boot" / "codex.boot.yaml"
        data = yaml.safe_load(boot.read_text(encoding="utf-8"))
        data["session_count"] = -1
        boot.write_text(yaml.dump(data), encoding="utf-8")

        result = ValidationResult()
        validate_schema(sync_path, result)
        assert any("session_count" in i.message for i in result.issues)


# ─── Layer Tests: Structure ───────────────────────────────────


class TestStructureValidation:
    """Tests for Layer 2: Structural Validation."""

    def test_all_dirs_exist_on_fresh(self, fresh_project, sync_path):
        result = ValidationResult()
        agents = DEFAULT_AGENTS
        validate_structure(fresh_project, sync_path, agents, result)
        struct_errors = [i for i in result.issues if i.severity == Severity.ERROR]
        assert len(struct_errors) == 0

    def test_missing_inbox_detected(self, fresh_project, sync_path):
        shutil.rmtree(sync_path / "inbox" / "codex")
        result = ValidationResult()
        validate_structure(fresh_project, sync_path, DEFAULT_AGENTS, result)
        assert any("inbox/codex" in i.message for i in result.issues)

    def test_missing_templates_dir(self, fresh_project, sync_path):
        shutil.rmtree(sync_path / "work-orders" / "TEMPLATES")
        result = ValidationResult()
        validate_structure(fresh_project, sync_path, DEFAULT_AGENTS, result)
        assert any("TEMPLATES" in i.message for i in result.issues)


# ─── Layer Tests: Protocol ────────────────────────────────────


class TestProtocolValidation:
    """Tests for Layer 3: Protocol Compliance."""

    def test_hash_match_no_issues(self, sync_path):
        result = ValidationResult()
        validate_protocol(sync_path, DEFAULT_AGENTS, result)
        protocol_errors = [i for i in result.issues if i.layer == "Protocol" and i.severity == Severity.ERROR]
        assert len(protocol_errors) == 0

    def test_hash_mismatch_detected(self, sync_path):
        (sync_path / "PROTOCOL_DIGEST.hash").write_text("B" * 64, encoding="utf-8")
        result = ValidationResult()
        validate_protocol(sync_path, DEFAULT_AGENTS, result)
        assert any("mismatch" in i.message for i in result.issues)

    def test_missing_agent_in_tree_warns(self, sync_path):
        tree = sync_path / "runtime" / "TREE.yaml"
        data = yaml.safe_load(tree.read_text(encoding="utf-8"))
        del data["agents"]["codex"]
        tree.write_text(yaml.dump(data), encoding="utf-8")

        result = ValidationResult()
        validate_protocol(sync_path, DEFAULT_AGENTS, result)
        assert any("codex" in i.message and "missing from TREE" in i.message for i in result.issues)


# ─── Layer Tests: Boot Integrity ─────────────────────────────


class TestBootIntegrity:
    """Tests for Layer 4: Boot Integrity."""

    def test_fresh_runtime_passes(self, sync_path):
        result = ValidationResult()
        validate_boot_integrity(sync_path, DEFAULT_AGENTS, result)
        boot_errors = [i for i in result.issues if i.severity == Severity.ERROR]
        assert len(boot_errors) == 0

    def test_boot_exceeds_tree_version(self, sync_path):
        boot = sync_path / "runtime" / "boot" / "claude.boot.yaml"
        data = yaml.safe_load(boot.read_text(encoding="utf-8"))
        data["tree_version"] = 999
        boot.write_text(yaml.dump(data), encoding="utf-8")

        result = ValidationResult()
        validate_boot_integrity(sync_path, DEFAULT_AGENTS, result)
        assert any("exceeds" in i.message for i in result.issues)

    def test_stale_protocol_hash_warns(self, sync_path):
        (sync_path / "PROTOCOL_DIGEST.hash").write_text("C" * 64, encoding="utf-8")
        boot = sync_path / "runtime" / "boot" / "claude.boot.yaml"
        data = yaml.safe_load(boot.read_text(encoding="utf-8"))
        data["protocol_digest_hash"] = "D" * 64
        boot.write_text(yaml.dump(data), encoding="utf-8")

        result = ValidationResult()
        validate_boot_integrity(sync_path, DEFAULT_AGENTS, result)
        assert any("stale" in i.message for i in result.issues)


# ─── Auto-fix Tests ──────────────────────────────────────────


class TestAutoFix:
    """Tests for auto-fix capability."""

    def test_fix_missing_read_dir(self, fresh_project, sync_path):
        shutil.rmtree(sync_path / "inbox" / "codex" / "_read")

        result = validate(fresh_project, fix=True)
        assert (sync_path / "inbox" / "codex" / "_read").exists()

    def test_fix_missing_outbox(self, fresh_project, sync_path):
        shutil.rmtree(sync_path / "outbox" / "gemini")

        result = validate(fresh_project, fix=True)
        assert (sync_path / "outbox" / "gemini").exists()

    def test_non_fixable_errors_remain(self, fresh_project, sync_path):
        (fresh_project / "AGENTS.md").unlink()
        result = validate(fresh_project, fix=True)
        assert not result.passed

    def test_missing_read_dir_is_error(self, fresh_project, sync_path):
        """Missing _read/ folder should be ERROR, not WARN."""
        shutil.rmtree(sync_path / "inbox" / "codex" / "_read")

        result = validate(fresh_project, fix=False)
        read_issues = [i for i in result.issues if "_read" in i.message]
        assert len(read_issues) == 1
        assert read_issues[0].severity == Severity.ERROR
        assert read_issues[0].auto_fixable is True

    def test_missing_ceo_read_dir_is_error(self, fresh_project, sync_path):
        """Missing CEO inbox _read/ folder should be ERROR."""
        shutil.rmtree(sync_path / "inbox" / "CEO" / "_read")

        result = validate(fresh_project, fix=False)
        ceo_read_issues = [i for i in result.issues if "CEO/_read" in i.message]
        assert len(ceo_read_issues) == 1
        assert ceo_read_issues[0].severity == Severity.ERROR
        assert ceo_read_issues[0].auto_fixable is True

    def test_fix_missing_ceo_read_dir(self, fresh_project, sync_path):
        """Auto-fix should create missing CEO inbox _read/ folder."""
        shutil.rmtree(sync_path / "inbox" / "CEO" / "_read")

        result = validate(fresh_project, fix=True)
        assert (sync_path / "inbox" / "CEO" / "_read").exists()
        assert (sync_path / "inbox" / "CEO" / "_read" / ".gitkeep").exists()



# ─── Blocked Agent Validation Tests ─────────────────────────────


class TestBlockedAgentValidation:
    """Tests for blocked agent validation."""

    def test_blocked_agent_with_empty_blockers_is_error(self, fresh_project, sync_path):
        """Blocked agent with empty blockers list should be ERROR."""
        tree = sync_path / "runtime" / "TREE.yaml"
        data = yaml.safe_load(tree.read_text(encoding="utf-8"))
        data["agents"]["claude"]["status"] = "blocked"
        data["agents"]["claude"]["blockers"] = []
        tree.write_text(yaml.dump(data), encoding="utf-8")

        result = validate(fresh_project)
        blocked_issues = [i for i in result.issues if "empty blockers" in i.message]
        assert len(blocked_issues) == 1
        assert blocked_issues[0].severity == Severity.ERROR

    def test_blocked_agent_with_valid_wo_blocker_passes(self, fresh_project, sync_path):
        """Blocked agent with valid WO blocker should pass."""
        # Add a work order to INDEX.yaml
        index = sync_path / "work-orders" / "INDEX.yaml"
        index_data = yaml.safe_load(index.read_text(encoding="utf-8"))
        index_data["orders"].append({
            "id": "WO-001",
            "type": "FEATURE",
            "title": "Test WO",
            "status": "ACTIVE",
            "priority": "P1",
            "assigned_agents": ["codex"],
            "dependencies": [],
            "created": "2026-01-01",
            "updated": "2026-01-01",
            "file": "ACTIVE/WO-001.yaml"
        })
        index.write_text(yaml.dump(index_data), encoding="utf-8")

        # Set claude as blocked by WO-001
        tree = sync_path / "runtime" / "TREE.yaml"
        data = yaml.safe_load(tree.read_text(encoding="utf-8"))
        data["agents"]["claude"]["status"] = "blocked"
        data["agents"]["claude"]["blockers"] = ["WO-001"]
        tree.write_text(yaml.dump(data), encoding="utf-8")

        result = validate(fresh_project)
        blocked_issues = [i for i in result.issues if "blocked" in i.message.lower() and "claude" in i.message]
        assert len(blocked_issues) == 0

    def test_blocked_agent_with_valid_agent_blocker_passes(self, fresh_project, sync_path):
        """Blocked agent with valid agent blocker should pass."""
        tree = sync_path / "runtime" / "TREE.yaml"
        data = yaml.safe_load(tree.read_text(encoding="utf-8"))
        data["agents"]["claude"]["status"] = "blocked"
        data["agents"]["claude"]["blockers"] = ["codex"]
        tree.write_text(yaml.dump(data), encoding="utf-8")

        result = validate(fresh_project)
        blocked_issues = [i for i in result.issues if "blocked" in i.message.lower() and "claude" in i.message]
        assert len(blocked_issues) == 0

    def test_blocked_agent_with_nonexistent_wo_is_error(self, fresh_project, sync_path):
        """Blocked agent referencing non-existent WO should be ERROR."""
        tree = sync_path / "runtime" / "TREE.yaml"
        data = yaml.safe_load(tree.read_text(encoding="utf-8"))
        data["agents"]["claude"]["status"] = "blocked"
        data["agents"]["claude"]["blockers"] = ["WO-999"]
        tree.write_text(yaml.dump(data), encoding="utf-8")

        result = validate(fresh_project)
        wo_issues = [i for i in result.issues if "non-existent work order" in i.message]
        assert len(wo_issues) == 1
        assert wo_issues[0].severity == Severity.ERROR

    def test_blocked_agent_with_nonexistent_agent_is_error(self, fresh_project, sync_path):
        """Blocked agent referencing non-existent agent should be ERROR."""
        tree = sync_path / "runtime" / "TREE.yaml"
        data = yaml.safe_load(tree.read_text(encoding="utf-8"))
        data["agents"]["claude"]["status"] = "blocked"
        data["agents"]["claude"]["blockers"] = ["nonexistent-agent"]
        tree.write_text(yaml.dump(data), encoding="utf-8")

        result = validate(fresh_project)
        agent_issues = [i for i in result.issues if "non-existent agent" in i.message]
        assert len(agent_issues) == 1
        assert agent_issues[0].severity == Severity.ERROR

    def test_idle_agent_with_empty_blockers_passes(self, fresh_project, sync_path):
        """Idle agent with empty blockers should pass (only blocked status requires blockers)."""
        tree = sync_path / "runtime" / "TREE.yaml"
        data = yaml.safe_load(tree.read_text(encoding="utf-8"))
        data["agents"]["claude"]["status"] = "idle"
        data["agents"]["claude"]["blockers"] = []
        tree.write_text(yaml.dump(data), encoding="utf-8")

        result = validate(fresh_project)
        blocked_issues = [i for i in result.issues if "empty blockers" in i.message]
        assert len(blocked_issues) == 0


# ─── Graph Version Validation Tests ─────────────────────────────


class TestGraphVersionValidation:
    """Tests for graph_version alignment between boot and TREE."""

    def test_fresh_runtime_with_null_graph_version_passes(self, fresh_project, sync_path):
        """Fresh runtime with null graph_version should pass."""
        result = validate(fresh_project)
        graph_issues = [i for i in result.issues if "graph_version" in i.message]
        assert len(graph_issues) == 0

    def test_boot_graph_version_with_null_tree_is_error(self, fresh_project, sync_path):
        """Boot with graph_version when TREE has null should be ERROR."""
        boot = sync_path / "runtime" / "boot" / "claude.boot.yaml"
        data = yaml.safe_load(boot.read_text(encoding="utf-8"))
        data["graph_version"] = "A" * 64
        boot.write_text(yaml.dump(data), encoding="utf-8")

        result = validate(fresh_project)
        graph_issues = [i for i in result.issues if "graph_version" in i.message and "null" in i.message]
        assert len(graph_issues) == 1
        assert graph_issues[0].severity == Severity.ERROR

    def test_matching_graph_versions_passes(self, fresh_project, sync_path):
        """Matching graph_version in boot and TREE should pass."""
        graph_hash = "B" * 64

        tree = sync_path / "runtime" / "TREE.yaml"
        tree_data = yaml.safe_load(tree.read_text(encoding="utf-8"))
        tree_data["graph_version"] = graph_hash
        tree.write_text(yaml.dump(tree_data), encoding="utf-8")

        boot = sync_path / "runtime" / "boot" / "claude.boot.yaml"
        boot_data = yaml.safe_load(boot.read_text(encoding="utf-8"))
        boot_data["graph_version"] = graph_hash
        boot.write_text(yaml.dump(boot_data), encoding="utf-8")

        result = validate(fresh_project)
        graph_issues = [i for i in result.issues if "graph_version" in i.message]
        assert len(graph_issues) == 0

    def test_mismatched_graph_versions_is_error(self, fresh_project, sync_path):
        """Mismatched graph_version between boot and TREE should be ERROR."""
        tree = sync_path / "runtime" / "TREE.yaml"
        tree_data = yaml.safe_load(tree.read_text(encoding="utf-8"))
        tree_data["graph_version"] = "C" * 64
        tree.write_text(yaml.dump(tree_data), encoding="utf-8")

        boot = sync_path / "runtime" / "boot" / "claude.boot.yaml"
        boot_data = yaml.safe_load(boot.read_text(encoding="utf-8"))
        boot_data["graph_version"] = "D" * 64
        boot.write_text(yaml.dump(boot_data), encoding="utf-8")

        result = validate(fresh_project)
        graph_issues = [i for i in result.issues if "graph_version mismatch" in i.message]
        assert len(graph_issues) == 1
        assert graph_issues[0].severity == Severity.ERROR

    def test_tree_graph_version_with_null_boot_passes(self, fresh_project, sync_path):
        """TREE with graph_version but boot with null should pass (boot hasn't synced yet)."""
        tree = sync_path / "runtime" / "TREE.yaml"
        tree_data = yaml.safe_load(tree.read_text(encoding="utf-8"))
        tree_data["graph_version"] = "E" * 64
        tree.write_text(yaml.dump(tree_data), encoding="utf-8")

        result = validate(fresh_project)
        graph_issues = [i for i in result.issues if "graph_version" in i.message]
        assert len(graph_issues) == 0


# ─── Work Order Deliverable Validation Tests ────────────────────


class TestWorkOrderDeliverableValidation:
    """Tests for work order deliverable requirement."""

    def test_feature_without_deliverable_is_error(self, fresh_project, sync_path):
        """FEATURE work order without deliverable should be ERROR."""
        index = sync_path / "work-orders" / "INDEX.yaml"
        index_data = yaml.safe_load(index.read_text(encoding="utf-8"))
        index_data["orders"].append({
            "id": "WO-001",
            "type": "FEATURE",
            "title": "Test Feature",
            "status": "ACTIVE",
            "priority": "P1",
            "assigned_agents": ["codex"],
            "dependencies": [],
            "created": "2026-01-01",
            "updated": "2026-01-01",
            "file": "ACTIVE/WO-001.yaml"
        })
        index.write_text(yaml.dump(index_data), encoding="utf-8")

        result = validate(fresh_project)
        deliverable_issues = [i for i in result.issues if "deliverable" in i.message]
        assert len(deliverable_issues) == 1
        assert deliverable_issues[0].severity == Severity.ERROR

    def test_feature_with_deliverable_passes(self, fresh_project, sync_path):
        """FEATURE work order with deliverable should pass."""
        index = sync_path / "work-orders" / "INDEX.yaml"
        index_data = yaml.safe_load(index.read_text(encoding="utf-8"))
        index_data["orders"].append({
            "id": "WO-001",
            "type": "FEATURE",
            "title": "Test Feature",
            "status": "ACTIVE",
            "priority": "P1",
            "assigned_agents": ["codex"],
            "dependencies": [],
            "created": "2026-01-01",
            "updated": "2026-01-01",
            "file": "ACTIVE/WO-001.yaml",
            "deliverable": {
                "type": "code",
                "path": "src/feature.py",
                "description": "New feature implementation"
            }
        })
        index.write_text(yaml.dump(index_data), encoding="utf-8")

        result = validate(fresh_project)
        deliverable_issues = [i for i in result.issues if "deliverable" in i.message]
        assert len(deliverable_issues) == 0

    def test_research_without_deliverable_passes(self, fresh_project, sync_path):
        """RESEARCH work order without deliverable should pass (not required)."""
        index = sync_path / "work-orders" / "INDEX.yaml"
        index_data = yaml.safe_load(index.read_text(encoding="utf-8"))
        index_data["orders"].append({
            "id": "WO-001",
            "type": "RESEARCH",
            "title": "Test Research",
            "status": "ACTIVE",
            "priority": "P2",
            "assigned_agents": ["claude"],
            "dependencies": [],
            "created": "2026-01-01",
            "updated": "2026-01-01",
            "file": "ACTIVE/WO-001.yaml"
        })
        index.write_text(yaml.dump(index_data), encoding="utf-8")

        result = validate(fresh_project)
        deliverable_issues = [i for i in result.issues if "deliverable" in i.message]
        assert len(deliverable_issues) == 0

    def test_bugfix_without_deliverable_is_error(self, fresh_project, sync_path):
        """BUGFIX work order without deliverable should be ERROR."""
        index = sync_path / "work-orders" / "INDEX.yaml"
        index_data = yaml.safe_load(index.read_text(encoding="utf-8"))
        index_data["orders"].append({
            "id": "WO-001",
            "type": "BUGFIX",
            "title": "Fix bug",
            "status": "ACTIVE",
            "priority": "P0",
            "assigned_agents": ["codex"],
            "dependencies": [],
            "created": "2026-01-01",
            "updated": "2026-01-01",
            "file": "ACTIVE/WO-001.yaml"
        })
        index.write_text(yaml.dump(index_data), encoding="utf-8")

        result = validate(fresh_project)
        deliverable_issues = [i for i in result.issues if "deliverable" in i.message]
        assert len(deliverable_issues) == 1

    def test_phase_without_deliverable_passes(self, fresh_project, sync_path):
        """PHASE work order without deliverable should pass (not required)."""
        index = sync_path / "work-orders" / "INDEX.yaml"
        index_data = yaml.safe_load(index.read_text(encoding="utf-8"))
        index_data["orders"].append({
            "id": "WO-001",
            "type": "PHASE",
            "title": "Phase 1",
            "status": "ACTIVE",
            "priority": "P1",
            "assigned_agents": ["claude"],
            "dependencies": [],
            "created": "2026-01-01",
            "updated": "2026-01-01",
            "file": "ACTIVE/WO-001.yaml"
        })
        index.write_text(yaml.dump(index_data), encoding="utf-8")

        result = validate(fresh_project)
        deliverable_issues = [i for i in result.issues if "deliverable" in i.message]
        assert len(deliverable_issues) == 0
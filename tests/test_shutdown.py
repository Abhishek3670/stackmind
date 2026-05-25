"""Tests for stackmind shutdown command."""

from pathlib import Path

import pytest
import yaml

from cli.init import init
from cli.shutdown import (
    archive_handoff,
    find_handoff_report,
    shutdown,
    update_boot_snapshot,
    update_tree_status,
)


@pytest.fixture
def fresh_project(tmp_path):
    """Create a fresh valid stackmind project."""
    project = tmp_path / "test-project"
    init(project, name="Test Project", no_git=True)
    return project


@pytest.fixture
def sync_path(fresh_project):
    """Return the .sync/ path of the fresh project."""
    return fresh_project / ".sync"


class TestShutdownHelpers:
    """Tests for shutdown helper functions."""

    def test_find_handoff_report_none(self, sync_path):
        """Should return None when no handoff report exists."""
        outbox = sync_path / "outbox" / "claude"
        result = find_handoff_report(outbox)
        assert result is None

    def test_find_handoff_report_exists(self, sync_path):
        """Should find handoff report when it exists."""
        outbox = sync_path / "outbox" / "claude"
        handoff = outbox / "handoff-2026-05-24T12-00-00.md"
        handoff.write_text("# Handoff Report\n\nSession complete.", encoding="utf-8")

        result = find_handoff_report(outbox)
        assert result is not None
        assert result.name == "handoff-2026-05-24T12-00-00.md"

    def test_find_handoff_report_most_recent(self, sync_path):
        """Should return most recent handoff report."""
        outbox = sync_path / "outbox" / "claude"
        (outbox / "handoff-2026-05-24T10-00-00.md").write_text("old", encoding="utf-8")
        (outbox / "handoff-2026-05-24T12-00-00.md").write_text("new", encoding="utf-8")

        result = find_handoff_report(outbox)
        assert result.name == "handoff-2026-05-24T12-00-00.md"

    def test_update_tree_status(self, sync_path):
        """Should update agent status to idle."""
        assert update_tree_status(sync_path, "claude")

        tree = yaml.safe_load((sync_path / "runtime" / "TREE.yaml").read_text())
        assert tree["agents"]["claude"]["status"] == "idle"

    def test_update_tree_status_invalid_agent(self, sync_path):
        """Should return False for non-existent agent."""
        assert not update_tree_status(sync_path, "nonexistent")

    def test_update_boot_snapshot(self, sync_path):
        """Should increment session_count."""
        boot_path = sync_path / "runtime" / "boot" / "claude.boot.yaml"
        boot = yaml.safe_load(boot_path.read_text())
        original_count = boot.get("session_count", 0)

        assert update_boot_snapshot(sync_path, "claude")

        boot = yaml.safe_load(boot_path.read_text())
        assert boot["session_count"] == original_count + 1

    def test_archive_handoff(self, sync_path):
        """Should move handoff to _read/ directory."""
        outbox = sync_path / "outbox" / "claude"
        handoff = outbox / "handoff-2026-05-24T12-00-00.md"
        handoff.write_text("# Handoff", encoding="utf-8")

        archive_handoff(handoff, outbox)

        assert not handoff.exists()
        assert (outbox / "_read" / "handoff-2026-05-24T12-00-00.md").exists()


class TestShutdownCommand:
    """Tests for the shutdown command."""

    def test_shutdown_without_handoff_fails(self, fresh_project):
        """Should fail when no handoff report exists."""
        result = shutdown(fresh_project, "claude", force=False)
        assert result is False

    def test_shutdown_with_handoff_succeeds(self, fresh_project, sync_path):
        """Should succeed when handoff report exists."""
        outbox = sync_path / "outbox" / "claude"
        handoff = outbox / "handoff-2026-05-24T12-00-00.md"
        handoff.write_text("# Handoff Report\n\nSession complete.", encoding="utf-8")

        result = shutdown(fresh_project, "claude", force=False)
        assert result is True

        # Verify state changes
        tree = yaml.safe_load((sync_path / "runtime" / "TREE.yaml").read_text())
        assert tree["agents"]["claude"]["status"] == "idle"

        # Verify handoff archived
        assert not handoff.exists()
        assert (outbox / "_read" / "handoff-2026-05-24T12-00-00.md").exists()

    def test_shutdown_force_without_handoff(self, fresh_project, sync_path):
        """--force should allow shutdown without handoff."""
        result = shutdown(fresh_project, "claude", force=True)
        assert result is True

        tree = yaml.safe_load((sync_path / "runtime" / "TREE.yaml").read_text())
        assert tree["agents"]["claude"]["status"] == "idle"

    def test_shutdown_invalid_agent(self, fresh_project):
        """Should fail for non-existent agent."""
        result = shutdown(fresh_project, "nonexistent", force=True)
        assert result is False

    def test_shutdown_no_sync_fails(self, tmp_path):
        """Should fail if no .sync/ directory."""
        result = shutdown(tmp_path, "claude", force=True)
        assert result is False

    def test_shutdown_increments_session_count(self, fresh_project, sync_path):
        """Should increment session_count in boot snapshot."""
        outbox = sync_path / "outbox" / "claude"
        handoff = outbox / "handoff-2026-05-24T12-00-00.md"
        handoff.write_text("# Handoff", encoding="utf-8")

        boot_path = sync_path / "runtime" / "boot" / "claude.boot.yaml"
        boot_before = yaml.safe_load(boot_path.read_text())
        count_before = boot_before.get("session_count", 0)

        shutdown(fresh_project, "claude", force=False)

        boot_after = yaml.safe_load(boot_path.read_text())
        assert boot_after["session_count"] == count_before + 1

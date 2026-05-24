"""Tests for stackmind migrate command."""

import shutil
from pathlib import Path

import pytest
import yaml

from cli.init import init
from cli.migrate import (
    apply_migration,
    get_applied_migrations,
    get_current_version,
    get_pending_migrations,
    load_migrations,
    migrate,
    rollback_migration,
    save_applied_migrations,
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


class TestMigrationHelpers:
    """Tests for migration helper functions."""

    def test_get_current_version(self, sync_path):
        """Should return current version from RUNTIME_VERSION."""
        version = get_current_version(sync_path)
        assert version == "1.0.0"

    def test_load_migrations(self):
        """Should load migration manifests from migrations directory."""
        migrations = load_migrations()
        assert len(migrations) >= 1
        assert all("from_version" in m for m in migrations)
        assert all("to_version" in m for m in migrations)

    def test_get_applied_migrations_empty(self, sync_path):
        """Should return empty list when no migrations applied."""
        applied = get_applied_migrations(sync_path)
        assert applied == []

    def test_save_and_get_applied_migrations(self, sync_path):
        """Should save and retrieve applied migrations."""
        save_applied_migrations(sync_path, ["1.1.0", "1.2.0"])
        applied = get_applied_migrations(sync_path)
        assert applied == ["1.1.0", "1.2.0"]

    def test_get_pending_migrations(self):
        """Should return migrations between current and target version."""
        migrations = [
            {"from_version": "1.0.0", "to_version": "1.1.0"},
            {"from_version": "1.1.0", "to_version": "1.2.0"},
            {"from_version": "1.2.0", "to_version": "2.0.0"},
        ]
        pending = get_pending_migrations("1.0.0", "1.2.0", migrations)
        assert len(pending) == 2
        assert pending[0]["to_version"] == "1.1.0"
        assert pending[1]["to_version"] == "1.2.0"


class TestMigrationActions:
    """Tests for migration action execution."""

    def test_apply_add_field(self, sync_path):
        """Should add field to YAML file."""
        migration = {
            "up": [
                {"action": "add_field", "file": "runtime/TREE.yaml", "field": "test_field", "value": "test_value"}
            ],
            "down": []
        }
        assert apply_migration(sync_path, migration)

        tree = yaml.safe_load((sync_path / "runtime" / "TREE.yaml").read_text())
        assert tree["test_field"] == "test_value"

    def test_apply_remove_field(self, sync_path):
        """Should remove field from YAML file."""
        # First add a field
        tree_path = sync_path / "runtime" / "TREE.yaml"
        tree = yaml.safe_load(tree_path.read_text())
        tree["to_remove"] = "value"
        tree_path.write_text(yaml.dump(tree))

        migration = {
            "up": [
                {"action": "remove_field", "file": "runtime/TREE.yaml", "field": "to_remove"}
            ],
            "down": []
        }
        assert apply_migration(sync_path, migration)

        tree = yaml.safe_load(tree_path.read_text())
        assert "to_remove" not in tree

    def test_apply_add_dir(self, sync_path):
        """Should create directory with .gitkeep."""
        migration = {
            "up": [
                {"action": "add_dir", "path": "test_dir/nested"}
            ],
            "down": []
        }
        assert apply_migration(sync_path, migration)

        dir_path = sync_path / "test_dir" / "nested"
        assert dir_path.is_dir()
        assert (dir_path / ".gitkeep").exists()

    def test_apply_remove_dir(self, sync_path):
        """Should remove directory."""
        # First create a directory
        dir_path = sync_path / "to_remove"
        dir_path.mkdir()
        (dir_path / "file.txt").write_text("test")

        migration = {
            "up": [
                {"action": "remove_dir", "path": "to_remove"}
            ],
            "down": []
        }
        assert apply_migration(sync_path, migration)
        assert not dir_path.exists()

    def test_rollback_migration(self, sync_path):
        """Should execute down actions."""
        # Add a field first
        tree_path = sync_path / "runtime" / "TREE.yaml"
        tree = yaml.safe_load(tree_path.read_text())
        tree["rollback_test"] = "value"
        tree_path.write_text(yaml.dump(tree))

        migration = {
            "up": [],
            "down": [
                {"action": "remove_field", "file": "runtime/TREE.yaml", "field": "rollback_test"}
            ]
        }
        assert rollback_migration(sync_path, migration)

        tree = yaml.safe_load(tree_path.read_text())
        assert "rollback_test" not in tree


class TestMigrateCommand:
    """Tests for the migrate command."""

    def test_migrate_check_shows_pending(self, fresh_project, sync_path, capsys):
        """--check should show pending migrations without applying."""
        result = migrate(fresh_project, check=True)
        assert result is True

    def test_migrate_up_to_date(self, fresh_project, sync_path):
        """Should report up to date when no pending migrations."""
        # Mark all migrations as applied
        migrations = load_migrations()
        applied = [m["to_version"] for m in migrations]
        save_applied_migrations(sync_path, applied)

        result = migrate(fresh_project)
        assert result is True

    def test_migrate_applies_migration(self, fresh_project, sync_path):
        """Should apply pending migrations."""
        # Ensure we have the sample migration
        migrations = load_migrations()
        if not migrations:
            pytest.skip("No migrations available")

        result = migrate(fresh_project)
        assert result is True

        # Check migration was tracked
        applied = get_applied_migrations(sync_path)
        assert len(applied) > 0

    def test_migrate_rollback(self, fresh_project, sync_path):
        """--rollback should undo last migration."""
        # First apply a migration
        migrate(fresh_project)
        applied_before = get_applied_migrations(sync_path)

        if not applied_before:
            pytest.skip("No migrations were applied")

        # Now rollback
        result = migrate(fresh_project, rollback=True)
        assert result is True

        applied_after = get_applied_migrations(sync_path)
        assert len(applied_after) == len(applied_before) - 1

    def test_migrate_no_sync_fails(self, tmp_path):
        """Should fail if no .sync/ directory."""
        result = migrate(tmp_path)
        assert result is False

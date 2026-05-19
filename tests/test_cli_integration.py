"""CLI integration tests — exercise main.py commands via Click test runner.

Covers WO-016 M4 test finalization:
- CLI init command
- CLI validate command
- CLI doctor command
- CLI version output
- Error handling paths
"""

import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_project(tmp_path):
    return str(tmp_path / "cli-test-project")


# ─── Version ─────────────────────────────────────────────────


class TestVersion:
    def test_version_flag(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "stackmind" in result.output
        assert "0.1.0" in result.output


# ─── Init Command ────────────────────────────────────────────


class TestInitCLI:
    def test_init_creates_project(self, runner, tmp_project):
        result = runner.invoke(cli, ["init", tmp_project, "--name", "CLI Test", "--no-git"])
        assert result.exit_code == 0
        assert Path(tmp_project).exists()
        assert (Path(tmp_project) / "AGENTS.md").exists()
        assert (Path(tmp_project) / ".sync").exists()

    def test_init_with_agents_flag(self, runner, tmp_project):
        result = runner.invoke(cli, ["init", tmp_project, "--agents", "claude,codex", "--no-git"])
        assert result.exit_code == 0
        boot_dir = Path(tmp_project) / ".sync" / "runtime" / "boot"
        assert (boot_dir / "claude.boot.yaml").exists()
        assert (boot_dir / "codex.boot.yaml").exists()
        assert not (boot_dir / "gemini.boot.yaml").exists()

    def test_init_rejects_existing(self, runner, tmp_project):
        runner.invoke(cli, ["init", tmp_project, "--no-git"])
        result = runner.invoke(cli, ["init", tmp_project, "--no-git"])
        assert result.exit_code != 0

    def test_init_defaults_name_to_dirname(self, runner, tmp_project):
        result = runner.invoke(cli, ["init", tmp_project, "--no-git"])
        assert result.exit_code == 0
        content = (Path(tmp_project) / "AGENTS.md").read_text(encoding="utf-8")
        assert "cli-test-project" in content


# ─── Validate Command ────────────────────────────────────────


class TestValidateCLI:
    def test_validate_healthy_project(self, runner, tmp_project):
        runner.invoke(cli, ["init", tmp_project, "--no-git"])
        result = runner.invoke(cli, ["validate", tmp_project])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_validate_missing_sync(self, runner, tmp_path):
        result = runner.invoke(cli, ["validate", str(tmp_path)])
        assert result.exit_code != 0
        assert "FAIL" in result.output

    def test_validate_fix_flag(self, runner, tmp_project):
        runner.invoke(cli, ["init", tmp_project, "--no-git"])
        # Remove an auto-fixable item
        import shutil
        shutil.rmtree(Path(tmp_project) / ".sync" / "inbox" / "codex" / "_read")
        result = runner.invoke(cli, ["validate", tmp_project, "--fix"])
        assert result.exit_code == 0
        assert (Path(tmp_project) / ".sync" / "inbox" / "codex" / "_read").exists()


# ─── Doctor Command ──────────────────────────────────────────


class TestDoctorCLI:
    def test_doctor_healthy_project(self, runner, tmp_project):
        runner.invoke(cli, ["init", tmp_project, "--no-git"])
        result = runner.invoke(cli, ["doctor", tmp_project])
        assert result.exit_code == 0
        assert "Runtime Version Check" in result.output
        assert "Agent Summary" in result.output

    def test_doctor_missing_sync(self, runner, tmp_path):
        result = runner.invoke(cli, ["doctor", str(tmp_path)])
        assert result.exit_code != 0
        assert "FAIL" in result.output


# ─── Edge Cases ──────────────────────────────────────────────


class TestEdgeCases:
    def test_init_nonexistent_parent(self, runner, tmp_path):
        deep = str(tmp_path / "a" / "b" / "c" / "project")
        result = runner.invoke(cli, ["init", deep, "--no-git"])
        assert result.exit_code == 0
        assert Path(deep).exists()

    def test_validate_corrupt_yaml(self, runner, tmp_project):
        runner.invoke(cli, ["init", tmp_project, "--no-git"])
        tree = Path(tmp_project) / ".sync" / "runtime" / "TREE.yaml"
        tree.write_text("{{{{invalid yaml", encoding="utf-8")
        result = runner.invoke(cli, ["validate", tmp_project])
        assert result.exit_code != 0

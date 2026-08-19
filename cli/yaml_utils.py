"""Shared YAML helper utilities for CLI modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any] | None:
    """Load YAML file, returning None on error."""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_yaml(path: Path, data: dict[str, Any]) -> None:
    """Save data dictionary to YAML file."""
    path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")

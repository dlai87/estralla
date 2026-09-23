"""Durable state helpers for target curriculum repositories."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_DIR = ".aicg"


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp suitable for reports."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def ensure_state_dir(repo_path: Path) -> Path:
    state_dir = repo_path / STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)
    return path


def state_path(repo_path: Path, name: str) -> Path:
    return ensure_state_dir(repo_path) / name


def write_state(repo_path: Path, name: str, data: dict[str, Any]) -> Path:
    return write_json(state_path(repo_path, name), data)


def read_state(repo_path: Path, name: str) -> dict[str, Any]:
    return read_json(state_path(repo_path, name))


def relative_path(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from aicg.diff import diff_repo


def _init_repo(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)


def _write_plan(repo: Path, action_paths: list[str], work_id: str = "fill-foo") -> None:
    plan = {
        "schema_version": 2,
        "repo": {"name": "repo", "path": str(repo)},
        "work_items": [
            {
                "id": work_id,
                "type": "module_solution_gap",
                "actions": [{"type": "write_solution", "path": p} for p in action_paths],
            }
        ],
    }
    (repo / ".aicg").mkdir(parents=True, exist_ok=True)
    (repo / ".aicg" / "work-plan.json").write_text(json.dumps(plan), encoding="utf-8")


def test_diff_reports_expected_file_match(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _write_plan(repo, ["modules/mod-001/exercise-01/SOLUTION.md"])

    target = repo / "modules" / "mod-001" / "exercise-01" / "SOLUTION.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Solution\n\nWorked answer.\n", encoding="utf-8")

    report = diff_repo(repo, work_id="fill-foo")

    assert report["summary"]["untracked"] == 1
    assert report["summary"]["unexpected"] == 0
    entry = report["entries"][0]
    assert entry["expected"] is True
    assert entry["status"] == "untracked"
    assert entry["line_count"] == 3
    assert entry["preview_head"][0] == "# Solution"


def test_diff_flags_unexpected_changes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _write_plan(repo, ["modules/mod-001/exercise-01/SOLUTION.md"])

    (repo / "modules" / "mod-001" / "exercise-01").mkdir(parents=True)
    (repo / "modules" / "mod-001" / "exercise-01" / "SOLUTION.md").write_text(
        "# Solution\n", encoding="utf-8"
    )
    # An off-plan file the agent touched.
    (repo / "unrelated.md").write_text("nope\n", encoding="utf-8")

    report = diff_repo(repo, work_id="fill-foo")

    statuses = {entry["path"]: entry["expected"] for entry in report["entries"]}
    assert statuses["modules/mod-001/exercise-01/SOLUTION.md"] is True
    assert statuses["unrelated.md"] is False
    assert report["summary"]["unexpected"] == 1


def test_diff_skips_aicg_state_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _write_plan(repo, ["modules/mod-001/exercise-01/SOLUTION.md"])

    # Untracked file under .aicg/ — must not appear in report.
    (repo / ".aicg" / "verify-report.json").write_text("{}\n", encoding="utf-8")

    report = diff_repo(repo)

    paths = [entry["path"] for entry in report["entries"]]
    assert all(not p.startswith(".aicg") for p in paths)


def test_diff_full_includes_unified_diff(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    initial = repo / "README.md"
    initial.write_text("# Original\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)

    initial.write_text("# Updated\n", encoding="utf-8")
    _write_plan(repo, ["README.md"])

    report = diff_repo(repo, show_full=True)

    assert report["full_diff"]
    assert "-# Original" in report["full_diff"]
    assert "+# Updated" in report["full_diff"]

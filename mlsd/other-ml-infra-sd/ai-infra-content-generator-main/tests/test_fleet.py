"""Tests for the fleet status read model (roadmap §4)."""
from __future__ import annotations

import json
from pathlib import Path

from aicg.fleet import (
    build_domain_status,
    read_queue_depth,
    render_fleet_table,
)
from aicg.org_config import load_manifest


def _write(path: Path, manifest: dict) -> Path:
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _manifest(org: str, roles: int, *, judge=True, flag_only=True, author=False) -> dict:
    return {
        "org": org,
        "default_remote": f"git@github.com:{org}/{{repo}}.git",
        "quality_judge": {
            "enabled": judge,
            "flag_only": flag_only,
            "thresholds": {"default": 70, "freshness": 76},
        },
        "pipeline": {"phases": {"author": author}, "daily_budget": 8},
        "roles": [
            {
                "id": f"role-{i}",
                "title": f"Role {i}",
                "level": 10 * (i + 1),
                "learning_repo": f"role-{i}-learning",
                "solution_repo": f"role-{i}-solutions",
            }
            for i in range(roles)
        ],
    }


def test_mode_act_observe_inert(tmp_path: Path) -> None:
    act = build_domain_status(
        "d-act", load_manifest(_write(tmp_path / "a.yaml", _manifest("a", 2, author=True)))
    )
    observe = build_domain_status(
        "d-obs", load_manifest(_write(tmp_path / "b.yaml", _manifest("b", 3)))
    )
    inert = build_domain_status(
        "d-inert", load_manifest(_write(tmp_path / "c.yaml", _manifest("c", 1, judge=False)))
    )
    assert act.mode == "ACT"
    assert observe.mode == "OBSERVE"
    assert inert.mode == "INERT"


def test_domain_status_fields(tmp_path: Path) -> None:
    m = load_manifest(_write(tmp_path / "m.yaml", _manifest("ml-engineering-curriculum", 4)))
    s = build_domain_status("ml-engineering", m, queue_depth=5)
    assert s.org == "ml-engineering-curriculum"
    assert s.role_count == 4
    assert s.freshness_bar == 76
    assert s.judge_enabled and s.judge_flag_only
    assert s.queue_depth == 5


def test_read_queue_depth_counts_open_items(tmp_path: Path) -> None:
    (tmp_path / "work-queue.json").write_text(
        json.dumps(
            {
                "items": [
                    {"id": "1", "status": "queued"},
                    {"id": "2", "status": "in_progress"},
                    {"id": "3", "status": "done"},
                ]
            }
        ),
        encoding="utf-8",
    )
    assert read_queue_depth(tmp_path) == 2


def test_read_queue_depth_missing_returns_none(tmp_path: Path) -> None:
    assert read_queue_depth(tmp_path) is None


def test_render_table_includes_every_domain(tmp_path: Path) -> None:
    statuses = [
        build_domain_status("ai-infra", load_manifest(_write(tmp_path / "i.yaml", _manifest("ai-infra-curriculum", 11, author=True)))),
        build_domain_status("ml-engineering", load_manifest(_write(tmp_path / "m.yaml", _manifest("ml-engineering-curriculum", 4)))),
    ]
    out = render_fleet_table(statuses)
    assert "ai-infra" in out
    assert "ml-engineering" in out
    assert "2 domains · 15 roles" in out
    assert "1 ACT / 1 OBSERVE / 0 INERT" in out


def test_render_fleet_digest_totals():
    from aicg.fleet import DigestRow, render_fleet_digest
    rows = [
        DigestRow("ai-infra", "ACT", 76, 11, 11),
        DigestRow("ml-engineering", "ACT", 52, 2, 8),
    ]
    out = render_fleet_digest(rows, date="2026-06-30")
    assert "AICG fleet — 2026-06-30" in out
    assert "ai-infra: 11/11 filled · ACT · BAR 76" in out
    assert "ml-engineering: 2/8 filled" in out
    assert "Total: 13/19 roles (68%) authored" in out

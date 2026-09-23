"""Tests for one-command domain provisioning (roadmap §3)."""
from __future__ import annotations

import json
from pathlib import Path

from aicg.domain_provision import render_org_profile
from aicg.org_config import load_manifest


def _manifest(tmp_path: Path) -> object:
    data = {
        "org": "ml-engineering-curriculum",
        "default_remote": "git@github.com:ml-engineering-curriculum/{repo}.git",
        "maintained_by": {
            "name": "VeriSwarm.ai",
            "url": "https://veriswarm.ai",
            "phrasing": "Maintained by [VeriSwarm.ai](https://veriswarm.ai)",
        },
        "roles": [
            {"id": "principal-ml-engineer", "title": "Principal Machine Learning Engineer", "level": 48,
             "learning_repo": "principal-ml-engineer-learning", "solution_repo": "principal-ml-engineer-solutions"},
            {"id": "ml-engineer", "title": "Machine Learning Engineer", "level": 20,
             "learning_repo": "ml-engineer-learning", "solution_repo": "ml-engineer-solutions"},
        ],
    }
    p = tmp_path / "ml.yaml"
    p.write_text(json.dumps(data), encoding="utf-8")
    return load_manifest(p)


def test_profile_orders_roles_by_level(tmp_path: Path) -> None:
    out = render_org_profile(_manifest(tmp_path))
    # Entry rung should appear before the senior rung in the ladder table.
    assert out.index("Machine Learning Engineer** | L20") < out.index("Principal Machine Learning Engineer** | L48")


def test_profile_has_display_name_and_repo_links(tmp_path: Path) -> None:
    out = render_org_profile(_manifest(tmp_path))
    assert out.startswith("# ML Engineering Curriculum")
    assert "https://github.com/ml-engineering-curriculum/ml-engineer-learning" in out
    assert "Maintained by [VeriSwarm.ai](https://veriswarm.ai)" in out


def test_profile_cross_links_three_siblings_marks_self(tmp_path: Path) -> None:
    out = render_org_profile(_manifest(tmp_path))
    # The current org is marked "you are here"; the other three are linked.
    assert "**ML Engineering Curriculum** *(you are here)*" in out
    for sib in ("ai-infra-curriculum", "ai-engineering-curriculum", "ai-governance-curriculum"):
        assert f"https://github.com/{sib}" in out
    assert "ml-engineering-curriculum)" not in out  # self not rendered as a link


def test_profile_links_career_guide(tmp_path: Path) -> None:
    out = render_org_profile(_manifest(tmp_path))
    assert "[Career Progression Guide](./CAREER_PROGRESSION.md)" in out

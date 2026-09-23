from __future__ import annotations

import json

import pytest

from aicg.agent_cli import AgentLimitReached, classify_limit_scope, retry_after_for_scope
from aicg.generator import generate_from_plan


def test_detects_five_hour_subscription_limit():
    output = "Claude usage limit reached for your 5-hour session. Try again later."

    assert classify_limit_scope(output) == "five_hour"
    assert retry_after_for_scope("five_hour").endswith("Z")


def test_detects_weekly_subscription_limit():
    output = "Weekly limit reached. Please try again next week."

    assert classify_limit_scope(output) == "weekly"


def test_ignores_non_limit_errors():
    assert classify_limit_scope("command not found") is None


def test_generate_all_drains_pending_work(tmp_path):
    from aicg.generator import generate_all_pending

    repo = tmp_path / "repo"
    repo.mkdir()
    script = tmp_path / "noop.sh"
    script.write_text("#!/usr/bin/env bash\necho ok\nexit 0\n", encoding="utf-8")
    script.chmod(0o755)
    plan = {
        "repo": {"name": "repo"},
        "work_items": [
            {
                "id": f"work-{i}",
                "repo": "repo",
                "module": f"mod-{i}",
                "status": "planned",
                "source_policy": {"required_default_sources": []},
                "exercises": [],
            }
            for i in range(3)
        ],
    }

    batch = generate_all_pending(repo, plan, command_override=str(script))

    assert batch["completed_count"] == 3
    assert batch["pending_count"] == 3
    assert batch["deferred"] is None


def test_generate_all_stops_on_subscription_limit(tmp_path):
    from aicg.generator import generate_all_pending

    repo = tmp_path / "repo"
    repo.mkdir()
    script = tmp_path / "limit.sh"
    script.write_text(
        "#!/usr/bin/env bash\necho 'weekly limit reached' >&2\nexit 1\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    plan = {
        "repo": {"name": "repo"},
        "work_items": [
            {
                "id": f"work-{i}",
                "repo": "repo",
                "module": f"mod-{i}",
                "status": "planned",
                "source_policy": {"required_default_sources": []},
                "exercises": [],
            }
            for i in range(3)
        ],
    }

    batch = generate_all_pending(repo, plan, command_override=str(script))

    assert batch["completed_count"] == 0
    assert batch["deferred"] is not None
    assert batch["deferred"]["limit_scope"] == "weekly"


def test_generator_records_limit_pattern_unmatched_when_failure_is_opaque(tmp_path):
    """When the agent fails for unknown reasons, surface a tunable signal."""
    repo = tmp_path / "repo"
    repo.mkdir()
    script = tmp_path / "opaque.sh"
    script.write_text(
        "#!/usr/bin/env bash\necho 'something weird happened' >&2\nexit 1\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    plan = {
        "repo": {"name": "repo"},
        "work_items": [
            {
                "id": "work-1",
                "repo": "repo",
                "module": "mod-001",
                "source_policy": {"required_default_sources": []},
                "exercises": [],
            }
        ],
    }

    with pytest.raises(RuntimeError):
        generate_from_plan(repo, plan, work_id="work-1", command_override=str(script))

    state = json.loads((repo / ".aicg" / "run-state.json").read_text(encoding="utf-8"))
    assert state["status"] == "generator_failed"
    assert state["limit_pattern_unmatched"] is True


def test_generator_persists_limit_state(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    script = tmp_path / "limit.sh"
    script.write_text("#!/usr/bin/env bash\necho 'weekly limit reached' >&2\nexit 1\n", encoding="utf-8")
    script.chmod(0o755)
    plan = {
        "repo": {"name": "repo"},
        "work_items": [
            {
                "id": "work-1",
                "repo": "repo",
                "module": "mod-001",
                "source_policy": {"required_default_sources": []},
                "exercises": [],
            }
        ],
    }

    with pytest.raises(AgentLimitReached):
        generate_from_plan(repo, plan, work_id="work-1", command_override=str(script))

    state = json.loads((repo / ".aicg" / "run-state.json").read_text(encoding="utf-8"))
    assert state["status"] == "agent_limit_reached"
    assert state["limit_scope"] == "weekly"
    assert state["retry_after"].endswith("Z")

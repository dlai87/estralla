from __future__ import annotations

import pytest

from aicg.gitops import GitOpsError, is_aicg_state_path, select_work_item


def test_aicg_state_paths_are_not_pr_content():
    assert is_aicg_state_path(".aicg")
    assert is_aicg_state_path(".aicg/audit-report.json")
    assert not is_aicg_state_path("modules/mod-001/exercise-01/SOLUTION.md")


def test_select_work_item_defaults_to_first():
    items = [{"id": "fill-a"}, {"id": "fill-b"}]
    assert select_work_item(items)["id"] == "fill-a"


def test_select_work_item_finds_by_id():
    items = [{"id": "fill-a"}, {"id": "fill-b"}]
    assert select_work_item(items, work_id="fill-b")["id"] == "fill-b"


def test_select_work_item_raises_when_id_unknown():
    items = [{"id": "fill-a"}]
    with pytest.raises(GitOpsError) as excinfo:
        select_work_item(items, work_id="fill-z")
    assert "fill-z" in str(excinfo.value)
    assert "fill-a" in str(excinfo.value)

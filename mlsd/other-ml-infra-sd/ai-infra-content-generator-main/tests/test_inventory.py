from __future__ import annotations

from conftest import make_security_workspace

from aicg.inventory import WorkspaceInventory


def test_discovers_paired_learning_and_solutions_repos(tmp_path):
    workspace = make_security_workspace(tmp_path)

    inventory = WorkspaceInventory(workspace)
    repos = inventory.by_name()
    solutions = repos["ai-infra-security-solutions"]
    learning = repos["ai-infra-security-learning"]

    assert solutions.kind == "solutions"
    assert learning.kind == "learning"
    assert inventory.paired_repo(solutions) == learning
    assert inventory.paired_repo(learning) == solutions


def test_inventory_recognizes_sibling_org_repos(tmp_path):
    """Prefix-agnostic discovery: sibling-org repos (no ai-infra- prefix) and
    their pairing must resolve, same as ai-infra repos."""
    from aicg.inventory import WorkspaceInventory
    for n in ("ml-engineer-learning", "ml-engineer-solutions",
              "ai-infra-mlops-learning", "ai-infra-mlops-solutions"):
        (tmp_path / n).mkdir()
    inv = WorkspaceInventory(tmp_path)
    names = set(inv.by_name())
    assert {"ml-engineer-learning", "ml-engineer-solutions"} <= names
    learn = inv.require("ml-engineer-learning")
    assert learn.track == "ml-engineer"
    assert inv.paired_repo(learn).name == "ml-engineer-solutions"
    # ai-infra pairing still works
    assert inv.paired_repo(inv.require("ai-infra-mlops-learning")).name == "ai-infra-mlops-solutions"

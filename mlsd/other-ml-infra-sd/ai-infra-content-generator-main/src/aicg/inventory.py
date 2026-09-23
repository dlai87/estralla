"""Workspace and curriculum repository discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

LEARNING_SUFFIX = "-learning"
SOLUTIONS_SUFFIX = "-solutions"


@dataclass(frozen=True)
class RepositoryInfo:
    name: str
    path: Path
    kind: str
    track: str
    has_git: bool

    @property
    def module_root(self) -> Path:
        if self.kind == "learning":
            lessons = self.path / "lessons"
            if lessons.exists():
                return lessons
        return self.path / "modules"


class InventoryError(RuntimeError):
    """Raised when a requested repository cannot be resolved."""


class WorkspaceInventory:
    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()

    def discover(self) -> list[RepositoryInfo]:
        repos: list[RepositoryInfo] = []
        if not self.workspace.exists():
            return repos

        for child in sorted(self.workspace.iterdir(), key=lambda item: item.name):
            if not child.is_dir():
                continue
            info = parse_repository(child)
            if info is not None:
                repos.append(info)
        return repos

    def by_name(self) -> dict[str, RepositoryInfo]:
        return {repo.name: repo for repo in self.discover()}

    def require(self, name: str) -> RepositoryInfo:
        repos = self.by_name()
        if name not in repos:
            available = ", ".join(sorted(repos)) or "none"
            raise InventoryError(f"Repository '{name}' was not found in {self.workspace} ({available}).")
        return repos[name]

    def paired_repo(self, repo: RepositoryInfo) -> RepositoryInfo | None:
        # Swap the suffix on the repo's own name (prefix-agnostic), so this
        # pairs both ai-infra-X-learning <-> ai-infra-X-solutions and the
        # sibling-org X-learning <-> X-solutions.
        if repo.kind == "learning":
            paired_name = repo.name.removesuffix(LEARNING_SUFFIX) + SOLUTIONS_SUFFIX
        elif repo.kind == "solutions":
            paired_name = repo.name.removesuffix(SOLUTIONS_SUFFIX) + LEARNING_SUFFIX
        else:
            return None
        return self.by_name().get(paired_name)


def parse_repository(path: Path) -> RepositoryInfo | None:
    # Recognize any curriculum repo by its -learning/-solutions suffix, across
    # all orgs (ai-infra-X-* and the sibling-org X-*). Repos are resolved by
    # exact name (require/by_name), so making sibling repos discoverable does
    # not cause an org's manifest-driven flow to pick up another org's repos.
    name = path.name
    if name.endswith(LEARNING_SUFFIX):
        kind = "learning"
        track = name.removesuffix(LEARNING_SUFFIX).removeprefix("ai-infra-")
    elif name.endswith(SOLUTIONS_SUFFIX):
        kind = "solutions"
        track = name.removesuffix(SOLUTIONS_SUFFIX).removeprefix("ai-infra-")
    else:
        return None

    return RepositoryInfo(
        name=name,
        path=path.resolve(),
        kind=kind,
        track=track,
        has_git=(path / ".git").exists(),
    )


def default_workspace(cwd: Path | None = None) -> Path:
    current = (cwd or Path.cwd()).resolve()
    if current.name == "ai-infra-content-generator":
        return current.parent
    if (current.parent / "ai-infra-content-generator").exists():
        return current.parent
    return current

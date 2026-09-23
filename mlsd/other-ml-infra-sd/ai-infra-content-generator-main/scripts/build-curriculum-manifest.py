#!/usr/bin/env python3
"""Walk every curriculum repo in a workspace and emit ``manifest/curriculum.manifest.json``.

Layout discovery handles both naming conventions present in the org:
- ``lessons/mod-NNN-name/`` (most learning repos)
- ``modules/mod-NNN-name/`` (most solutions repos + some learning repos)

Each module may contain ``exercise-NN-name/`` subdirectories. Top-level
``projects/project-NN-name/`` directories are catalogued separately, and
``resources/`` files are listed by path.

Titles are extracted from the first H1/H2 in the directory's README.md
(or fall back to the slug). Cross-references between learning and
solutions repos are made by pairing on the slug pattern
``ai-infra-X-learning`` ↔ ``ai-infra-X-solutions``.

Idempotent — re-running produces the same output for an unchanged
workspace.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

LOGGER = logging.getLogger(__name__)

MODULE_DIRS = ("lessons", "modules")
PROJECT_DIR = "projects"
RESOURCE_DIR = "resources"
EXERCISE_RE = re.compile(r"^exercise-(\d+)")
MODULE_RE = re.compile(r"^mod-(\d+)")
PROJECT_RE = re.compile(r"^project-(\d+)")
ORG = "ai-infra-curriculum"

# Track-slug discovery: ``ai-infra-X-learning`` -> ``X``.
TRACK_FROM_REPO_RE = re.compile(r"^ai-infra-(.+)-(?:learning|solutions)$")

# Sibling-org domain configs live next to the org manifest. Their role
# ids name tracks that have LEFT the ai-infra org (the agentic +
# governance split). The workspace may still hold stale local clones of
# those repos under their old ``ai-infra-<slug>-*`` directory names, so
# the slug-based walk would wrongly re-emit them as ai-infra tracks with
# ai-infra-curriculum GitHub URLs. Exclude them by slug.
DOMAINS_DIR = Path(__file__).resolve().parent.parent / "config" / "domains"


def moved_slugs() -> set[str]:
    """Role ids that belong to a sibling-org domain config, not ai-infra."""
    slugs: set[str] = set()
    if not DOMAINS_DIR.is_dir():
        return slugs
    for cfg in sorted(DOMAINS_DIR.glob("*.yaml")):
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            try:
                import yaml  # optional; configs are JSON-compatible
            except ImportError:
                LOGGER.warning("skipping %s: not JSON and PyYAML unavailable", cfg.name)
                continue
            data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        for role in data.get("roles", []):
            slug = role.get("id")
            if slug:
                slugs.add(slug)
    return slugs

# Hierarchy (used to fill `level` field — higher = more senior).
TRACK_LEVEL = {
    "junior-engineer": 1,
    "engineer": 2,
    "ml-platform": 2,
    "mlops": 2,
    "performance": 2,
    "security": 2,
    "senior-engineer": 3,
    "team-lead": 3,
    "principal-engineer": 4,
    "architect": 3,
    "senior-architect": 4,
    "principal-architect": 5,
    # Executive track. The org manifest uses level=70 to keep it
    # above every individual-contributor / architect level.
    "chief-ai-officer": 70,
}


def github_url(repo: str, path: str = "") -> str:
    base = f"https://github.com/{ORG}/{repo}"
    if path:
        return f"{base}/blob/main/{path.lstrip('/')}"
    return base


def read_title(path: Path, fallback: str) -> str:
    """Pull the first H1 (or H2) from a README in this directory."""
    for readme in (path / "README.md", path):
        if readme.is_file() and readme.suffix == ".md":
            text = readme.read_text(encoding="utf-8", errors="ignore")
        elif readme.is_dir():
            continue
        else:
            continue
        for line in text.splitlines()[:30]:
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
            if stripped.startswith("## "):
                return stripped[3:].strip()
    return fallback


def humanize_slug(slug: str) -> str:
    parts = slug.split("-")
    if parts and parts[0].isdigit():
        parts = parts[1:]
    return " ".join(p.capitalize() for p in parts) or slug


def find_module_root(repo: Path) -> Path | None:
    """Return the directory that holds ``mod-NNN-*`` children, or None."""
    for candidate in MODULE_DIRS:
        d = repo / candidate
        if not d.is_dir():
            continue
        for child in d.iterdir():
            if child.is_dir() and MODULE_RE.match(child.name):
                return d
    return None


def list_modules(repo_path: Path) -> list[Path]:
    root = find_module_root(repo_path)
    if root is None:
        return []
    return sorted(
        (p for p in root.iterdir() if p.is_dir() and MODULE_RE.match(p.name)),
        key=lambda p: int(MODULE_RE.match(p.name).group(1)),
    )


def list_exercises(module_path: Path) -> list[Path]:
    return sorted(
        (
            p
            for p in module_path.iterdir()
            if p.is_dir() and EXERCISE_RE.match(p.name)
        ),
        key=lambda p: int(EXERCISE_RE.match(p.name).group(1)),
    )


def list_projects(repo_path: Path) -> list[Path]:
    proj_dir = repo_path / PROJECT_DIR
    if not proj_dir.is_dir():
        return []
    return sorted(
        (
            p
            for p in proj_dir.iterdir()
            if p.is_dir() and PROJECT_RE.match(p.name)
        ),
        key=lambda p: int(PROJECT_RE.match(p.name).group(1)),
    )


def list_resources(repo_path: Path) -> list[Path]:
    res_dir = repo_path / RESOURCE_DIR
    if not res_dir.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(res_dir.rglob("*.md")):
        if p.is_file():
            out.append(p)
    return out


def relative_path(path: Path, repo_path: Path) -> str:
    return str(path.relative_to(repo_path)).replace("\\", "/")


def build_exercise(
    ex_dir_learning: Path | None,
    ex_dir_solutions: Path | None,
    repo_learning: str | None,
    repo_solutions: str | None,
    repo_learning_path: Path | None,
    repo_solutions_path: Path | None,
) -> dict:
    name_source = ex_dir_learning or ex_dir_solutions
    if name_source is None:
        raise RuntimeError("build_exercise called with no directory")
    match = EXERCISE_RE.match(name_source.name)
    number = int(match.group(1)) if match else 0
    title = read_title(name_source, fallback=humanize_slug(name_source.name))

    def rel(d: Path | None, base: Path | None) -> str | None:
        if d is None or base is None:
            return None
        return relative_path(d, base)

    def url(d: Path | None, base: Path | None, repo: str | None) -> str | None:
        if d is None or base is None or repo is None:
            return None
        return github_url(repo, relative_path(d, base))

    return {
        "slug": name_source.name,
        "number": number,
        "title": title,
        "learning_path": rel(ex_dir_learning, repo_learning_path),
        "solutions_path": rel(ex_dir_solutions, repo_solutions_path),
        "learning_url": url(ex_dir_learning, repo_learning_path, repo_learning),
        "solutions_url": url(ex_dir_solutions, repo_solutions_path, repo_solutions),
    }


def build_module(mod_path: Path, repo_path: Path, repo: str) -> dict:
    match = MODULE_RE.match(mod_path.name)
    number = int(match.group(1)) if match else 0
    title = read_title(mod_path, fallback=humanize_slug(mod_path.name))
    return {
        "slug": mod_path.name,
        "number": number,
        "title": title,
        "path": relative_path(mod_path, repo_path),
        "github_url": github_url(repo, relative_path(mod_path, repo_path)),
        "exercises": [],
        "prerequisites": [],
        "related": [],
    }


def build_project(
    proj_learning: Path | None,
    proj_solutions: Path | None,
    repo_learning: str | None,
    repo_solutions: str | None,
    repo_learning_path: Path | None,
    repo_solutions_path: Path | None,
) -> dict:
    src = proj_learning or proj_solutions
    if src is None:
        raise RuntimeError("build_project called with no directory")
    match = PROJECT_RE.match(src.name)
    number = int(match.group(1)) if match else 0
    title = read_title(src, fallback=humanize_slug(src.name))

    docs: list[str] = []
    if proj_learning is not None:
        docs.extend(
            sorted(p.name for p in proj_learning.iterdir() if p.is_file() and p.suffix == ".md")
        )

    def rel(d: Path | None, base: Path | None) -> str | None:
        if d is None or base is None:
            return None
        return relative_path(d, base)

    def url(d: Path | None, base: Path | None, repo: str | None) -> str | None:
        if d is None or base is None or repo is None:
            return None
        return github_url(repo, relative_path(d, base))

    return {
        "slug": src.name,
        "number": number,
        "title": title,
        "learning_path": rel(proj_learning, repo_learning_path),
        "solutions_path": rel(proj_solutions, repo_solutions_path),
        "learning_url": url(proj_learning, repo_learning_path, repo_learning),
        "solutions_url": url(proj_solutions, repo_solutions_path, repo_solutions),
        "docs": docs,
        "prerequisites": [],
    }


def build_resource(path: Path, repo_path: Path, repo: str) -> dict:
    rel = relative_path(path, repo_path)
    slug = path.stem
    return {
        "slug": slug,
        "path": rel,
        "github_url": github_url(repo, rel),
    }


def discover_tracks(workspace: Path) -> dict[str, dict]:
    """Pair learning + solutions repos by track slug.

    Tracks that have moved to a sibling org (see ``moved_slugs``) are
    skipped so the ai-infra manifest stays scoped to its own 11 roles.
    """
    excluded = moved_slugs()
    pairs: dict[str, dict[str, str]] = defaultdict(dict)
    for entry in sorted(workspace.iterdir()):
        if not entry.is_dir():
            continue
        match = TRACK_FROM_REPO_RE.match(entry.name)
        if match is None:
            continue
        track_slug = match.group(1)
        if track_slug in excluded:
            continue
        kind = "learning" if entry.name.endswith("-learning") else "solutions"
        pairs[track_slug][kind] = entry.name
    return dict(pairs)


def build_track(track_slug: str, repos: dict[str, str], workspace: Path) -> dict:
    learning_repo = repos.get("learning")
    solutions_repo = repos.get("solutions")
    learning_path = workspace / learning_repo if learning_repo else None
    solutions_path = workspace / solutions_repo if solutions_repo else None

    modules: list[dict] = []

    # Catalog modules. Prefer the learning repo's modules; if it has
    # none (e.g., a solutions-only track), use the solutions repo.
    primary_path = (
        learning_path
        if learning_path and list_modules(learning_path)
        else solutions_path
    )
    primary_repo = (
        learning_repo if primary_path is learning_path else solutions_repo
    )

    if primary_path and primary_repo:
        for mod_path in list_modules(primary_path):
            module = build_module(mod_path, primary_path, primary_repo)
            # Cross-reference exercises across learning + solutions
            learning_mod = (
                learning_path / "lessons" / mod_path.name
                if learning_path and (learning_path / "lessons" / mod_path.name).is_dir()
                else learning_path / "modules" / mod_path.name
                if learning_path and (learning_path / "modules" / mod_path.name).is_dir()
                else None
            )
            solutions_mod = (
                solutions_path / "modules" / mod_path.name
                if solutions_path and (solutions_path / "modules" / mod_path.name).is_dir()
                else solutions_path / "lessons" / mod_path.name
                if solutions_path and (solutions_path / "lessons" / mod_path.name).is_dir()
                else None
            )

            learning_exercises = {
                p.name: p for p in (list_exercises(learning_mod) if learning_mod else [])
            }
            solutions_exercises = {
                p.name: p for p in (list_exercises(solutions_mod) if solutions_mod else [])
            }
            all_slugs = sorted(set(learning_exercises) | set(solutions_exercises))
            module["exercises"] = [
                build_exercise(
                    learning_exercises.get(slug),
                    solutions_exercises.get(slug),
                    learning_repo,
                    solutions_repo,
                    learning_path,
                    solutions_path,
                )
                for slug in sorted(
                    all_slugs,
                    key=lambda s: int(EXERCISE_RE.match(s).group(1))
                    if EXERCISE_RE.match(s)
                    else 0,
                )
            ]
            modules.append(module)

    # Catalog projects across the same pair.
    learning_projects = {p.name: p for p in (list_projects(learning_path) if learning_path else [])}
    solutions_projects = {p.name: p for p in (list_projects(solutions_path) if solutions_path else [])}
    project_slugs = sorted(
        set(learning_projects) | set(solutions_projects),
        key=lambda s: int(PROJECT_RE.match(s).group(1))
        if PROJECT_RE.match(s)
        else 0,
    )
    projects = [
        build_project(
            learning_projects.get(slug),
            solutions_projects.get(slug),
            learning_repo,
            solutions_repo,
            learning_path,
            solutions_path,
        )
        for slug in project_slugs
    ]

    # Resources only come from the learning repo (solutions has narrower
    # scope and reuses the same reading lists).
    resources = []
    if learning_path and learning_repo:
        for p in list_resources(learning_path):
            resources.append(build_resource(p, learning_path, learning_repo))

    display_name = humanize_slug(track_slug) + " Track"
    return {
        "slug": track_slug,
        "display_name": display_name,
        "level": TRACK_LEVEL.get(track_slug, 0),
        "learning_repo": learning_repo,
        "solutions_repo": solutions_repo,
        "learning_repo_url": github_url(learning_repo) if learning_repo else None,
        "solutions_repo_url": github_url(solutions_repo) if solutions_repo else None,
        "modules": modules,
        "projects": projects,
        "resources": resources,
    }


def build_manifest(workspace: Path) -> dict:
    tracks = discover_tracks(workspace)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "org": ORG,
        "tracks": [build_track(slug, repos, workspace) for slug, repos in sorted(tracks.items())],
    }


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd().parent,
        help="Parent dir holding ai-infra-*-learning and ai-infra-*-solutions repos. Default: parent of CWD.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output JSON path. Default: manifest/curriculum.manifest.json next to this script.",
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print to stdout instead of writing the file.",
    )
    args = parser.parse_args(argv)

    workspace: Path = args.workspace.expanduser().resolve()
    if not workspace.is_dir():
        LOGGER.error("workspace not found: %s", workspace)
        return 2

    out: Path = (
        args.out.expanduser().resolve()
        if args.out is not None
        else Path(__file__).resolve().parent.parent / "manifest" / "curriculum.manifest.json"
    )

    manifest = build_manifest(workspace)
    payload = json.dumps(manifest, indent=2, sort_keys=False) + "\n"

    if args.print:
        sys.stdout.write(payload)
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(payload, encoding="utf-8")
    LOGGER.info(
        "Wrote %s — %d tracks, %d modules, %d exercises, %d projects, %d resources",
        out,
        len(manifest["tracks"]),
        sum(len(t["modules"]) for t in manifest["tracks"]),
        sum(len(m["exercises"]) for t in manifest["tracks"] for m in t["modules"]),
        sum(len(t["projects"]) for t in manifest["tracks"]),
        sum(len(t["resources"]) for t in manifest["tracks"]),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

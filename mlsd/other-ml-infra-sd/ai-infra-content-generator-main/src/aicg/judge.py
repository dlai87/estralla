"""LLM-as-judge quality grading for generated artifacts.

The structural verify step in :mod:`aicg.verify` confirms that the
agent wrote the right files with the right sections. It does *not*
read the actual content. The judge closes that gap by invoking a
separate configured judge CLI (Claude / Codex / any local wrapper)
on every produced artifact and parsing a JSON verdict::

    {
      "total": 0-100,
      "dimensions": {"correctness": 0-25, ...},
      "blockers": ["string"],
      "summary": "..."
    }

The judge is wired through the manifest::

    quality_judge:
      enabled: true
      agent_command: "{runner}/scripts/run-claude-judge.sh ..."
      thresholds:
        default: 70
        module_rationale_missing: 65
      dimensions:
        - correctness
        - clarity
        - source_quality
        - depth

When ``enabled`` is false (the default) or no agent_command is set,
``judge_action`` returns ``None`` and the verify step proceeds with
structural-only checks.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agent_cli import (
    AgentCommandResult,
    classify_limit_scope,
    reclassify_with_response_file,
    retry_after_for_scope,
)
from .org_config import OrgManifest

DEFAULT_DIMENSIONS = ("correctness", "clarity", "source_quality", "depth")
DEFAULT_DIMENSION_MAX = 25  # 4 dimensions × 25 == 100
DEFAULT_THRESHOLD = 70

# Freshness dimensions are (name, description) pairs so they are fully
# domain-configurable (roadmap §2.1). The default set is AI/tech-shaped; a
# non-tech domain supplies its own via quality_judge.freshness_dimensions
# (e.g. nursing: guideline_currency / regulation_currency).
DEFAULT_FRESHNESS_DIMENSIONS = (
    (
        "api_currency",
        "deprecated APIs, removed methods, idioms that have been superseded in "
        "the current library release.",
    ),
    (
        "version_currency",
        "references to old versions of libraries, tools, or platforms where a "
        "current release is materially different.",
    ),
    (
        "citation_validity",
        "broken links, dead vendors, docs at URLs that have moved, blog posts "
        "older than 3 years cited as 'current'.",
    ),
    (
        "hardware_currency",
        "references to hardware that has been superseded (e.g. V100, A100 cited "
        "as 'latest').",
    ),
)
FRESHNESS_DEFAULT_THRESHOLD = 75

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _parse_freshness_dimensions(raw: Any) -> tuple[tuple[str, str], ...]:
    """Parse manifest ``freshness_dimensions`` into (name, description) pairs."""
    if not raw:
        return DEFAULT_FRESHNESS_DIMENSIONS
    parsed: list[tuple[str, str]] = []
    for entry in raw:
        if isinstance(entry, dict):
            name = str(entry.get("name", "")).strip()
            if name:
                parsed.append((name, str(entry.get("description", name))))
        elif isinstance(entry, (list, tuple)) and entry:
            name = str(entry[0])
            parsed.append((name, str(entry[1]) if len(entry) > 1 else name))
        else:
            name = str(entry)
            parsed.append((name, name))
    return tuple(parsed) if parsed else DEFAULT_FRESHNESS_DIMENSIONS


class JudgeError(RuntimeError):
    """Raised when the judge invocation cannot be carried out."""


@dataclass(frozen=True)
class JudgeConfig:
    enabled: bool
    agent_command: str | None
    dimensions: tuple[str, ...]
    thresholds: dict[str, int]
    timeout_seconds: int | None
    # Minimum days between freshness scans of the same artifact. Files
    # scanned more recently than this are skipped by `review_existing_
    # artifacts` so the per-night cap rotates through all artifacts
    # over time instead of re-judging the alphabetically-first 50.
    # 90 days = quarterly, which matches how slowly staleness develops
    # (deprecations, version bumps, dead vendor links).
    freshness_cooldown_days: int = 90
    # Flag-only mode: the judge scores and reports staleness but the review
    # loop enqueues NO repair work item (no autonomous regeneration). This is
    # the safe first activation (design doc P0) — full visibility, zero action,
    # until the judge has earned trust on live content.
    flag_only: bool = False
    # Domain-configurable freshness rubric (roadmap §2.1): (name, description)
    # pairs. Defaults to the AI/tech set; override per domain in the manifest.
    freshness_dimensions: tuple[tuple[str, str], ...] = DEFAULT_FRESHNESS_DIMENSIONS

    @classmethod
    def from_manifest(cls, manifest: OrgManifest) -> "JudgeConfig":
        cfg = getattr(manifest, "quality_judge", None) or {}
        raw_dimensions = cfg.get("dimensions") or DEFAULT_DIMENSIONS
        dimensions = tuple(str(item) for item in raw_dimensions)
        thresholds = {
            str(key): int(value) for key, value in (cfg.get("thresholds") or {}).items()
        }
        thresholds.setdefault("default", DEFAULT_THRESHOLD)
        return cls(
            enabled=bool(cfg.get("enabled", False)),
            agent_command=cfg.get("agent_command"),
            dimensions=dimensions,
            thresholds=thresholds,
            timeout_seconds=cfg.get("timeout_seconds"),
            freshness_cooldown_days=int(cfg.get("freshness_cooldown_days", 90)),
            flag_only=bool(cfg.get("flag_only", False)),
            freshness_dimensions=_parse_freshness_dimensions(cfg.get("freshness_dimensions")),
        )

    def threshold_for(self, work_type: str) -> int:
        return int(self.thresholds.get(work_type, self.thresholds.get("default", DEFAULT_THRESHOLD)))

    def freshness_threshold(self) -> int:
        return int(
            self.thresholds.get(
                "freshness", self.thresholds.get("default", FRESHNESS_DEFAULT_THRESHOLD)
            )
        )


@dataclass(frozen=True)
class JudgeVerdict:
    score: int
    dimensions: dict[str, int]
    blockers: list[str]
    summary: str
    passed: bool
    threshold: int
    raw: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "dimensions": dict(self.dimensions),
            "blockers": list(self.blockers),
            "summary": self.summary,
            "passed": self.passed,
            "threshold": self.threshold,
        }


def judge_action(
    repo_path: Path,
    work_item: dict[str, Any],
    action: dict[str, Any],
    artifact_path: Path,
    config: JudgeConfig,
    runner_root: Path | None = None,
) -> JudgeVerdict | None:
    """Invoke the configured judge on ``artifact_path``.

    Returns ``None`` when the judge is disabled / unconfigured so the
    caller can skip quality grading without ceremony.
    """
    if not config.enabled or not config.agent_command:
        return None
    if not artifact_path.exists():
        # Structural verify already reported a missing file; nothing
        # for the judge to grade.
        return None

    work_type = work_item.get("type", "")
    threshold = config.threshold_for(work_type)
    prompt_path = _write_judge_prompt(
        repo_path=repo_path,
        work_item=work_item,
        action=action,
        artifact_path=artifact_path,
        config=config,
    )
    output_dir = repo_path / ".aicg" / "judge" / work_item["id"]
    output_dir.mkdir(parents=True, exist_ok=True)
    formatted = config.agent_command.format(
        prompt=str(prompt_path),
        output_dir=str(output_dir),
        repo=str(repo_path),
        work_id=work_item["id"],
        artifact=str(artifact_path),
        runner=str(runner_root or Path(__file__).resolve().parents[2]),
    )
    result = _run_judge_command(formatted, cwd=repo_path, timeout=config.timeout_seconds)
    # See Bug 2 fix in agent_cli.reclassify_with_response_file — the
    # judge wrapper also redirects claude's stdout into response.json,
    # so a session-limit JSONL line lands there rather than in our
    # subprocess stdout. Re-classify before falling through to
    # "command failed" status.
    response_path = output_dir / "response.json"
    result = reclassify_with_response_file(result, response_path)
    if result.limit_reached:
        # The judge can hit subscription limits too; report it as a
        # blocker instead of recording a fake score.
        return JudgeVerdict(
            score=0,
            dimensions={dim: 0 for dim in config.dimensions},
            blockers=[
                f"Judge subscription limit reached ({result.limit_scope}); "
                f"retry after {result.retry_after}."
            ],
            summary="Judge unavailable: subscription limit.",
            passed=False,
            threshold=threshold,
            raw=result.stdout + "\n" + result.stderr,
        )
    if result.returncode != 0:
        return JudgeVerdict(
            score=0,
            dimensions={dim: 0 for dim in config.dimensions},
            blockers=[f"Judge command failed with exit {result.returncode}."],
            summary="Judge command failed.",
            passed=False,
            threshold=threshold,
            raw=result.stdout + "\n" + result.stderr,
        )

    raw_text = response_path.read_text(encoding="utf-8") if response_path.exists() else result.stdout
    verdict = parse_judge_response(
        raw_text=raw_text,
        config=config,
        threshold=threshold,
    )
    return verdict


def judge_artifact_freshness(
    repo_path: Path,
    artifact_path: Path,
    artifact_id: str,
    config: JudgeConfig,
    runner_root: Path | None = None,
) -> JudgeVerdict | None:
    """Invoke the judge on an *existing* artifact for freshness review.

    Unlike :func:`judge_action`, this does not require a plan or a
    work_item — it's used by ``aicg org review`` to scan committed
    content for staleness. Returns ``None`` when the judge is disabled
    or unconfigured.
    """
    if not config.enabled or not config.agent_command:
        return None
    if not artifact_path.exists():
        return None

    threshold = config.freshness_threshold()
    # The freshness rubric comes from config.freshness_dimensions (domain-
    # configurable, §2.1); the prompt reads them directly.
    prompt_path = _write_freshness_prompt(
        repo_path=repo_path,
        artifact_path=artifact_path,
        artifact_id=artifact_id,
        config=config,
    )
    output_dir = repo_path / ".aicg" / "review" / _safe_slug(artifact_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    formatted = config.agent_command.format(
        prompt=str(prompt_path),
        output_dir=str(output_dir),
        repo=str(repo_path),
        work_id=f"review:{artifact_id}",
        artifact=str(artifact_path),
        runner=str(runner_root or Path(__file__).resolve().parents[2]),
    )
    result = _run_judge_command(
        formatted, cwd=repo_path, timeout=config.timeout_seconds
    )
    # Bug 2: peek into response.json for a session-limit JSONL line
    # before reporting a generic command failure.
    response_path = output_dir / "response.json"
    result = reclassify_with_response_file(result, response_path)
    if result.limit_reached:
        return JudgeVerdict(
            score=0,
            dimensions={name: 0 for name, _ in config.freshness_dimensions},
            blockers=[
                f"Judge subscription limit reached ({result.limit_scope}); "
                f"retry after {result.retry_after}."
            ],
            summary="Freshness review unavailable: subscription limit.",
            passed=False,
            threshold=threshold,
            raw=result.stdout + "\n" + result.stderr,
        )
    if result.returncode != 0:
        return JudgeVerdict(
            score=0,
            dimensions={name: 0 for name, _ in config.freshness_dimensions},
            blockers=[f"Freshness judge failed with exit {result.returncode}."],
            summary="Freshness judge command failed.",
            passed=False,
            threshold=threshold,
            raw=result.stdout + "\n" + result.stderr,
        )

    raw_text = (
        response_path.read_text(encoding="utf-8")
        if response_path.exists()
        else result.stdout
    )
    return parse_judge_response(raw_text=raw_text, config=config, threshold=threshold)


def parse_judge_response(
    raw_text: str,
    config: JudgeConfig,
    threshold: int,
) -> JudgeVerdict:
    """Parse the judge's response into a verdict, tolerantly."""
    payload = _extract_json_payload(raw_text)
    if payload is None:
        return JudgeVerdict(
            score=0,
            dimensions={dim: 0 for dim in config.dimensions},
            blockers=["Judge response did not contain a JSON verdict."],
            summary=(raw_text or "")[-400:].strip(),
            passed=False,
            threshold=threshold,
            raw=raw_text,
        )

    dimensions_raw = payload.get("dimensions") or {}
    dimensions: dict[str, int] = {}
    for dim in config.dimensions:
        score = dimensions_raw.get(dim)
        try:
            dimensions[dim] = int(score) if score is not None else 0
        except (TypeError, ValueError):
            dimensions[dim] = 0

    total: int
    if "total" in payload:
        try:
            total = int(payload["total"])
        except (TypeError, ValueError):
            total = sum(dimensions.values())
    else:
        total = sum(dimensions.values())

    blockers_raw = payload.get("blockers") or []
    if isinstance(blockers_raw, str):
        blockers_raw = [blockers_raw]
    blockers = [str(item) for item in blockers_raw if item]

    summary = str(payload.get("summary", "")).strip()

    passed = total >= threshold and not blockers
    return JudgeVerdict(
        score=max(0, min(100, total)),
        dimensions=dimensions,
        blockers=blockers,
        summary=summary,
        passed=passed,
        threshold=threshold,
        raw=raw_text,
    )


def _extract_json_payload(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    # Allow either a raw JSON object or a fenced ```json``` block.
    match = _JSON_BLOCK_RE.search(text)
    candidate = match.group(1) if match else None
    if candidate is None:
        stripped = text.strip()
        if stripped.startswith("{"):
            candidate = stripped
    if candidate is None:
        return None
    try:
        loaded = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, dict) else None


def _write_freshness_prompt(
    repo_path: Path,
    artifact_path: Path,
    artifact_id: str,
    config: JudgeConfig,
) -> Path:
    rel = (
        artifact_path.relative_to(repo_path).as_posix()
        if artifact_path.is_absolute()
        else str(artifact_path)
    )
    dims = config.freshness_dimensions or DEFAULT_FRESHNESS_DIMENSIONS
    per_dim_max = 100 // len(dims)
    dimension_rubric = "\n".join(
        f"- `{name}` (0-{per_dim_max}): {description}" for name, description in dims
    )
    dims_json = ", ".join('"' + name + '": 0' for name, _ in dims)
    content = (
        f"# Freshness review: {artifact_id}\n\n"
        f"You are reviewing a committed curriculum artifact for staleness.\n"
        f"This is NOT a generation task. You may suggest changes in your\n"
        f"summary but you MUST NOT edit the file. The runner will turn\n"
        f"your verdict into a separate work item if a refresh is needed.\n\n"
        f"## Artifact\n\n"
        f"Path: `{rel}`\n\n"
        f"Read the file at the absolute path: `{artifact_path}`\n\n"
        f"## Rubric\n\n"
        f"{dimension_rubric}\n\n"
        f"List any `blockers` for anything that would mislead a learner "
        f"into using deprecated, insecure, or no-longer-correct patterns.\n\n"
        f"## Output contract\n\n"
        f"Write `response.json` in the output directory with this shape:\n\n"
        f"```json\n"
        f"{{\n"
        f"  \"total\": 0-100,\n"
        f"  \"dimensions\": {{{dims_json}}},\n"
        f"  \"blockers\": [\"description of any stale claim\"],\n"
        f"  \"summary\": \"one-paragraph note explaining specific stale references\"\n"
        f"}}\n"
        f"```\n"
    )
    return _write_prompt(
        repo_path=repo_path,
        artifact_id=artifact_id,
        content=content,
    )


def _write_prompt(repo_path: Path, artifact_id: str, content: str) -> Path:
    output_dir = repo_path / ".aicg" / "review" / _safe_slug(artifact_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = output_dir / "prompt.md"
    prompt_path.write_text(content, encoding="utf-8")
    return prompt_path


def _safe_slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-]+", "-", text).strip("-").lower()[:120]


def _write_judge_prompt(
    repo_path: Path,
    work_item: dict[str, Any],
    action: dict[str, Any],
    artifact_path: Path,
    config: JudgeConfig,
) -> Path:
    rubric_lines = "\n".join(
        f"- {dim} (0-{DEFAULT_DIMENSION_MAX}): score the artifact's "
        f"{dim.replace('_', ' ')}."
        for dim in config.dimensions
    )
    content = (
        f"# Judge packet: {work_item['id']}\n\n"
        f"You are an LLM-as-judge grading a curriculum artifact.\n\n"
        f"## Work item\n\n"
        f"- ID: `{work_item['id']}`\n"
        f"- Type: `{work_item.get('type', '?')}`\n"
        f"- Module: `{work_item.get('module', '-')}`\n"
        f"- Project: `{work_item.get('project', '-')}`\n"
        f"- Title: {work_item.get('title', '')}\n\n"
        f"## Artifact to grade\n\n"
        f"Path: `{artifact_path.relative_to(repo_path) if artifact_path.is_absolute() else artifact_path}`\n\n"
        f"Read the file at the absolute path: `{artifact_path}`\n\n"
        f"## Rubric\n\n"
        f"{rubric_lines}\n\n"
        f"List any `blockers` that should fail the work item regardless "
        f"of score (e.g. fabricated citations, unresolved `needs-research` "
        f"markers, factually wrong claims, contradicts source policy).\n\n"
        f"## Output contract\n\n"
        f"Write `response.json` in the output directory with this shape:\n\n"
        f"```json\n"
        f"{{\n"
        f"  \"total\": 0-100,\n"
        f"  \"dimensions\": {{{', '.join(f'\"{d}\": 0' for d in config.dimensions)}}},\n"
        f"  \"blockers\": [],\n"
        f"  \"summary\": \"one-paragraph rationale\"\n"
        f"}}\n"
        f"```\n\n"
        f"If you cannot reach the artifact, set `total: 0` and include\n"
        f"the reason in `blockers`.\n"
    )
    prompt_dir = repo_path / ".aicg" / "judge" / work_item["id"]
    prompt_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = prompt_dir / "prompt.md"
    prompt_path.write_text(content, encoding="utf-8")
    return prompt_path


def _run_judge_command(
    command: str, cwd: Path, timeout: int | None
) -> AgentCommandResult:
    try:
        completed = subprocess.run(
            shlex.split(command),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return AgentCommandResult(
            command=command,
            returncode=124,
            stdout=(exc.stdout or "").decode("utf-8", errors="replace")[-4000:] if isinstance(exc.stdout, bytes) else (exc.stdout or "")[-4000:],
            stderr=f"Judge timed out after {timeout}s.",
            limit_reached=False,
            retry_after=None,
            limit_scope=None,
            limit_pattern_unmatched=True,
        )
    output = f"{completed.stdout}\n{completed.stderr}"
    limit_scope = classify_limit_scope(output)
    limit_reached = completed.returncode != 0 and limit_scope is not None
    return AgentCommandResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout[-4000:],
        stderr=completed.stderr[-4000:],
        limit_reached=limit_reached,
        retry_after=retry_after_for_scope(limit_scope) if limit_scope else None,
        limit_scope=limit_scope,
        limit_pattern_unmatched=completed.returncode != 0 and limit_scope is None,
    )

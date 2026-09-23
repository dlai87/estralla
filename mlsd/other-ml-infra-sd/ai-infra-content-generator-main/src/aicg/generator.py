"""File-based generation adapter for local Claude/Codex commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .agent_cli import AgentLimitReached, run_agent_command
from .source_registry import SourceRegistry
from .state import ensure_state_dir, state_path, utc_now, write_json, write_state

RUN_STATE = "run-state.json"


class GenerationNotConfigured(RuntimeError):
    def __init__(self, prompt_path: Path, output_dir: Path):
        self.prompt_path = prompt_path
        self.output_dir = output_dir
        super().__init__(
            "No generator command configured. Prompt packet was written for manual execution."
        )


def generate_from_plan(
    repo_path: Path,
    work_plan: dict[str, Any],
    module: str | None = None,
    work_id: str | None = None,
    config_paths: list[Path] | None = None,
    registry: SourceRegistry | None = None,
    command_override: str | None = None,
) -> dict[str, Any]:
    item = select_work_item(work_plan, module=module, work_id=work_id)
    if item is None:
        raise ValueError("No matching work item was found.")

    registry = registry or SourceRegistry.load()
    state_dir = ensure_state_dir(repo_path)
    prompt_dir = state_dir / "prompts"
    output_dir = state_dir / "generated" / item["id"]
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = prompt_dir / f"{item['id']}.md"
    prompt_path.write_text(build_prompt_packet(item, registry), encoding="utf-8")

    command = command_override or load_generator_command(repo_path, config_paths or [])
    run_state = {
        "schema_version": 1,
        "updated_at": utc_now(),
        "repo": work_plan["repo"]["name"],
        "work_id": item["id"],
        "prompt_path": str(prompt_path),
        "output_dir": str(output_dir),
        "status": "prompt_ready",
    }
    write_state(repo_path, RUN_STATE, run_state)

    if not command:
        raise GenerationNotConfigured(prompt_path=prompt_path, output_dir=output_dir)

    formatted = command.format(
        prompt=str(prompt_path),
        output_dir=str(output_dir),
        repo=str(repo_path),
        work_id=item["id"],
        runner=str(Path(__file__).resolve().parents[2]),
    )
    result = run_agent_command(formatted, cwd=repo_path)
    if result.limit_reached:
        run_state.update(
            {
                "status": "agent_limit_reached",
                "deferred": True,
                "command": result.command,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "limit_scope": result.limit_scope,
                "retry_after": result.retry_after,
                "updated_at": utc_now(),
            }
        )
        write_json(state_path(repo_path, RUN_STATE), run_state)
        raise AgentLimitReached(result)

    run_state.update(
        {
            "status": "generated" if result.returncode == 0 else "generator_failed",
            "command": result.command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "limit_pattern_unmatched": result.limit_pattern_unmatched,
            "updated_at": utc_now(),
        }
    )
    write_json(state_path(repo_path, RUN_STATE), run_state)
    if result.returncode != 0:
        raise RuntimeError(f"Generator command failed with exit code {result.returncode}.")
    return run_state


def select_work_item(
    work_plan: dict[str, Any],
    module: str | None = None,
    work_id: str | None = None,
) -> dict[str, Any] | None:
    """Look up a work item in the plan.

    Searches ``work_items`` first, then ``backlog_items`` — the org
    work-queue can promote backlog (e.g. ``exercise_depth_followup``)
    items to ready, but the per-repo plan still keeps them in the
    backlog list. This used to raise 'No matching work item was found.'
    """
    pools = (
        work_plan.get("work_items", []),
        work_plan.get("backlog_items", []),
    )
    for pool in pools:
        for item in pool:
            if work_id and item["id"] != work_id:
                continue
            if module and item.get("module") != module:
                continue
            return item
    return None


def generate_all_pending(
    repo_path: Path,
    work_plan: dict[str, Any],
    module: str | None = None,
    config_paths: list[Path] | None = None,
    registry: SourceRegistry | None = None,
    command_override: str | None = None,
) -> dict[str, Any]:
    """Drain every pending work item in ``work_plan`` in order.

    Stops early if the agent reports a subscription limit and surfaces
    the partial result. Verification of each generated artifact is the
    caller's responsibility — typically ``aicg run`` calls
    ``verify_repo`` after this returns.
    """
    pending = [
        item
        for item in work_plan.get("work_items", [])
        if item.get("status") in {"planned", "prompt_ready", "verification_failed"}
        and (module is None or item.get("module") == module)
    ]
    results: list[dict[str, Any]] = []
    deferred: dict[str, Any] | None = None
    for item in pending:
        try:
            state = generate_from_plan(
                repo_path,
                work_plan,
                module=module,
                work_id=item["id"],
                config_paths=config_paths,
                registry=registry,
                command_override=command_override,
            )
        except AgentLimitReached as exc:
            deferred = {
                "work_id": item["id"],
                "limit_scope": exc.result.limit_scope,
                "retry_after": exc.result.retry_after,
            }
            break
        except GenerationNotConfigured:
            raise
        results.append(state)
    return {
        "schema_version": 1,
        "completed_count": len(results),
        "pending_count": len(pending),
        "deferred": deferred,
        "items": results,
    }


def build_prompt_packet(work_item: dict[str, Any], registry: SourceRegistry) -> str:
    source_ids = work_item.get("source_policy", {}).get("required_default_sources", [])
    source_lines = []
    for source_id in source_ids:
        source = registry.get(source_id)
        if source is None:
            continue
        source_lines.append(f"- `{source.id}` ({source.authority}): {source.name} - {source.url}")

    exercise_lines = []
    for exercise in work_item.get("exercises", []):
        exercise_lines.append(
            "\n".join(
                [
                    f"### {exercise['exercise_id']} - {exercise.get('title', exercise['exercise_id'])}",
                    f"- Learning file: `{exercise['learning_path']}`",
                    f"- Output directory: `{exercise['expected_solution_dir']}`",
                    "- Required artifact: `SOLUTION.md`",
                ]
            )
        )

    # Work items either target a module (module_solution_gap) or a
    # project (project_solution_gap); refresh items target a path. Use
    # whichever locator is present so we don't crash on KeyError.
    scope_label = (
        f"module `{work_item['module']}`"
        if work_item.get("module")
        else f"project `{work_item['project']}`"
        if work_item.get("project")
        else f"path `{work_item.get('path', '?')}`"
    )
    is_depth_followup = work_item.get("type") == "exercise_depth_followup"
    if is_depth_followup:
        goal_lead = (
            "Split the existing module-level SOLUTION.md into per-exercise "
            "SOLUTION.md files. The module-level file already covers the "
            "rationale; your job is to factor it into the per-exercise "
            "directories listed below WITHOUT inventing new content. Keep "
            "the module-level file as a high-level index"
        )
    elif work_item.get("module"):
        goal_lead = "Create module-level reference solutions"
    elif work_item.get("project"):
        goal_lead = "Author the project solution artifact"
    else:
        goal_lead = "Refresh the artifact below"

    return (
        f"# AICG Work Packet: {work_item['id']}\n\n"
        f"## Goal\n\n"
        f"{goal_lead} for `{work_item['repo']}` {scope_label}.\n\n"
        "## Scope\n\n"
        "- Modify only the target solutions repository.\n"
        "- Create one directory per learning exercise under the module solution directory.\n"
        "- Each exercise directory must contain `SOLUTION.md`.\n"
        "- Design exercises need a worked example, decision rationale, and grading rubric.\n"
        "- Implementation exercises need runnable or statically valid artifacts where feasible.\n\n"
        "## Source Policy\n\n"
        "- Use official standards and project documentation first.\n"
        "- VeriSwarm references may only be used as practitioner implementation examples.\n"
        "- Do not invent facts, metrics, incidents, or case studies.\n"
        "- If a factual claim cannot be verified, write `<!-- needs-research: ... -->`; this blocks auto-merge.\n\n"
        + ("\n".join(source_lines) if source_lines else "- No default sources matched this work item.")
        + "\n\n"
        "## Exercises\n\n"
        + "\n\n".join(exercise_lines)
        + "\n\n"
        "## Output Contract\n\n"
        "For every exercise, write a `SOLUTION.md` with these sections:\n\n"
        "1. Solution overview\n"
        "2. Worked answer or implementation\n"
        "3. Validation steps\n"
        "4. Rubric or review checklist\n"
        "5. Common mistakes\n"
        "6. References\n\n"
        "Keep claims tied to the listed official sources or to clearly labeled local exercise context.\n"
    )


def load_generator_command(repo_path: Path, config_paths: list[Path]) -> str | None:
    """Locate the configured generator command for ``repo_path``.

    The runner first looks beside the target repo (``aicg.yaml`` /
    ``aicg.yml`` / ``aicg.json``) and then falls through to any
    additional configs supplied via the CLI. Files can be JSON or YAML;
    the loader is tolerant of both.
    """
    from .config_loader import ConfigError, load_config

    candidate_paths = [
        repo_path / "aicg.yaml",
        repo_path / "aicg.yml",
        repo_path / "aicg.json",
        *config_paths,
    ]
    for path in candidate_paths:
        if not path.exists():
            continue
        try:
            parsed = load_config(path)
        except ConfigError:
            continue
        if not isinstance(parsed, dict):
            continue
        command = parsed.get("generator_command") or parsed.get("agent_command")
        if command:
            return str(command)
    return None

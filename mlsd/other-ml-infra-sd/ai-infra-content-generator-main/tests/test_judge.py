from __future__ import annotations

import json
import textwrap
from pathlib import Path

from conftest import make_security_workspace, write_file, write_minimal_manifest

from aicg.judge import JudgeConfig, parse_judge_response


SOLUTION_TEMPLATE = textwrap.dedent(
    """\
    # Threat model exercise solution

    ## Overview
    Walkthrough.

    ## Implementation
    Steps.

    ## Validation
    Run pytest.

    ## Rubric
    Graded.

    ## Common mistakes
    Listed.

    ## References
    - https://www.nist.gov/itl/ai-risk-management-framework
    """
)


def _enable_judge(manifest_path: Path, agent_command: str) -> None:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["quality_judge"]["enabled"] = True
    payload["quality_judge"]["agent_command"] = agent_command
    payload["quality_judge"]["thresholds"] = {"default": 70}
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _plan_with_action(solutions: Path) -> dict:
    target = (
        "modules/mod-001-ml-security-foundations/"
        "exercise-01-threat-model/SOLUTION.md"
    )
    return {
        "schema_version": 2,
        "repo": {"name": "ai-infra-security-solutions", "path": str(solutions)},
        "work_items": [
            {
                "id": "fill-mod-001-ml-security-foundations-solutions",
                "type": "module_solution_gap",
                "repo": "ai-infra-security-solutions",
                "module": "mod-001-ml-security-foundations",
                "status": "generated",
                "source_policy": {"required_default_sources": []},
                "exercises": [],
                "actions": [{"type": "write_solution", "path": target}],
            }
        ],
    }


def _write_plan(solutions: Path, plan: dict) -> Path:
    state = solutions / ".aicg"
    state.mkdir(parents=True, exist_ok=True)
    plan_path = state / "work-plan.json"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return plan_path


def test_judge_config_disabled_by_default(tmp_path: Path) -> None:
    from aicg.org_config import load_manifest

    manifest = load_manifest(write_minimal_manifest(tmp_path / "aicg-org.yaml"))
    config = JudgeConfig.from_manifest(manifest)
    assert config.enabled is False
    assert config.threshold_for("module_solution_gap") == 70


def test_parse_judge_response_accepts_fenced_json() -> None:
    config = JudgeConfig(
        enabled=True,
        agent_command="",
        dimensions=("correctness", "clarity", "source_quality", "depth"),
        thresholds={"default": 70},
        timeout_seconds=None,
    )
    raw = textwrap.dedent(
        """\
        Here is the verdict:

        ```json
        {
          "total": 82,
          "dimensions": {
            "correctness": 22,
            "clarity": 20,
            "source_quality": 20,
            "depth": 20
          },
          "blockers": [],
          "summary": "Solid solution."
        }
        ```
        """
    )
    verdict = parse_judge_response(raw, config, threshold=70)
    assert verdict.score == 82
    assert verdict.passed is True
    assert verdict.dimensions["correctness"] == 22


def test_parse_judge_response_blockers_force_failure() -> None:
    config = JudgeConfig(
        enabled=True,
        agent_command="",
        dimensions=("correctness", "clarity"),
        thresholds={"default": 50},
        timeout_seconds=None,
    )
    raw = json.dumps(
        {
            "total": 90,
            "dimensions": {"correctness": 45, "clarity": 45},
            "blockers": ["citation fabricated"],
            "summary": "High score but fabricated citation.",
        }
    )
    verdict = parse_judge_response(raw, config, threshold=50)
    assert verdict.score == 90
    assert verdict.passed is False
    assert "fabricated" in verdict.blockers[0]


def test_parse_judge_response_handles_garbage() -> None:
    config = JudgeConfig(
        enabled=True,
        agent_command="",
        dimensions=("correctness",),
        thresholds={"default": 70},
        timeout_seconds=None,
    )
    verdict = parse_judge_response("not json", config, threshold=70)
    assert verdict.score == 0
    assert not verdict.passed
    assert any("did not contain a JSON" in b for b in verdict.blockers)


def _make_judge_script(tmp_path: Path, payload: dict, exit_code: int = 0) -> Path:
    script = tmp_path / "fake-judge.sh"
    body = json.dumps(payload)
    script.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        'while [[ $# -gt 0 ]]; do\n'
        '  case "$1" in\n'
        '    --output-dir) OUT="$2"; shift 2 ;;\n'
        '    *) shift ;;\n'
        '  esac\n'
        "done\n"
        'mkdir -p "$OUT"\n'
        f"cat > \"$OUT/response.json\" <<'EOF'\n{body}\nEOF\n"
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


def test_verify_blocks_when_judge_scores_below_threshold(tmp_path: Path) -> None:
    from aicg.org_config import load_manifest
    from aicg.verify import verify_repo

    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"
    write_file(
        solutions
        / "modules"
        / "mod-001-ml-security-foundations"
        / "exercise-01-threat-model"
        / "SOLUTION.md",
        SOLUTION_TEMPLATE,
    )
    _write_plan(solutions, _plan_with_action(solutions))

    manifest_path = write_minimal_manifest(tmp_path / "aicg-org.yaml")
    judge_script = _make_judge_script(
        tmp_path,
        {
            "total": 40,
            "dimensions": {
                "correctness": 10,
                "clarity": 10,
                "source_quality": 10,
                "depth": 10,
            },
            "blockers": [],
            "summary": "Below threshold.",
        },
    )
    _enable_judge(
        manifest_path,
        f"{judge_script} --output-dir {{output_dir}}",
    )
    manifest = load_manifest(manifest_path)
    judge_config = JudgeConfig.from_manifest(manifest)

    report = verify_repo(
        workspace,
        "ai-infra-security-solutions",
        judge_config=judge_config,
    )

    assert report["status"] == "verification_failed"
    quality = report["work_items"][0]["actions"][0]["quality"]
    assert quality is not None
    assert quality["passed"] is False
    assert quality["score"] == 40


def test_verify_passes_when_judge_scores_above_threshold(tmp_path: Path) -> None:
    from aicg.org_config import load_manifest
    from aicg.verify import verify_repo

    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"
    write_file(
        solutions
        / "modules"
        / "mod-001-ml-security-foundations"
        / "exercise-01-threat-model"
        / "SOLUTION.md",
        SOLUTION_TEMPLATE,
    )
    _write_plan(solutions, _plan_with_action(solutions))

    manifest_path = write_minimal_manifest(tmp_path / "aicg-org.yaml")
    judge_script = _make_judge_script(
        tmp_path,
        {
            "total": 88,
            "dimensions": {
                "correctness": 22,
                "clarity": 22,
                "source_quality": 22,
                "depth": 22,
            },
            "blockers": [],
            "summary": "Solid solution.",
        },
    )
    _enable_judge(
        manifest_path,
        f"{judge_script} --output-dir {{output_dir}}",
    )
    manifest = load_manifest(manifest_path)
    judge_config = JudgeConfig.from_manifest(manifest)

    report = verify_repo(
        workspace,
        "ai-infra-security-solutions",
        judge_config=judge_config,
    )

    assert report["status"] == "verified"
    quality = report["work_items"][0]["actions"][0]["quality"]
    assert quality["passed"] is True
    assert quality["score"] == 88


def test_verify_skips_judge_when_config_disabled(tmp_path: Path) -> None:
    from aicg.verify import verify_repo

    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"
    write_file(
        solutions
        / "modules"
        / "mod-001-ml-security-foundations"
        / "exercise-01-threat-model"
        / "SOLUTION.md",
        SOLUTION_TEMPLATE,
    )
    _write_plan(solutions, _plan_with_action(solutions))

    # judge_config=None means structural-only verify.
    report = verify_repo(
        workspace,
        "ai-infra-security-solutions",
        judge_config=None,
    )

    assert report["status"] == "verified"
    assert report["work_items"][0]["actions"][0]["quality"] is None


def test_verify_records_judge_blockers_as_failure(tmp_path: Path) -> None:
    from aicg.org_config import load_manifest
    from aicg.verify import verify_repo

    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"
    write_file(
        solutions
        / "modules"
        / "mod-001-ml-security-foundations"
        / "exercise-01-threat-model"
        / "SOLUTION.md",
        SOLUTION_TEMPLATE,
    )
    _write_plan(solutions, _plan_with_action(solutions))

    manifest_path = write_minimal_manifest(tmp_path / "aicg-org.yaml")
    judge_script = _make_judge_script(
        tmp_path,
        {
            "total": 95,
            "dimensions": {
                "correctness": 25,
                "clarity": 25,
                "source_quality": 20,
                "depth": 25,
            },
            "blockers": ["citation appears fabricated"],
            "summary": "High score but fabricated citation.",
        },
    )
    _enable_judge(
        manifest_path,
        f"{judge_script} --output-dir {{output_dir}}",
    )
    manifest = load_manifest(manifest_path)
    judge_config = JudgeConfig.from_manifest(manifest)

    report = verify_repo(
        workspace,
        "ai-infra-security-solutions",
        judge_config=judge_config,
    )

    assert report["status"] == "verification_failed"
    quality = report["work_items"][0]["actions"][0]["quality"]
    assert quality["score"] == 95
    assert quality["passed"] is False
    assert any("fabricated" in b for b in quality["blockers"])

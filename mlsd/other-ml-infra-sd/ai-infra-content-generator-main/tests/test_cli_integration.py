from __future__ import annotations

import json

from conftest import make_security_workspace, write_file

from aicg.cli import main
from aicg.validator import check_curriculum_file_format


def test_cli_audit_plan_validate_report_only(tmp_path, capsys):
    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"

    assert (
        main(
            [
                "audit",
                "--workspace",
                str(workspace),
                "--repo",
                "ai-infra-security-solutions",
            ]
        )
        == 0
    )
    assert (solutions / ".aicg" / "audit-report.json").exists()

    assert main(["plan", "--workspace", str(workspace), "--repo", "ai-infra-security-solutions"]) == 0
    plan = json.loads((solutions / ".aicg" / "work-plan.json").read_text(encoding="utf-8"))
    assert plan["work_item_count"] == 1

    assert (
        main(
            [
                "validate",
                "--workspace",
                str(workspace),
                "--repo",
                "ai-infra-security-solutions",
                "--report-only",
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "Validation failed" in output
    assert (solutions / ".aicg" / "validation-report.json").exists()


def test_cli_generate_writes_prompt_when_agent_is_not_configured(tmp_path):
    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"
    assert main(["plan", "--workspace", str(workspace), "--repo", "ai-infra-security-solutions"]) == 0

    rc = main(
        [
            "generate",
            "--workspace",
            str(workspace),
            "--repo",
            "ai-infra-security-solutions",
            "--module",
            "mod-001-ml-security-foundations",
        ]
    )

    assert rc == 2
    prompt = (
        solutions
        / ".aicg"
        / "prompts"
        / "fill-mod-001-ml-security-foundations-solutions.md"
    )
    assert prompt.exists()
    assert "official standards" in prompt.read_text(encoding="utf-8")


def test_curriculum_file_format_detects_broken_root_table(tmp_path):
    repo = tmp_path / "repo"
    write_file(
        repo / "CURRICULUM.md",
        "# Curriculum\n\n| Skill | Module |\n|---|---|\n| Python |\n",
    )

    check = check_curriculum_file_format(repo)

    assert check["status"] == "fail"
    assert check["findings"][0]["message"] == "Markdown table row has a different column count."

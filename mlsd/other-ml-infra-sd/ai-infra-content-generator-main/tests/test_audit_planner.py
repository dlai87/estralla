from __future__ import annotations

from conftest import make_security_workspace, write_file

from aicg.audit import audit_repo, scan_placeholders
from aicg.planner import plan_from_audit


def test_audit_detects_missing_module_level_solution_parity(tmp_path):
    workspace = make_security_workspace(tmp_path)

    report = audit_repo(workspace, "ai-infra-security-solutions", write_report=False)

    assert report["summary"]["status"] == "fail"
    assert report["modules"][0]["module_id"] == "mod-001-ml-security-foundations"
    assert report["modules"][0]["missing_solution_count"] == 1
    assert any(gap["type"] == "missing_solution_module" for gap in report["gaps"])
    assert any(gap["type"] == "missing_exercise_solution" for gap in report["gaps"])


def test_plan_groups_missing_exercise_solutions_by_module(tmp_path):
    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"
    report = audit_repo(workspace, "ai-infra-security-solutions", write_report=False)

    plan = plan_from_audit(report, repo_path=solutions)

    assert plan["work_item_count"] == 1
    item = plan["work_items"][0]
    assert item["id"] == "fill-mod-001-ml-security-foundations-solutions"
    assert item["module"] == "mod-001-ml-security-foundations"
    assert item["exercises"][0]["exercise_id"] == "exercise-01"
    # The planner preserves the slug from the learning-side filename so
    # the generated solution lands beside its peer exercise content.
    assert item["actions"][-1]["path"].endswith(
        "/exercise-01-threat-model/SOLUTION.md"
    )


def test_module_level_solution_satisfies_audit(tmp_path):
    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"

    # Author a module-level SOLUTION.md but no exercise-level artifact.
    write_file(
        solutions
        / "modules"
        / "mod-001-ml-security-foundations"
        / "SOLUTION.md",
        "# Module Solution\n\nDesign rationale for the module.\n",
    )

    report = audit_repo(workspace, "ai-infra-security-solutions", write_report=False)

    module = report["modules"][0]
    assert module["has_module_rationale"] is True
    assert module["status"] == "module_rationale_only"
    # No error-severity gap because the rationale covers the module.
    assert report["summary"]["error_count"] == 0
    # The exercise is flagged as "could go deeper" — a warning, not error.
    assert any(
        gap["type"] == "exercise_solution_module_level_only"
        for gap in report["gaps"]
    )


def test_audit_finds_slug_bearing_exercise_dir(tmp_path):
    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"

    # Author a SOLUTION.md inside the slug-bearing directory that real
    # solutions repos use (e.g. ``exercise-01-threat-model/``).
    write_file(
        solutions
        / "modules"
        / "mod-001-ml-security-foundations"
        / "exercise-01-threat-model"
        / "SOLUTION.md",
        "# Threat Model Solution\n",
    )

    report = audit_repo(workspace, "ai-infra-security-solutions", write_report=False)

    module = report["modules"][0]
    assert module["status"] == "ok"
    assert module["exercises"][0]["status"] == "ok"
    assert module["exercises"][0]["found_artifact"].endswith(
        "exercise-01-threat-model/SOLUTION.md"
    )


def test_audit_accepts_alternative_exercise_artifacts(tmp_path):
    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"

    # README.md counts as a valid exercise solution artifact too —
    # several solutions repos use README.md + STEP_BY_STEP.md instead of
    # SOLUTION.md.
    write_file(
        solutions
        / "modules"
        / "mod-001-ml-security-foundations"
        / "exercise-01-threat-model"
        / "README.md",
        "# Threat Model Walkthrough\n\nSteps...\n",
    )

    report = audit_repo(workspace, "ai-infra-security-solutions", write_report=False)

    assert report["modules"][0]["exercises"][0]["status"] == "ok"
    assert report["summary"]["error_count"] == 0


def test_audit_skips_aicg_state_dir_in_placeholder_scan(tmp_path):
    repo = tmp_path / "repo"
    # An AICG-generated prompt packet that mentions ``needs-research``
    # in instructions — must not be flagged as a real marker.
    write_file(
        repo / ".aicg" / "prompts" / "fake-work.md",
        "# Prompt\n\nIf you can't verify, write `needs-research` marker.\n",
    )
    write_file(
        repo / "modules" / "README.md",
        "# Modules\n",
    )

    findings = scan_placeholders(repo)

    # The placeholder scanner should walk past .aicg/ entirely.
    assert all(".aicg" not in finding.get("path", "") for finding in findings)


def test_audit_skips_archive_dir(tmp_path):
    repo = tmp_path / "repo"
    write_file(
        repo / "_archive" / "old-scaffold.md",
        "# Old\n\nTODO: rewrite\n",
    )
    write_file(repo / "modules" / "README.md", "# Modules\n")

    findings = scan_placeholders(repo)

    assert all("_archive" not in finding.get("path", "") for finding in findings)


def test_placeholder_cache_reuses_results_until_file_changes(tmp_path):
    from aicg.audit import PlaceholderCache, scan_placeholders

    repo = tmp_path / "repo"
    target = repo / "modules" / "mod-001" / "exercise-01" / "README.md"
    write_file(
        target,
        "# Exercise\n\n# manual-review needed before publish\n",
    )

    cache = PlaceholderCache(repo)
    findings_first = scan_placeholders(repo, cache=cache)
    cache_path = cache.save()
    assert cache_path is not None
    assert any(item["type"] == "manual_review" for item in findings_first)

    # Second invocation with the same cache reads from disk and should
    # avoid scanning unchanged files. We can detect this by mutating
    # the file in-place after the cache was populated and confirming
    # the cache picks up the new marker only after the mtime changes.
    cache_again = PlaceholderCache(repo)
    findings_unchanged = scan_placeholders(repo, cache=cache_again)
    assert findings_unchanged == findings_first

    # Touch the file with a newer marker. The cache should detect the
    # mtime change and rescan.
    import os

    write_file(
        target,
        "# Exercise\n\n<!-- needs-research: replacement -->\n",
    )
    os.utime(target, None)  # bump mtime explicitly on filesystems with low resolution
    cache_after = PlaceholderCache(repo)
    findings_after = scan_placeholders(repo, cache=cache_after)
    assert any(item["type"] == "needs_research" for item in findings_after)
    assert not any(item["type"] == "manual_review" for item in findings_after)


def test_audit_flags_missing_project_solution(tmp_path):
    workspace = make_security_workspace(tmp_path)
    learning = workspace / "ai-infra-security-learning"
    write_file(
        learning / "projects" / "project-1-zero-trust" / "README.md",
        "# Project 1 — Zero Trust\n\nCapstone description.\n",
    )

    report = audit_repo(workspace, "ai-infra-security-solutions", write_report=False)

    assert report["summary"]["project_count"] == 1
    assert report["projects"][0]["project_id"] == "project-1-zero-trust"
    assert report["projects"][0]["status"] == "gap"
    assert any(
        gap["type"] == "missing_solution_project" for gap in report["gaps"]
    )


def test_audit_recognises_project_solution_with_readme(tmp_path):
    workspace = make_security_workspace(tmp_path)
    learning = workspace / "ai-infra-security-learning"
    solutions = workspace / "ai-infra-security-solutions"
    write_file(
        learning / "projects" / "project-1-zero-trust" / "README.md",
        "# Project 1 — Zero Trust\n",
    )
    write_file(
        solutions / "projects" / "project-1-zero-trust" / "README.md",
        "# Solution walkthrough\n",
    )

    report = audit_repo(workspace, "ai-infra-security-solutions", write_report=False)

    assert report["projects"][0]["status"] == "ok"
    assert report["projects"][0]["found_artifact"].endswith(
        "project-1-zero-trust/README.md"
    )


def test_plan_emits_project_work_item(tmp_path):
    workspace = make_security_workspace(tmp_path)
    solutions = workspace / "ai-infra-security-solutions"
    learning = workspace / "ai-infra-security-learning"
    write_file(
        learning / "projects" / "project-1-zero-trust" / "README.md",
        "# Project 1\n",
    )

    report = audit_repo(workspace, "ai-infra-security-solutions", write_report=False)
    plan = plan_from_audit(report, repo_path=solutions)

    project_work = next(
        (item for item in plan["work_items"] if item["type"] == "project_solution_gap"),
        None,
    )
    assert project_work is not None
    assert project_work["id"] == "fill-project-1-zero-trust-solution"
    assert project_work["actions"][-1]["path"].endswith(
        "projects/project-1-zero-trust/SOLUTION.md"
    )


def test_placeholder_scan_flags_manual_review_and_needs_research(tmp_path):
    repo = tmp_path / "repo"
    write_file(
        repo / "modules" / "mod-001" / "exercise-01" / "SOLUTION.md",
        "# Solution\n\n# manual-review\n\n<!-- needs-research: verify source -->\n",
    )

    findings = scan_placeholders(repo)

    assert {finding["type"] for finding in findings} >= {"manual_review", "needs_research"}
    assert all(finding["severity"] == "error" for finding in findings)

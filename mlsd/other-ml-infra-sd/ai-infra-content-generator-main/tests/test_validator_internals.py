from __future__ import annotations

import textwrap
from pathlib import Path

from conftest import write_file

from aicg.audit import (
    audit_solution_sources,
    gap as audit_gap,
)
from aicg.source_registry import Source, SourceRegistry
from aicg.validator import check_curriculum_file_format, validate_markdown_tables


def _registry() -> SourceRegistry:
    return SourceRegistry(
        sources=[
            Source(
                id="nist-ai-rmf",
                name="NIST AI RMF",
                url="https://www.nist.gov/itl/ai-risk-management-framework",
                authority="official_standard",
                topics=("governance",),
                fit="",
            ),
            Source(
                id="veriswarm-trust-center",
                name="VeriSwarm Trust Center",
                url="https://veriswarm.example.com/docs",
                authority="practitioner_reference",
                topics=("governance",),
                fit="",
            ),
        ],
        last_verified="2026-05-24",
    )


def test_audit_solution_sources_flags_practitioner_without_official(tmp_path: Path) -> None:
    solution = write_file(
        tmp_path / "solution.md",
        "# Solution\n\nSee https://veriswarm.example.com/docs/page for context.\n",
    )

    findings = audit_solution_sources(
        solution,
        repo_path=tmp_path,
        module_id="mod-001",
        exercise_id="exercise-01",
        registry=_registry(),
    )

    types = {item["type"] for item in findings}
    assert "practitioner_reference_without_official_source" in types
    assert all(item["severity"] == "warning" for item in findings)


def test_audit_solution_sources_accepts_official_alongside_practitioner(tmp_path: Path) -> None:
    solution = write_file(
        tmp_path / "solution.md",
        textwrap.dedent(
            """\
            # Solution

            Reference architecture follows the NIST AI RMF.
            See https://www.nist.gov/itl/ai-risk-management-framework for the
            primary control framework. The team also reviewed
            https://veriswarm.example.com/docs/page for implementation
            patterns.
            """
        ),
    )

    findings = audit_solution_sources(
        solution,
        repo_path=tmp_path,
        module_id="mod-001",
        exercise_id="exercise-01",
        registry=_registry(),
    )

    assert findings == []


def test_audit_solution_sources_warns_when_substantial_text_has_no_urls(tmp_path: Path) -> None:
    # Threshold inside audit_solution_sources is 250 words.
    body = ("placeholder content. " * 200).strip()
    solution = write_file(tmp_path / "solution.md", f"# Solution\n\n{body}\n")

    findings = audit_solution_sources(
        solution,
        repo_path=tmp_path,
        module_id="mod-001",
        exercise_id="exercise-01",
        registry=_registry(),
    )

    assert any(item["type"] == "missing_source_references" for item in findings)


def test_audit_gap_helper_drops_none_values() -> None:
    payload = audit_gap("missing_thing", "error", "msg", extra=None, other="value")
    assert "extra" not in payload
    assert payload["other"] == "value"


def test_validate_markdown_tables_accepts_well_formed_table(tmp_path: Path) -> None:
    text = textwrap.dedent(
        """\
        # Title

        | Col A | Col B |
        |-------|-------|
        | a1    | b1    |
        | a2    | b2    |
        """
    )
    path = write_file(tmp_path / "doc.md", text)
    findings = validate_markdown_tables(path, tmp_path, text.splitlines())
    assert findings == []


def test_validate_markdown_tables_flags_column_mismatch(tmp_path: Path) -> None:
    text = textwrap.dedent(
        """\
        | Col A | Col B |
        |-------|-------|
        | a1    | b1    |
        | a2    |
        """
    )
    path = write_file(tmp_path / "doc.md", text)
    findings = validate_markdown_tables(path, tmp_path, text.splitlines())
    assert any(
        finding["message"] == "Markdown table row has a different column count."
        for finding in findings
    )


def test_validate_markdown_tables_flags_missing_separator(tmp_path: Path) -> None:
    text = textwrap.dedent(
        """\
        | Col A | Col B |
        | a1    | b1    |
        """
    )
    path = write_file(tmp_path / "doc.md", text)
    findings = validate_markdown_tables(path, tmp_path, text.splitlines())
    assert any(
        finding["message"]
        == "Markdown table is missing the |---|---| separator row after the header."
        for finding in findings
    )


def test_validate_markdown_tables_skips_code_blocks(tmp_path: Path) -> None:
    text = textwrap.dedent(
        """\
        # Title

        ```
        | this | is |
        | not  | a  | table |
        ```

        | Col A | Col B |
        |-------|-------|
        | a1    | b1    |
        """
    )
    path = write_file(tmp_path / "doc.md", text)
    findings = validate_markdown_tables(path, tmp_path, text.splitlines())
    assert findings == []


def test_validate_markdown_tables_supports_alignment_markers(tmp_path: Path) -> None:
    text = textwrap.dedent(
        """\
        | Col A | Col B | Col C |
        | :---- | :---: | ----: |
        | a1    | b1    | c1    |
        """
    )
    path = write_file(tmp_path / "doc.md", text)
    findings = validate_markdown_tables(path, tmp_path, text.splitlines())
    assert findings == []


def test_check_curriculum_file_format_passes_clean_readme(tmp_path: Path) -> None:
    write_file(tmp_path / "README.md", "# Title\n\nClean readme.\n")
    result = check_curriculum_file_format(tmp_path)
    assert result["status"] == "pass"

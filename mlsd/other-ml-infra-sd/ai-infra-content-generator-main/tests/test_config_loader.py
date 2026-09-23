from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from aicg.config_loader import ConfigError, load_config, parse_config


def test_parse_config_handles_json(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text('{"org": "AI-Infra", "roles": []}\n', encoding="utf-8")
    assert load_config(path) == {"org": "AI-Infra", "roles": []}


def test_parse_config_handles_mini_yaml() -> None:
    text = textwrap.dedent(
        """\
        org: AI-Infra-Curriculum
        default_remote: "git@github.com:org/{repo}.git"
        release:
          tag_format: v%Y.%m
          branch: main
        roles:
          - id: security
            title: AI Security Engineer
            level: 35
            learning_repo: ai-infra-security-learning
            solution_repo: ai-infra-security-solutions
          - id: engineer
            title: AI Engineer
            level: 25
            learning_repo: ai-infra-engineer-learning
            solution_repo: ai-infra-engineer-solutions
        automation:
          auto_merge: false
          max_daily_work_items: 1
        """
    )
    parsed = parse_config(text)
    assert parsed["org"] == "AI-Infra-Curriculum"
    assert parsed["release"]["tag_format"] == "v%Y.%m"
    assert parsed["release"]["branch"] == "main"
    assert len(parsed["roles"]) == 2
    assert parsed["roles"][0]["id"] == "security"
    assert parsed["roles"][0]["level"] == 35
    assert parsed["automation"]["auto_merge"] is False
    assert parsed["automation"]["max_daily_work_items"] == 1


def test_parse_config_supports_comments_and_blank_lines() -> None:
    text = textwrap.dedent(
        """\
        # Top-level comment
        org: AI-Infra

        # Roles list
        roles:
          - id: security
            level: 1
        """
    )
    parsed = parse_config(text)
    assert parsed == {"org": "AI-Infra", "roles": [{"id": "security", "level": 1}]}


def test_parse_config_quoted_strings_preserve_specials() -> None:
    text = 'agent_command: "{runner}/scripts/run.sh --prompt {prompt}"\n'
    parsed = parse_config(text)
    assert parsed == {"agent_command": "{runner}/scripts/run.sh --prompt {prompt}"}


def test_parse_config_rejects_malformed_input() -> None:
    with pytest.raises(ConfigError):
        parse_config("not a mapping or list")

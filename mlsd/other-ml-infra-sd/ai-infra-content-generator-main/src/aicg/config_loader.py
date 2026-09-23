"""Tolerant YAML+JSON config loader.

The runner ships without a hard dependency on ``pyyaml``. Most config
files in the curriculum (org manifest, ``aicg.yaml``) are short and use
a strict subset of YAML: scalars, lists, nested mappings, comments.
This module loads that subset deterministically and falls back to JSON
when content begins with ``{`` / ``[`` so the same loader can read both
formats transparently.

If ``pyyaml`` is installed in the environment the parser delegates to
it, which makes the loader future-proof for richer files without
forcing the dep on every install.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(RuntimeError):
    """Raised when a config file cannot be parsed."""


def load_config(path: Path) -> Any:
    """Load a YAML or JSON config file from ``path``."""
    text = path.read_text(encoding="utf-8")
    return parse_config(text, source=str(path))


def parse_config(text: str, source: str = "<config>") -> Any:
    stripped = text.lstrip()
    if not stripped:
        return {}
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"{source}: invalid JSON: {exc}") from exc

    # Prefer pyyaml if available — it handles every edge case correctly.
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        yaml = None  # type: ignore[assignment]

    if yaml is not None:
        try:
            loaded = yaml.safe_load(text) or {}
        except yaml.YAMLError as exc:  # type: ignore[union-attr]
            raise ConfigError(f"{source}: invalid YAML: {exc}") from exc
        if not isinstance(loaded, (dict, list)):
            raise ConfigError(
                f"{source}: top-level YAML must be a mapping or list; "
                f"got {type(loaded).__name__}."
            )
        return loaded

    return _parse_mini_yaml(text, source=source)


# ---------------------------------------------------------------------------
# Minimal YAML parser
# ---------------------------------------------------------------------------


@dataclass
class _Line:
    line_number: int
    indent: int
    raw: str
    content: str


def _tokenize(text: str) -> list[_Line]:
    tokens: list[_Line] = []
    for number, raw in enumerate(text.splitlines(), 1):
        stripped = raw.split("#", 1)[0].rstrip() if not _is_in_string(raw) else raw.rstrip()
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        tokens.append(_Line(line_number=number, indent=indent, raw=raw, content=stripped.strip()))
    return tokens


def _is_in_string(_raw: str) -> bool:
    # Comment-stripping for mini-YAML is intentionally simple. We assume
    # `#` outside of quoted strings is a comment, which is true for the
    # configs the runner consumes.
    return False


def _parse_mini_yaml(text: str, source: str) -> Any:
    tokens = _tokenize(text)
    if not tokens:
        return {}
    if tokens[0].content.startswith("- "):
        result, index = _parse_list(tokens, 0, tokens[0].indent, source)
    else:
        result, index = _parse_mapping(tokens, 0, tokens[0].indent, source)
    if index != len(tokens):
        leftover = tokens[index]
        raise ConfigError(
            f"{source}:{leftover.line_number}: unexpected indentation or content {leftover.content!r}"
        )
    return result


def _parse_mapping(
    tokens: list[_Line], start: int, indent: int, source: str
) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    index = start
    while index < len(tokens):
        token = tokens[index]
        if token.indent < indent:
            break
        if token.indent > indent:
            raise ConfigError(
                f"{source}:{token.line_number}: indentation jumped without a parent key"
            )
        if ":" not in token.content:
            raise ConfigError(
                f"{source}:{token.line_number}: expected 'key: value', got {token.content!r}"
            )
        key, _, value_part = token.content.partition(":")
        key = key.strip()
        value_part = value_part.strip()
        index += 1
        if value_part:
            result[key] = _parse_scalar(value_part)
            continue

        # Look ahead at the next token to see whether the value is a
        # nested mapping or list.
        if index >= len(tokens):
            result[key] = None
            continue
        next_token = tokens[index]
        if next_token.indent <= indent:
            result[key] = None
            continue
        child_indent = next_token.indent
        if next_token.content.startswith("- "):
            value, index = _parse_list(tokens, index, child_indent, source)
        else:
            value, index = _parse_mapping(tokens, index, child_indent, source)
        result[key] = value
    return result, index


def _parse_list(
    tokens: list[_Line], start: int, indent: int, source: str
) -> tuple[list[Any], int]:
    result: list[Any] = []
    index = start
    while index < len(tokens):
        token = tokens[index]
        if token.indent < indent:
            break
        if token.indent > indent:
            raise ConfigError(
                f"{source}:{token.line_number}: list items must align at indent {indent}"
            )
        if not token.content.startswith("- "):
            break
        body = token.content[2:].strip()
        index += 1
        if ":" in body and not body.startswith('"') and not body.startswith("'"):
            # Inline mapping entry like ``- key: value``. Build a one-key
            # mapping and continue collecting additional keys at the
            # nested indent level.
            key, _, value_part = body.partition(":")
            key = key.strip()
            value_part = value_part.strip()
            entry: dict[str, Any] = {}
            if value_part:
                entry[key] = _parse_scalar(value_part)
            elif index < len(tokens) and tokens[index].indent > indent:
                child_indent = tokens[index].indent
                if tokens[index].content.startswith("- "):
                    value, index = _parse_list(tokens, index, child_indent, source)
                else:
                    value, index = _parse_mapping(tokens, index, child_indent, source)
                entry[key] = value
            else:
                entry[key] = None
            # Continue collecting additional keys at the same level as
            # the first key of the inline mapping.
            while index < len(tokens):
                next_token = tokens[index]
                if next_token.indent <= indent or next_token.content.startswith("- "):
                    break
                if next_token.indent < indent + 2:
                    break
                if ":" not in next_token.content:
                    raise ConfigError(
                        f"{source}:{next_token.line_number}: expected key under list item"
                    )
                sub_key, _, sub_value = next_token.content.partition(":")
                sub_key = sub_key.strip()
                sub_value = sub_value.strip()
                index += 1
                if sub_value:
                    entry[sub_key] = _parse_scalar(sub_value)
                elif index < len(tokens) and tokens[index].indent > next_token.indent:
                    child_indent = tokens[index].indent
                    if tokens[index].content.startswith("- "):
                        value, index = _parse_list(tokens, index, child_indent, source)
                    else:
                        value, index = _parse_mapping(tokens, index, child_indent, source)
                    entry[sub_key] = value
                else:
                    entry[sub_key] = None
            result.append(entry)
        elif body:
            result.append(_parse_scalar(body))
        else:
            # Either a nested mapping or a nested list.
            if index < len(tokens) and tokens[index].indent > indent:
                child_indent = tokens[index].indent
                if tokens[index].content.startswith("- "):
                    value, index = _parse_list(tokens, index, child_indent, source)
                else:
                    value, index = _parse_mapping(tokens, index, child_indent, source)
                result.append(value)
            else:
                result.append(None)
    return result, index


_SCALAR_TRUE = {"true", "yes", "on"}
_SCALAR_FALSE = {"false", "no", "off"}
_SCALAR_NULL = {"null", "~", ""}


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return None
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    lowered = value.lower()
    if lowered in _SCALAR_TRUE:
        return True
    if lowered in _SCALAR_FALSE:
        return False
    if lowered in _SCALAR_NULL:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value

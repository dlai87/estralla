#!/usr/bin/env python3
"""Compatibility wrapper for the objective AICG validator.

The old lecture-note word-count standard has been retired. Completeness is now
based on learning/solution parity, required artifacts, source-backed claims,
placeholder markers, and runnable validation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aicg.inventory import default_workspace  # noqa: E402
from aicg.validator import validate_repo  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run objective AICG validation.")
    parser.add_argument("--workspace", type=Path, default=None)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--module", default=None)
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON.")
    parser.add_argument("--report-only", action="store_true", help="Always exit 0.")
    args = parser.parse_args(argv)

    workspace = (args.workspace or default_workspace(ROOT)).resolve()
    report = validate_repo(workspace, args.repo, module=args.module)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Validation {report['status']} for {args.repo}")
        for check in report["checks"]:
            print(f"- {check['name']}: {check['status']} ({check['finding_count']} finding(s))")
    return 0 if args.report_only or report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

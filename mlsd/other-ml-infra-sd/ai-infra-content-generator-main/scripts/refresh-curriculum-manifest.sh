#!/usr/bin/env bash
#
# Idempotent wrapper around scripts/build-curriculum-manifest.py.
#
# Re-walks the workspace and rewrites manifest/curriculum.manifest.json
# to match the current structural state. Safe to call from any pipeline
# step that mutates curriculum structure (steward, post-merge hooks,
# weekly audits).
#
# Usage:
#   refresh-curriculum-manifest.sh [--workspace PATH] [--out PATH]
#
# Defaults match the Python builder: workspace = parent of CWD,
# out = manifest/curriculum.manifest.json next to the script.
#
# Exits 0 if the manifest was rewritten successfully (regardless of
# whether it actually changed). Exits non-zero on any builder error.

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PYTHON="${PYTHON:-python3}"

# Prefer the repo's venv if it exists.
if [[ -x "$REPO_DIR/.venv/bin/python" ]]; then
  PYTHON="$REPO_DIR/.venv/bin/python"
fi

log() {
  printf '[%s] refresh-curriculum-manifest: %s\n' \
    "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*"
}

log "Running builder via $PYTHON"
"$PYTHON" "$SCRIPT_DIR/build-curriculum-manifest.py" "$@"
log "Done"

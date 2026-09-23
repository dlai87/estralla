#!/usr/bin/env bash
set -euo pipefail

# claude is typically installed under ~/.local/bin which is in
# interactive PATH but not in subprocess PATH inherited from ssh or
# systemd. Make the wrapper self-sufficient.
export PATH="${HOME}/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Research wrapper: sibling of run-claude-content.sh but with web tools
# enabled because research requires fetching live job postings, vendor
# docs, and industry references. The agent must end up writing the
# files listed in the prompt's Output Contract:
#
#   - JOB_REQUIREMENTS.md
#   - .aicg/job-requirements.json
#   - .aicg/curriculum-plan-delta.json
#
# It does NOT write the prompt's response.md (used by content gen);
# the runner's verifier checks for the contract files directly.

MODEL="claude-opus-4-7"
PROMPT=""
OUTPUT_DIR=""
REPO=""
WORK_ID=""

usage() {
  cat <<EOF
Usage: $(basename "$0") --prompt PATH --output-dir DIR --repo PATH [OPTIONS]

Options:
  --model NAME       Claude model. Default: claude-opus-4-7.
  --repo PATH        Target learning-repo path (the agent's working root).
  --work-id ID       AICG work item id ('research:<role>').
  -h, --help         Show this help.

Web tools (WebFetch, WebSearch) are allowed in addition to the
content-generation tool list.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)        MODEL="${2:-}";        shift 2 ;;
    --prompt)       PROMPT="${2:-}";       shift 2 ;;
    --output-dir)   OUTPUT_DIR="${2:-}";   shift 2 ;;
    --repo)         REPO="${2:-}";         shift 2 ;;
    --work-id)      WORK_ID="${2:-}";      shift 2 ;;
    -h|--help)      usage; exit 0 ;;
    *)              echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ -f "$PROMPT" ]] || { echo "Prompt not found: $PROMPT" >&2; exit 2; }
[[ -n "$OUTPUT_DIR" ]] || { echo "--output-dir is required" >&2; exit 2; }
[[ -n "$REPO" && -d "$REPO" ]] || { echo "--repo path missing or not a directory: $REPO" >&2; exit 2; }
command -v claude >/dev/null || { echo "claude CLI not found in PATH" >&2; exit 127; }

mkdir -p "$OUTPUT_DIR"
{
  echo "model=$MODEL"
  echo "repo=$REPO"
  echo "work_id=$WORK_ID"
  echo "prompt=$PROMPT"
  date '+started_at=%Y-%m-%dT%H:%M:%S%z'
} >"$OUTPUT_DIR/research-run.env"

# Unattended permission profile + web tools for research.
# Single space-separated string — claude greedily consumes positional
# args after --allowedTools, so an array form swallows the prompt.
ALLOWED_TOOLS="Edit Write Read Glob Grep WebFetch WebSearch Bash(mkdir:*) Bash(ls:*) Bash(cat:*) Bash(git status:*) Bash(git diff:*)"

cd "$REPO"
# Prompt via stdin so positional-arg parsing can't mangle it.
claude \
  --model "$MODEL" \
  --print \
  --permission-mode acceptEdits \
  --add-dir "$REPO" \
  --allowedTools "$ALLOWED_TOOLS" \
  <"$PROMPT" \
  >"$OUTPUT_DIR/response.md"

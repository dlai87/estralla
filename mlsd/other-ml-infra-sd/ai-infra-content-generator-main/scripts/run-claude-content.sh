#!/usr/bin/env bash
set -euo pipefail

# claude / codex are typically installed under ~/.local/bin which is
# in interactive PATH but not in subprocess PATH inherited from ssh
# or systemd. Make the wrapper self-sufficient.
export PATH="${HOME}/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

MODEL="claude-opus-4-7"
PROMPT=""
OUTPUT_DIR=""
REPO=""
WORK_ID=""

usage() {
  cat <<EOF
Usage: $(basename "$0") --prompt PATH --output-dir DIR [OPTIONS]

Options:
  --model NAME       Claude model. Default: claude-opus-4-7.
  --repo PATH        Target repo path, passed through for logging.
  --work-id ID       AICG work item id, passed through for logging.
  -h, --help         Show this help.

This wrapper calls the local claude CLI. It does not use Anthropic API keys.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      MODEL="${2:-}"
      shift 2
      ;;
    --prompt)
      PROMPT="${2:-}"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="${2:-}"
      shift 2
      ;;
    --repo)
      REPO="${2:-}"
      shift 2
      ;;
    --work-id)
      WORK_ID="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
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
} >"$OUTPUT_DIR/agent-run.env"

# Unattended permission profile:
#   --permission-mode acceptEdits  : Edit/Write/Read auto-approved
#   --add-dir <repo>               : grant tool access to the repo
#   --allowedTools                 : narrow Bash to safe read-only ops + git status/diff
#   stdin redirected from /dev/null: never block on prompts
# --allowedTools accepts a single space-separated string (claude
# greedily consumes positional args after the flag, so passing an
# array swallows the prompt and breaks --print).
ALLOWED_TOOLS="Edit Write Read Glob Grep Bash(mkdir:*) Bash(ls:*) Bash(cat:*) Bash(git status:*) Bash(git diff:*)"

cd "$REPO"
# Hard timeout so a hung/stalled agent call can't wedge the job for hours (a
# missing timeout here let one authoring run hang ~10h). --kill-after sends
# SIGKILL if it ignores SIGTERM. Override with AICG_AGENT_TIMEOUT.
AGENT_TIMEOUT="${AICG_AGENT_TIMEOUT:-1200}"
# Feed the prompt via stdin so positional-arg parsing can't mangle it.
# `|| rc=$?` so set -e doesn't abort before we can report a timeout.
rc=0
timeout --kill-after=30 "$AGENT_TIMEOUT" claude \
  --model "$MODEL" \
  --print \
  --permission-mode acceptEdits \
  --add-dir "$REPO" \
  --allowedTools "$ALLOWED_TOOLS" \
  <"$PROMPT" \
  >"$OUTPUT_DIR/response.md" || rc=$?
if [[ "$rc" -eq 124 || "$rc" -eq 137 ]]; then
  echo "[run-claude-content] agent timed out after ${AGENT_TIMEOUT}s" >&2
fi
exit "$rc"

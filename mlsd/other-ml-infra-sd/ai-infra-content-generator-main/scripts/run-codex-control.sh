#!/usr/bin/env bash
set -euo pipefail

# codex is typically installed under ~/.local/bin which is in
# interactive PATH but not in subprocess PATH inherited from ssh or
# systemd. Make the wrapper self-sufficient.
export PATH="${HOME}/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

MODEL="codex-gpt-5.5"
PROMPT=""
OUTPUT_DIR=""
REPO=""
WORK_ID=""

usage() {
  cat <<EOF
Usage: $(basename "$0") --prompt PATH --output-dir DIR [OPTIONS]

Options:
  --model NAME       Codex model. Default: codex-gpt-5.5.
  --repo PATH        Target repo path, passed through for logging.
  --work-id ID       AICG work item id, passed through for logging.
  -h, --help         Show this help.

This wrapper calls the local codex CLI. It does not use OpenAI API keys.
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
command -v codex >/dev/null || { echo "codex CLI not found in PATH" >&2; exit 127; }

mkdir -p "$OUTPUT_DIR"
{
  echo "model=$MODEL"
  echo "repo=$REPO"
  echo "work_id=$WORK_ID"
  echo "prompt=$PROMPT"
  date '+started_at=%Y-%m-%dT%H:%M:%S%z'
} >"$OUTPUT_DIR/agent-run.env"

# Unattended permission profile:
#   --sandbox workspace-write : agent can write inside the repo, sandboxed elsewhere
#   --cd <repo>               : working root pinned to the repo
#   --skip-git-repo-check     : repo is git but may have a dirty state from earlier
#   prompt fed via stdin      : --input was removed in newer codex builds
cd "$REPO"
codex exec \
  --model "$MODEL" \
  --sandbox workspace-write \
  --cd "$REPO" \
  --skip-git-repo-check \
  - < "$PROMPT" \
  >"$OUTPUT_DIR/response.md"

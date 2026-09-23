#!/usr/bin/env bash
set -euo pipefail

# claude is typically installed under ~/.local/bin which is in
# interactive PATH but not in subprocess PATH inherited from ssh or
# systemd. Make the wrapper self-sufficient.
export PATH="${HOME}/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Local Claude judge wrapper. Mirrors run-claude-content.sh but
# scopes the agent to grading: it reads the judge prompt packet (which
# includes the absolute artifact path and the rubric) and is expected
# to write `response.json` into the output directory matching the
# contract documented in src/aicg/judge.py.

MODEL="claude-opus-4-7"
PROMPT=""
OUTPUT_DIR=""
REPO=""
WORK_ID=""
ARTIFACT=""

usage() {
  cat <<EOF
Usage: $(basename "$0") --prompt PATH --output-dir DIR [OPTIONS]

Options:
  --model NAME       Claude model. Default: claude-opus-4-7.
  --repo PATH        Target repo path, passed through for logging.
  --work-id ID       AICG work item id, passed through for logging.
  --artifact PATH    Absolute path to the artifact being graded.
  -h, --help         Show this help.

The wrapper invokes the local claude CLI; no Anthropic API token is
used. The judge must write response.json to the output directory.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)        MODEL="${2:-}";        shift 2 ;;
    --prompt)       PROMPT="${2:-}";       shift 2 ;;
    --output-dir)   OUTPUT_DIR="${2:-}";   shift 2 ;;
    --repo)         REPO="${2:-}";         shift 2 ;;
    --work-id)      WORK_ID="${2:-}";      shift 2 ;;
    --artifact)     ARTIFACT="${2:-}";     shift 2 ;;
    -h|--help)      usage; exit 0 ;;
    *)              echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ -f "$PROMPT" ]] || { echo "Prompt not found: $PROMPT" >&2; exit 2; }
[[ -n "$OUTPUT_DIR" ]] || { echo "--output-dir is required" >&2; exit 2; }
command -v claude >/dev/null || { echo "claude CLI not found in PATH" >&2; exit 127; }

mkdir -p "$OUTPUT_DIR"
{
  echo "model=$MODEL"
  echo "repo=$REPO"
  echo "work_id=$WORK_ID"
  echo "artifact=$ARTIFACT"
  echo "prompt=$PROMPT"
  date '+started_at=%Y-%m-%dT%H:%M:%S%z'
} >"$OUTPUT_DIR/judge-run.env"

# The judge is expected to use the prompt verbatim. We append a
# system-style suffix telling the agent that the output contract is
# response.json under OUTPUT_DIR.
PROMPT_BODY="$(cat "$PROMPT")
---
You are READ-ONLY and cannot write any files. Output your verdict as a single
JSON object inside a \`\`\`json code block as the final part of your reply.
Do NOT attempt to write a file. Follow the schema described in the prompt above."

# Judge is read-only by contract; deny write tools to ensure it cannot
# mutate the artifact it is grading.
ARTIFACT_DIR="$(dirname "$ARTIFACT")"
# Single space-separated strings: claude greedily consumes positional
# args after --allowedTools / --disallowedTools.
ALLOWED_TOOLS="Read Glob Grep Bash(cat:*) Bash(ls:*)"
DISALLOWED_TOOLS="Edit Write"

# Pipe the prompt via stdin to avoid positional-arg ambiguity.
printf '%s' "$PROMPT_BODY" | claude \
  --model "$MODEL" \
  --print \
  --permission-mode default \
  --add-dir "$ARTIFACT_DIR" \
  --allowedTools "$ALLOWED_TOOLS" \
  --disallowedTools "$DISALLOWED_TOOLS" \
  >"$OUTPUT_DIR/raw-output.md"

# The judge is read-only and emits its verdict JSON to stdout (raw-output.md).
# Robustly extract the last balanced JSON object that has a "score" field —
# handles a fenced ```json block or a verdict embedded in prose.
if [[ ! -f "$OUTPUT_DIR/response.json" ]]; then
  python3 - "$OUTPUT_DIR/raw-output.md" "$OUTPUT_DIR/response.json" <<'PYEOF'
import json
import sys

raw = open(sys.argv[1], encoding="utf-8", errors="replace").read()


def balanced_objects(s):
    objs, i, n = [], 0, len(s)
    while i < n:
        if s[i] == "{":
            depth, j = 0, i
            while j < n:
                if s[j] == "{":
                    depth += 1
                elif s[j] == "}":
                    depth -= 1
                    if depth == 0:
                        objs.append(s[i : j + 1])
                        break
                j += 1
            i = j + 1
        else:
            i += 1
    return objs


best = None
for cand in balanced_objects(raw):
    try:
        obj = json.loads(cand)
    except Exception:
        continue
    if isinstance(obj, dict) and ("total" in obj or "score" in obj) and "dimensions" in obj:
        best = obj  # keep the last valid verdict (freshness schema uses "total")
if best is not None:
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(best, f)
PYEOF
fi

#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly RUNNER_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

WORKSPACE="$(cd "$RUNNER_DIR/.." && pwd)"
SCHEDULER="systemd"
DRY_RUN=0

usage() {
  cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS]

Options:
  --workspace PATH   Curriculum workspace. Default: parent of runner repo.
  --scheduler MODE   systemd or cron. Default: systemd.
  --dry-run          Print actions without changing host scheduler.
  -h, --help         Show this help.
EOF
}

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

die() {
  log "ERROR: $*" >&2
  exit 1
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --workspace)
        WORKSPACE="${2:-}"
        shift 2
        ;;
      --scheduler)
        SCHEDULER="${2:-}"
        shift 2
        ;;
      --dry-run)
        DRY_RUN=1
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument: $1"
        ;;
    esac
  done
}

main() {
  command -v git >/dev/null || die "git is required"
  command -v python3 >/dev/null || die "python3 is required"

  log "Preparing local virtualenv"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    python3 -m venv "$RUNNER_DIR/.venv"
    "$RUNNER_DIR/.venv/bin/python" -m pip install -e "${RUNNER_DIR}[dev]"
    "$RUNNER_DIR/scripts/aicg-org-job.sh" sync --workspace "$WORKSPACE"
  else
    log "Would create $RUNNER_DIR/.venv"
    log "Would install editable dev package"
    log "Would sync repos into $WORKSPACE"
  fi

  local schedule_args=(--scheduler "$SCHEDULER" --workspace "$WORKSPACE")
  if [[ "$DRY_RUN" -eq 1 ]]; then
    schedule_args+=(--dry-run)
  fi
  "$RUNNER_DIR/scripts/install-schedules.sh" "${schedule_args[@]}"
}

parse_args "$@"
main

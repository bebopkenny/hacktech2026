#!/usr/bin/env bash
# RevitSync — pull latest code and restart the stack on an existing VM.
#
# Usage (on the VM, inside the cloned repo):
#   sudo bash deploy/update.sh
#
# Override the branch with: REPO_BRANCH=main sudo bash deploy/update.sh

set -euo pipefail

REPO_BRANCH="${REPO_BRANCH:-testing}"

c_cyan="\033[1;36m"; c_green="\033[1;32m"; c_yellow="\033[1;33m"; c_red="\033[1;31m"; c_reset="\033[0m"
step()  { echo -e "\n${c_cyan}>> $*${c_reset}"; }
ok()    { echo -e "   ${c_green}OK${c_reset}   $*"; }
warn()  { echo -e "   ${c_yellow}WARN${c_reset} $*"; }
abort() { echo -e "\n${c_red}ERROR: $*${c_reset}" >&2; exit 1; }

if [[ "${EUID}" -ne 0 ]]; then
  abort "Run as root: sudo bash deploy/update.sh"
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  abort "No docker compose available. Run deploy/bootstrap.sh first."
fi

REPO_DIR="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$REPO_DIR" ]]; then
  abort "Not inside a git checkout. cd into the repo first."
fi
cd "$REPO_DIR"

step "Pulling latest from $REPO_BRANCH"
git fetch --quiet origin "$REPO_BRANCH"
git checkout --quiet "$REPO_BRANCH"
git pull --ff-only origin "$REPO_BRANCH"
ok "now at $(git rev-parse --short HEAD)"

step "Rebuilding and restarting"
$COMPOSE up -d --build
ok "stack restarted"

step "Health check"
for i in {1..30}; do
  if curl -fsS "http://localhost:8000/health" >/dev/null 2>&1; then
    ok "coordination /health: OK"
    break
  fi
  sleep 1
  [[ $i -eq 30 ]] && warn "coordination /health never came up — check '$COMPOSE logs coordination'"
done

ok "done. Tail logs with: $COMPOSE logs -f"

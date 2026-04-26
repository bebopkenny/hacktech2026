#!/usr/bin/env bash
# RevitSync — one-shot bootstrap for a fresh Ubuntu Vultr VM.
#
# Usage (on the VM, as root):
#   curl -fsSL https://raw.githubusercontent.com/bebopkenny/hacktech2026/testing/deploy/bootstrap.sh | bash
#
# Or, if you've already cloned the repo:
#   sudo bash deploy/bootstrap.sh
#
# What it does:
#   1. Installs Docker + docker compose plugin (idempotent).
#   2. Clones the repo to /opt/revitsync if not already present.
#   3. Prompts for K2_API_KEY and writes /opt/revitsync/.env (if missing).
#   4. Opens UFW ports 8000 + 8001 (if UFW is active).
#   5. Builds and starts the stack with `docker compose up -d`.
#   6. Prints the WebSocket URL the Revit plugin should use.

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/bebopkenny/hacktech2026.git}"
REPO_BRANCH="${REPO_BRANCH:-testing}"
INSTALL_DIR="${INSTALL_DIR:-/opt/revitsync}"

c_cyan="\033[1;36m"; c_green="\033[1;32m"; c_yellow="\033[1;33m"; c_red="\033[1;31m"; c_reset="\033[0m"
step()  { echo -e "\n${c_cyan}>> $*${c_reset}"; }
ok()    { echo -e "   ${c_green}OK${c_reset}   $*"; }
warn()  { echo -e "   ${c_yellow}WARN${c_reset} $*"; }
abort() { echo -e "\n${c_red}ERROR: $*${c_reset}" >&2; exit 1; }

if [[ "${EUID}" -ne 0 ]]; then
  abort "Run as root: sudo bash deploy/bootstrap.sh"
fi

# ── 1. Docker ────────────────────────────────────────────────────────────────
step "Installing Docker"
if command -v docker >/dev/null 2>&1; then
  ok "docker already installed ($(docker --version))"
else
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker
  ok "docker installed"
fi

# Resolve `docker compose` (v2 plugin) or fallback to `docker-compose` (v1).
if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  abort "Neither 'docker compose' nor 'docker-compose' is available."
fi
ok "compose: ${COMPOSE}"

# ── 2. Clone or update repo ──────────────────────────────────────────────────
step "Fetching source ($REPO_URL @ $REPO_BRANCH)"
if [[ ! -d "$INSTALL_DIR/.git" ]]; then
  apt-get install -y -qq git
  git clone --branch "$REPO_BRANCH" "$REPO_URL" "$INSTALL_DIR"
  ok "cloned to $INSTALL_DIR"
else
  cd "$INSTALL_DIR"
  git fetch --quiet origin "$REPO_BRANCH"
  git checkout --quiet "$REPO_BRANCH"
  git pull --quiet --ff-only origin "$REPO_BRANCH" || warn "git pull failed — continuing with existing checkout"
  ok "updated $INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# ── 3. .env ──────────────────────────────────────────────────────────────────
step "Configuring .env"
if [[ -f .env ]]; then
  ok ".env already exists — leaving it alone"
else
  if [[ -n "${K2_API_KEY:-}" ]]; then
    api_key="$K2_API_KEY"
    ok "using K2_API_KEY from environment"
  else
    # Read from controlling terminal even when piped via curl.
    if [[ -r /dev/tty ]]; then
      printf "  K2 API key (https://api.k2think.ai): "
      read -rs api_key < /dev/tty
      echo
    else
      abort "No K2_API_KEY in env and no TTY to prompt. Re-run with: K2_API_KEY=xxx bash bootstrap.sh"
    fi
  fi
  cat > .env <<EOF
K2_API_KEY=${api_key}
EOF
  chmod 600 .env
  ok ".env written"
fi

# ── 4. Firewall ──────────────────────────────────────────────────────────────
step "Opening firewall ports"
if command -v ufw >/dev/null 2>&1 && ufw status | grep -qi "Status: active"; then
  ufw allow 8000/tcp >/dev/null && ok "ufw: 8000/tcp open"
  ufw allow 8001/tcp >/dev/null && ok "ufw: 8001/tcp open"
else
  warn "ufw is not active — assuming Vultr's cloud firewall already permits 8000/8001"
fi

# ── 5. Bring up stack ────────────────────────────────────────────────────────
step "Building and starting the stack"
$COMPOSE up -d --build
ok "stack is up"

step "Waiting for /health"
public_ip="$(curl -fsS https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')"
for i in {1..30}; do
  if curl -fsS "http://localhost:8000/health" >/dev/null 2>&1; then
    ok "coordination service is healthy"
    break
  fi
  sleep 1
  [[ $i -eq 30 ]] && warn "coordination /health never came up — check '$COMPOSE logs coordination'"
done

# ── 6. Done ──────────────────────────────────────────────────────────────────
cat <<EOF

----------------------------------------------------------------
  RevitSync stack is running.

  Coordination : http://${public_ip}:8000
  AI layer     : http://${public_ip}:8001
  WebSocket    : ws://${public_ip}:8000/ws/<session_id>

  Plugin install: set REVITSYNC_WS_URL=ws://${public_ip}:8000/ws
                  in install.ps1 prompt on the Windows machine.

  Logs   : cd ${INSTALL_DIR} && ${COMPOSE} logs -f
  Update : cd ${INSTALL_DIR} && bash deploy/update.sh
----------------------------------------------------------------
EOF

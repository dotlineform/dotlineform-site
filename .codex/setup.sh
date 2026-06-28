#!/usr/bin/env bash
set -euo pipefail

log()  { printf '[codex-setup] %s\n' "$*"; }
warn() { printf '[codex-setup][warn] %s\n' "$*" >&2; }
die()  { printf '[codex-setup][error] %s\n' "$*" >&2; exit 1; }

trap 'die "Command failed at line ${LINENO}: ${BASH_COMMAND}"' ERR

VENV_DIR=".venv"
VENV_PYTHON="${VENV_DIR}/bin/python"
VENV_PIP="${VENV_DIR}/bin/pip"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

have_sudo() {
  command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1
}

can_skip_apt_packages() {
  local -a required_commands=(python3 git gcc make pkg-config)
  local cmd

  for cmd in "${required_commands[@]}"; do
    command -v "$cmd" >/dev/null 2>&1 || return 1
  done

  python3 -m venv --help >/dev/null 2>&1 || return 1

  if [[ "${SETUP_INSTALL_MEDIA_PACKAGES:-0}" == "1" ]]; then
    command -v ffmpeg >/dev/null 2>&1 || return 1
    command -v heif-convert >/dev/null 2>&1 || return 1
  fi

  return 0
}

install_apt_packages() {
  if [[ "${SETUP_SKIP_APT:-0}" == "1" ]]; then
    log "SETUP_SKIP_APT=1; skipping apt package installation."
    return 0
  fi

  command -v apt-get >/dev/null 2>&1 || {
    log "apt-get not available; skipping system package installation."
    return 0
  }

  if [[ "${FORCE_APT_PACKAGES:-0}" != "1" ]] && can_skip_apt_packages; then
    log "System packages already satisfied; skipping apt package installation."
    return 0
  fi

  log "Installing baseline system packages via apt-get (FORCE_APT_PACKAGES=${FORCE_APT_PACKAGES:-0}, SETUP_INSTALL_MEDIA_PACKAGES=${SETUP_INSTALL_MEDIA_PACKAGES:-0})."

  local -a apt_cmd=(apt-get)
  if [[ "$(id -u)" -ne 0 ]]; then
    if have_sudo; then
      apt_cmd=(sudo -n apt-get)
    else
      warn "No non-interactive sudo; cannot install system packages."
      return 0
    fi
  fi

  "${apt_cmd[@]}" -o Acquire::Retries=3 update
  local -a packages=(
    build-essential \
    ca-certificates \
    curl \
    git \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    pkg-config \
    python3 \
    python3-pip \
    python3-venv \
    zlib1g-dev
  )

  if [[ "${SETUP_INSTALL_MEDIA_PACKAGES:-0}" == "1" ]]; then
    packages+=(ffmpeg libheif-examples)
  else
    log "Skipping optional media packages (ffmpeg, libheif-examples). Set SETUP_INSTALL_MEDIA_PACKAGES=1 to include."
  fi

  "${apt_cmd[@]}" install -y --no-install-recommends "${packages[@]}"
}

ensure_python_venv() {
  command -v python3 >/dev/null 2>&1 || die "python3 not available."
  local venv_created=0

  if [[ -d "$VENV_DIR" ]]; then
    log "Reusing existing virtualenv at ${VENV_DIR}."
  else
    log "Creating virtualenv at ${VENV_DIR}."
    python3 -m venv "$VENV_DIR"
    venv_created=1
  fi

  [[ -x "$VENV_PYTHON" ]] || die "Virtualenv python not found at ${VENV_PYTHON}."
  [[ -x "$VENV_PIP" ]] || die "Virtualenv pip not found at ${VENV_PIP}."

  log "Python executable: ${VENV_PYTHON}"
  log "pip executable: ${VENV_PIP}"

  if [[ "$venv_created" == "1" ]]; then
    log "Upgrading pip inside virtualenv (new virtualenv created)."
    "$VENV_PYTHON" -m pip install --upgrade pip
  else
    log "Skipping pip upgrade (reusing existing virtualenv)."
  fi

  if [[ -f requirements.txt ]]; then
    log "Installing Python dependencies into virtualenv"
    "$VENV_PIP" install -r requirements.txt
  else
    warn "requirements.txt not found; skipping Python dependency install."
  fi
}

persist_agent_environment() {
  if [[ "${SETUP_PERSIST_AGENT_ENV:-1}" != "1" ]]; then
    log "SETUP_PERSIST_AGENT_ENV is not 1; skipping shell environment persistence."
    return 0
  fi

  local bashrc="${HOME}/.bashrc"
  local marker="# dotlineform Codex setup environment"
  local repo_venv_bin="${REPO_ROOT}/${VENV_DIR}/bin"

  if [[ -f "$bashrc" ]] && grep -Fq "$marker" "$bashrc"; then
    log "Shell environment already contains dotlineform Codex setup block."
    return 0
  fi

  log "Persisting virtualenv PATH for later cloud agent shells in ${bashrc}."
  {
    printf '\n%s\n' "$marker"
    printf 'export PATH="%s:$PATH"\n' "$repo_venv_bin"
    printf 'export SITE_PYTHON="%s"\n' "${REPO_ROOT}/${VENV_PYTHON}"
    printf 'export PYTHON_BIN="%s"\n' "${REPO_ROOT}/${VENV_PYTHON}"
  } >> "$bashrc"
}

verify_environment() {
  log "Versions"
  printf 'python3 path: %s\n' "$(command -v python3 || echo not-found)"
  printf 'venv python path: %s\n' "${REPO_ROOT}/${VENV_PYTHON}"
  python3 -V
  "$VENV_PYTHON" -V

  if command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg -version | head -n 1
  fi
}

run_phase() {
  local phase="$1"
  shift
  local start_ts end_ts duration_s
  start_ts="$(date +%s)"
  log "Phase start: ${phase}"
  "$@"
  end_ts="$(date +%s)"
  duration_s="$((end_ts - start_ts))"
  log "Phase complete: ${phase} (${duration_s}s)"
}

main() {
  log "Repo root: $REPO_ROOT"
  run_phase "apt" install_apt_packages
  run_phase "python" ensure_python_venv
  run_phase "agent-env" persist_agent_environment
  run_phase "verify" verify_environment
  log "Setup complete"
}

main "$@"

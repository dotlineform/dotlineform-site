#!/usr/bin/env bash
set -euo pipefail

log()  { printf '[codex-setup] %s\n' "$*"; }
warn() { printf '[codex-setup][warn] %s\n' "$*" >&2; }
die()  { printf '[codex-setup][error] %s\n' "$*" >&2; exit 1; }

trap 'die "Command failed at line ${LINENO}: ${BASH_COMMAND}"' ERR

RUBY_VERSION="3.1.6"
BUNDLER_VERSION="2.6.9"
VENV_DIR=".venv"
VENV_PYTHON="${VENV_DIR}/bin/python"
VENV_PIP="${VENV_DIR}/bin/pip"
BUNDLE_LOCAL_PATH="vendor/bundle"
BUNDLE_EXE="bundle"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

have_sudo() {
  command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1
}

assert_ruby_version_consistency() {
  local ruby_version_file="$REPO_ROOT/.ruby-version"
  [[ -f "$ruby_version_file" ]] || return 0

  local repo_ruby_version
  repo_ruby_version="$(tr -d '[:space:]' < "$ruby_version_file")"

  if [[ "$repo_ruby_version" != "$RUBY_VERSION" ]]; then
    warn ".ruby-version (${repo_ruby_version}) differs from setup preferred RUBY_VERSION (${RUBY_VERSION}); continuing with installed Ruby."
  fi
}

can_skip_apt_packages() {
  local -a required_commands=(python3 git ffmpeg ruby gem bundle gcc make pkg-config)
  local cmd

  for cmd in "${required_commands[@]}"; do
    command -v "$cmd" >/dev/null 2>&1 || return 1
  done

  python3 -m venv --help >/dev/null 2>&1 || return 1
  return 0
}

toolchain_ready() {
  local -a required_commands=(python3 ruby bundle git ffmpeg)
  local -a missing_commands=()
  local cmd

  for cmd in "${required_commands[@]}"; do
    command -v "$cmd" >/dev/null 2>&1 || missing_commands+=("$cmd")
  done

  if [[ "${#missing_commands[@]}" -eq 0 ]]; then
    return 0
  fi

  log "Missing commands: ${missing_commands[*]}"
  return 1
}

install_apt_packages() {
  command -v apt-get >/dev/null 2>&1 || {
    log "apt-get not available; skipping system package installation."
    return 0
  }

  if [[ "${FORCE_APT_PACKAGES:-0}" != "1" ]] && can_skip_apt_packages; then
    log "System packages already satisfied; skipping apt package installation."
    return 0
  fi

  log "Installing required system packages via apt-get (FORCE_APT_PACKAGES=${FORCE_APT_PACKAGES:-0})."
  warn "Third-party apt repository warnings can be non-fatal if apt completes successfully."

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
  "${apt_cmd[@]}" install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    ffmpeg \
    git \
    libffi-dev \
    libgdbm-dev \
    libheif-examples \
    libreadline-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libyaml-dev \
    pkg-config \
    python3 \
    python3-pip \
    python3-venv \
    zlib1g-dev
}

ensure_python_venv() {
  command -v python3 >/dev/null 2>&1 || die "python3 not available."

  if [[ -d "$VENV_DIR" ]]; then
    log "Reusing existing virtualenv at ${VENV_DIR}."
  else
    log "Creating virtualenv at ${VENV_DIR}."
    python3 -m venv "$VENV_DIR"
  fi

  [[ -x "$VENV_PYTHON" ]] || die "Virtualenv python not found at ${VENV_PYTHON}."
  [[ -x "$VENV_PIP" ]] || die "Virtualenv pip not found at ${VENV_PIP}."

  log "Python executable: ${VENV_PYTHON}"
  log "pip executable: ${VENV_PIP}"

  log "Upgrading pip inside virtualenv"
  "$VENV_PYTHON" -m pip install --upgrade pip

  if [[ -f requirements.txt ]]; then
    log "Installing Python dependencies into virtualenv"
    "$VENV_PIP" install -r requirements.txt
  else
    warn "requirements.txt not found; skipping Python dependency install."
  fi
}

ensure_ruby_runtime() {
  command -v ruby >/dev/null 2>&1 || die "ruby is required but not available on PATH."
  command -v gem >/dev/null 2>&1 || die "gem is required but not available on PATH."

  local ruby_version_actual
  ruby_version_actual="$(ruby -e 'print RUBY_VERSION')"

  # Compatibility rule: require Ruby >= 3.1.0 for this repository setup.
  # We intentionally allow newer patch/minor versions (for example 3.2.x).
  ruby -e "exit(Gem::Version.new(RUBY_VERSION) >= Gem::Version.new('3.1.0') ? 0 : 1)" \
    || die "Ruby ${ruby_version_actual} is incompatible; require Ruby >= 3.1.0."

  log "Ruby version: ${ruby_version_actual} (preferred: ${RUBY_VERSION}, minimum supported: 3.1.0)"
}

ensure_bundler() {
  if command -v "$BUNDLE_EXE" >/dev/null 2>&1 && "$BUNDLE_EXE" _${BUNDLER_VERSION}_ -v >/dev/null 2>&1; then
    log "Bundler ${BUNDLER_VERSION} already available."
    return 0
  fi

  log "Installing Bundler ${BUNDLER_VERSION} to user gem home"
  gem install --user-install "bundler:${BUNDLER_VERSION}" --no-document

  local gem_user_bin
  gem_user_bin="$(ruby -r rubygems -e 'print Gem.user_dir')/bin"
  export PATH="${gem_user_bin}:$PATH"
  BUNDLE_EXE="${gem_user_bin}/bundle"

  [[ -x "$BUNDLE_EXE" ]] || die "bundle not found at ${BUNDLE_EXE} after installing Bundler ${BUNDLER_VERSION}."
  "$BUNDLE_EXE" _${BUNDLER_VERSION}_ -v >/dev/null 2>&1 || die "Bundler ${BUNDLER_VERSION} not available after installation."
}

install_ruby_deps() {
  if [[ -f Gemfile ]]; then
    log "Installing Ruby gems to ${BUNDLE_LOCAL_PATH}"
    "$BUNDLE_EXE" _${BUNDLER_VERSION}_ config set --local path "$BUNDLE_LOCAL_PATH"
    "$BUNDLE_EXE" _${BUNDLER_VERSION}_ install
  else
    warn "Gemfile not found; skipping Ruby dependency install."
  fi
}

verify_environment() {
  log "Versions"
  printf 'python3 path: %s\n' "$(command -v python3 || echo not-found)"
  printf 'venv python path: %s\n' "$(cd "$REPO_ROOT" && pwd)/${VENV_PYTHON}"
  printf 'venv pip path: %s\n' "$(cd "$REPO_ROOT" && pwd)/${VENV_PIP}"
  printf 'ruby path: %s\n' "$(command -v ruby || echo not-found)"
  printf 'bundle path: %s\n' "$BUNDLE_EXE"

  "$VENV_PYTHON" -V
  ruby -v
  "$BUNDLE_EXE" _${BUNDLER_VERSION}_ -v

  if command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg -version | head -n 1
  fi

  if [[ -f .bundle/config ]]; then
    log "Bundle local config"
    sed -n '1,80p' .bundle/config
  fi
}

main() {
  log "Repo root: $REPO_ROOT"
  assert_ruby_version_consistency
  install_apt_packages
  ensure_python_venv
  persist_python_venv_path
  ensure_ruby_runtime
  ensure_bundler
  install_ruby_deps
  verify_environment
  log "Setup complete"
}

main "$@"

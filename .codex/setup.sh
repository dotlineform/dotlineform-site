#!/usr/bin/env bash
set -euo pipefail

log()  { printf '[codex-setup] %s\n' "$*"; }
warn() { printf '[codex-setup][warn] %s\n' "$*" >&2; }
die()  { printf '[codex-setup][error] %s\n' "$*" >&2; exit 1; }

trap 'die "Command failed at line ${LINENO}: ${BASH_COMMAND}"' ERR

VENV_DIR=".venv"
VENV_PYTHON="${VENV_DIR}/bin/python"
VENV_PIP="${VENV_DIR}/bin/pip"
BUNDLE_EXE="bundle"
BUNDLE_BOOTSTRAP_ATTEMPTED=0

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
    libgdbm-dev \
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
  log "Ruby version: ${ruby_version_actual} ($(command -v ruby))"
}

run_bundler() {
  "$BUNDLE_EXE" "$@"
}

ensure_bundler_on_path() {
  if command -v bundle >/dev/null 2>&1; then
    BUNDLE_EXE="$(command -v bundle)"
    local bundler_version
    bundler_version="$(bundle -v 2>/dev/null || true)"
    if [[ -n "$bundler_version" ]]; then
      log "Bundler detected: ${bundler_version} (${BUNDLE_EXE})"
    else
      warn "bundle exists on PATH but could not report version; will attempt to use it."
    fi
    return 0
  fi

  return 1
}

bootstrap_bundler() {
  local fallback_version="${BUNDLER_FALLBACK_VERSION:-}"
  local gem_install_args=(--user-install --no-document bundler)

  if [[ -n "$fallback_version" ]]; then
    gem_install_args=(--user-install --no-document "bundler:${fallback_version}")
    log "Installing fallback Bundler ${fallback_version} with --user-install."
  else
    log "Installing fallback Bundler with --user-install."
  fi

  gem install "${gem_install_args[@]}"

  local gem_user_bin
  gem_user_bin="$(ruby -r rubygems -e 'print Gem.user_dir')/bin"
  export PATH="${gem_user_bin}:$PATH"

  BUNDLE_EXE="${gem_user_bin}/bundle"
  [[ -x "$BUNDLE_EXE" ]] || die "Bundler installation did not produce ${BUNDLE_EXE}."
  BUNDLE_BOOTSTRAP_ATTEMPTED=1
  log "Bundler detected: $("$BUNDLE_EXE" -v) (${BUNDLE_EXE})"
}

ensure_bundler() {
  if ensure_bundler_on_path; then
    return 0
  fi

  warn "bundle is not available on PATH; installing fallback bundler."
  bootstrap_bundler
}

install_ruby_deps() {
  if [[ -f Gemfile ]]; then
    log "Installing Ruby gems"
    if run_bundler config set --local path vendor/bundle && run_bundler install; then
      return 0
    fi

    if [[ "$BUNDLE_BOOTSTRAP_ATTEMPTED" == "0" ]]; then
      warn "Existing bundler failed for this Gemfile; installing fallback bundler and retrying once."
      bootstrap_bundler
      run_bundler config set --local path vendor/bundle
      run_bundler install
      return 0
    fi

    die "Bundler failed to install gems even after fallback install."
  else
    warn "Gemfile not found; skipping Ruby dependency install."
  fi
}

verify_environment() {
  log "Versions"
  printf 'python3 path: %s\n' "$(command -v python3 || echo not-found)"
  printf 'ruby path: %s\n' "$(command -v ruby || echo not-found)"
  printf 'bundle path: %s\n' "$BUNDLE_EXE"
  python3 -V
  ruby -v
  run_bundler -v

  if command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg -version | head -n 1
  fi

  if [[ -f .bundle/config ]]; then
    log "Bundle local config"
    sed -n '1,80p' .bundle/config
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
  run_phase "ruby-runtime" ensure_ruby_runtime
  run_phase "bundler-detect" ensure_bundler
  run_phase "ruby-deps" install_ruby_deps
  run_phase "verify" verify_environment
  log "Setup complete"
}

main "$@"

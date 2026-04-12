#!/usr/bin/env bash
set -Eeuo pipefail

log()  { printf '[codex-setup] %s\n' "$*"; }
warn() { printf '[codex-setup][warn] %s\n' "$*" >&2; }
die()  { printf '[codex-setup][error] %s\n' "$*" >&2; exit 1; }

trap 'die "Command failed at line ${LINENO}: ${BASH_COMMAND}"' ERR

RUBY_VERSION="3.1.6"
BUNDLER_VERSION="2.6.9"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

export RBENV_ROOT="${RBENV_ROOT:-$HOME/.rbenv}"
export PATH="$RBENV_ROOT/bin:$RBENV_ROOT/shims:$PATH"

append_line_if_missing() {
  local file="$1"
  local line="$2"
  mkdir -p "$(dirname "$file")"
  touch "$file"
  grep -Fqx "$line" "$file" || printf '%s\n' "$line" >> "$file"
}

have_sudo() {
  command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1
}

install_apt_packages() {
  command -v apt-get >/dev/null 2>&1 || {
    warn "apt-get not available; skipping OS package install."
    return 0
  }

  if [[ "$(id -u)" -eq 0 ]]; then
    apt-get update
    apt-get install -y --no-install-recommends \
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
  elif have_sudo; then
    sudo -n apt-get update
    sudo -n apt-get install -y --no-install-recommends \
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
  else
    warn "No non-interactive sudo; skipping OS package install."
  fi
}

assert_ruby_version_consistency() {
  local ruby_version_file="$REPO_ROOT/.ruby-version"
  [[ -f "$ruby_version_file" ]] || return 0

  local repo_ruby_version
  repo_ruby_version="$(tr -d '[:space:]' < "$ruby_version_file")"

  if [[ "$repo_ruby_version" != "$RUBY_VERSION" ]]; then
    die ".ruby-version (${repo_ruby_version}) does not match setup RUBY_VERSION (${RUBY_VERSION})."
  fi
}

ensure_rbenv() {
  if [[ ! -d "$RBENV_ROOT" ]]; then
    log "Installing rbenv"
    git clone https://github.com/rbenv/rbenv.git "$RBENV_ROOT"
  fi

  mkdir -p "$RBENV_ROOT/plugins"

  if [[ ! -d "$RBENV_ROOT/plugins/ruby-build" ]]; then
    log "Installing ruby-build"
    git clone https://github.com/rbenv/ruby-build.git "$RBENV_ROOT/plugins/ruby-build"
  fi

  command -v rbenv >/dev/null 2>&1 || die "rbenv not on PATH."
  eval "$(rbenv init - bash)"
}

persist_rbenv_init() {
  append_line_if_missing "$HOME/.bashrc" 'export RBENV_ROOT="$HOME/.rbenv"'
  append_line_if_missing "$HOME/.bashrc" 'export PATH="$RBENV_ROOT/bin:$RBENV_ROOT/shims:$PATH"'
  append_line_if_missing "$HOME/.bashrc" 'if command -v rbenv >/dev/null 2>&1; then eval "$(rbenv init - bash)"; fi'
}

ensure_ruby() {
  if ! rbenv versions --bare | grep -qx "$RUBY_VERSION"; then
    log "Installing Ruby $RUBY_VERSION"
    rbenv install "$RUBY_VERSION"
  fi

  rbenv global "$RUBY_VERSION"
  rbenv rehash
}

ensure_bundler() {
  if ! gem list -i bundler -v "$BUNDLER_VERSION" >/dev/null 2>&1; then
    log "Installing Bundler $BUNDLER_VERSION"
    gem install "bundler:$BUNDLER_VERSION" --no-document
    rbenv rehash
  fi
}

install_python_deps() {
  command -v python3 >/dev/null 2>&1 || die "python3 not available."

  python3 -m pip install --upgrade pip

  if [[ -f requirements.txt ]]; then
    log "Installing Python dependencies"
    python3 -m pip install -r requirements.txt
  else
    warn "requirements.txt not found; skipping."
  fi
}

install_ruby_deps() {
  if [[ -f Gemfile ]]; then
    log "Installing Ruby gems"
    bundle _${BUNDLER_VERSION}_ config set --local path vendor/bundle
    bundle _${BUNDLER_VERSION}_ install
  else
    warn "Gemfile not found; skipping."
  fi
}

verify_environment() {
  log "Versions"
  python3 -V
  ruby -v
  bundle -v

  if command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg -version | head -n 1
  fi
}

main() {
  log "Repo root: $REPO_ROOT"
  assert_ruby_version_consistency
  install_apt_packages
  ensure_rbenv
  persist_rbenv_init
  ensure_ruby
  ensure_bundler
  install_python_deps
  install_ruby_deps
  verify_environment
  log "Setup complete"
}

main "$@"

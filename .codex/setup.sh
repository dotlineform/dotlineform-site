#!/usr/bin/env bash
set -euo pipefail

# Resolve repo root (supports being run from anywhere).
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

export RBENV_ROOT="${RBENV_ROOT:-/usr/local/rbenv}"
export PATH="$RBENV_ROOT/shims:$RBENV_ROOT/bin:$PATH"

run_as_root() {
  if command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    "$@"
  fi
}

if command -v apt-get >/dev/null 2>&1; then
  run_as_root apt-get update
  run_as_root apt-get install -y --no-install-recommends \
    build-essential \
    libyaml-dev \
    zlib1g-dev \
    libffi-dev \
    libgdbm-dev \
    libreadline-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libheif-examples \
    ffmpeg \
    pkg-config \
    python3 \
    python3-pip \
    python3-venv \
    git
fi

if [ ! -d "$RBENV_ROOT" ]; then
  run_as_root git clone https://github.com/rbenv/rbenv.git "$RBENV_ROOT"
  run_as_root git clone https://github.com/rbenv/ruby-build.git "$RBENV_ROOT/plugins/ruby-build"
fi

if ! command -v rbenv >/dev/null 2>&1; then
  echo "ERROR: rbenv is not available on PATH after setup." >&2
  exit 1
fi

if ! rbenv versions --bare | grep -qx "3.1.6"; then
  rbenv install 3.1.6
fi
rbenv global 3.1.6
rbenv rehash

if ! gem list -i bundler -v 2.6.9 >/dev/null 2>&1; then
  gem install bundler:2.6.9 --no-document
fi
rbenv rehash

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

bundle config set --local path vendor/bundle
bundle _2.6.9_ install

python3 -V
python3 -c "import openpyxl; print('openpyxl', openpyxl.__version__)"
ruby -v
bundle -v
bundle exec jekyll -v
bundle _2.6.9_ exec ./scripts/build_docs.rb

#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/dotlineform-site
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

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

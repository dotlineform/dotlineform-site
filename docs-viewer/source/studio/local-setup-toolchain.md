---
doc_id: local-setup-toolchain
title: Local Setup Toolchain
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: local-setup
---
# Local Setup Toolchain

## Current repo/runtime summary

Current versions in use:

- Python: `3.12.7`
- Python package: `openpyxl 3.1.5`
- Ruby: `3.1.6`
- Bundler: `2.6.9`
- Jekyll: `3.10.0`
- `github-pages` gem: `232`

Current external tools used by the Python/media workflow:

- macOS `sips`
- `ffmpeg`
- `heif-convert` from `libheif`

The Python scripts themselves are lightweight:

- non-stdlib Python dependency is currently just `openpyxl`
- image/srcset generation also depends on external command-line tools, not extra Python packages
- the Tag Studio local write server uses only stdlib modules plus repo-local helpers

That summary is now incomplete for feature-specific Python dependencies because the Docs HTML import feature adds a pinned parser/sanitizer stack in `requirements.txt`.
Use [Runtime Dependencies](/docs/?scope=studio&doc=runtime-dependencies) as the current dependency-role reference.

## Fresh macOS install

Recommended order on a fresh macOS 24 system:

1. Install Apple command line tools if they are not already present:

```bash
xcode-select --install
```

2. Install the non-Python command-line dependencies with Homebrew:

```bash
brew install rbenv ruby-build ffmpeg libheif
brew install --cask miniconda
```

3. Initialize Conda for your shell, then open a new shell:

```bash
conda init zsh
```

If you use `bash` instead of the default macOS `zsh`, run:

```bash
conda init bash
```

4. Create and activate a dedicated Python environment:

```bash
conda create -n dotlineform python=3.12.7 openpyxl=3.1.5
conda activate dotlineform
```

5. Install and select the repo's Ruby version:

```bash
rbenv install 3.1.6
rbenv local 3.1.6
```

6. Install the pinned Bundler version and the Ruby gems:

```bash
gem install bundler:2.6.9
bundle _2.6.9_ install
```

At that point the local script/Jekyll toolchain should be in place.

## Version checks

Check that the active Python is the expected one:

```bash
which python3
python3 -V
python3 -c "import sys, openpyxl; print(sys.version); print('openpyxl', openpyxl.__version__)"
```

Expected current values:

- `python3 -V` -> `Python 3.12.7`
- `openpyxl` -> `3.1.5`

Check the media tools:

```bash
ffmpeg -version | head -n 1
heif-convert --version
sips --help | head -n 1
```

Check the Ruby/Jekyll toolchain:

```bash
ruby -v
bundle -v
bundle exec jekyll -v
```

Expected current values:

- `ruby -v` -> Ruby `3.1.6`
- `bundle -v` -> Bundler `2.6.9`
- `bundle exec jekyll -v` -> Jekyll `3.10.0`

If you want to confirm the repo's pinned Ruby/Bundler versions directly:

```bash
cat .ruby-version
tail -n 3 Gemfile.lock
```

## Switching to the correct version

### Python

The important requirement is that `python3` resolves to an interpreter that has `openpyxl 3.1.5` installed.

Activate the repo environment:

```bash
conda activate dotlineform
```

See available Conda environments:

```bash
conda info --envs
```

If `python3` still points somewhere unexpected, check:

```bash
which python3
python3 -V
```

The repo scripts are normally run via `./scripts/...`, so the active shell `python3` matters because the script shebangs use `/usr/bin/env python3`.

### Ruby

Use `rbenv` to ensure the repo-local Ruby is selected:

```bash
rbenv versions
rbenv local 3.1.6
rbenv version
rbenv which ruby
```

If Bundler reports the wrong version, install and invoke the pinned one:

```bash
gem install bundler:2.6.9
bundle _2.6.9_ -v
```

If local verification accidentally picks up `/usr/bin/ruby`, fix the shell setup first rather than working around it repeatedly.

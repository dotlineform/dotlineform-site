---
doc_id: local-setup
title: "Local Setup"
last_updated: 2026-04-13
parent_id: scripts
sort_order: 30
---

# Local Setup

This guide centralizes the current local toolchain needed to run the Python scripts in this repo and to verify the Jekyll site locally.

For cloud-hosted development guidance, see [Cloud Environments](/docs/?scope=studio&doc=scripts-cloud-environments).

All commands below assume you are in `dotlineform-site/` unless stated otherwise.

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

## Required env vars

These two env vars are required for the media/generation workflow unless you pass explicit path flags:

```bash
export DOTLINEFORM_PROJECTS_BASE_DIR="/absolute/path/to/dotlineform"
export DOTLINEFORM_MEDIA_BASE_DIR="/absolute/path/to/dotlineform-icloud"
```

What they mean:

- `DOTLINEFORM_PROJECTS_BASE_DIR`: base directory that contains the source `projects/` and `moments/` trees used for dimension reads and source-media lookup
- `DOTLINEFORM_MEDIA_BASE_DIR`: base directory that contains staged source images, generated srcset output, and staged work downloads

Optional env var:

```bash
export MAKE_SRCSET_JOBS=4
```

This sets the default parallel worker count for srcset generation.

Two additional env vars are used by the srcset wrapper, but they are usually set per-command by pipeline scripts rather than persisted globally:

- `MAKE_SRCSET_WORK_IDS_FILE`
- `MAKE_SRCSET_SUCCESS_IDS_FILE`

Those manifest env vars do not normally need to be added to your shell startup files.

## Persisting env vars

On default macOS shells, add the exports to `~/.zshrc`:

```bash
export DOTLINEFORM_PROJECTS_BASE_DIR="$HOME/path/to/dotlineform"
export DOTLINEFORM_MEDIA_BASE_DIR="$HOME/path/to/dotlineform-icloud"
export MAKE_SRCSET_JOBS=4
```

If you use `bash`, add the same lines to `~/.bashrc` instead.

After editing your shell config, reload it:

```bash
source ~/.zshrc
```

Or for `bash`:

```bash
source ~/.bashrc
```

## Repo-specific operating notes

- Run project commands from `dotlineform-site/`.
- Prefer the project-local script form: `./scripts/...`.
- canonical catalogue metadata now lives under `assets/studio/data/catalogue/`.
- `data/works_bulk_import.xlsx` is only used for the separate bulk-import workflow for new works and new work details.
- Shared env var names and media subpaths are defined in `_data/pipeline.json`.
- The pipeline currently generates primary image variants at `800`, `1200`, and `1600` widths.
- Thumb sizes are currently `96` and `192`.
- The repo still accepts some legacy `2400` references in compatibility checks, but new moment variants should stay at `800`, `1200`, and `1600`.
- HEIC/HEIF input conversion uses macOS `sips` when available and otherwise falls back to `heif-convert`.
- Image derivative generation requires `ffmpeg`; the scripts fail fast if it is missing.
- Script logs are written locally under `logs/` and `var/studio/logs/`.

Common commands:

```bash
./scripts/audit_site_consistency.py --strict
python3 ./scripts/validate_catalogue_source.py
python3 ./scripts/catalogue_json_build.py --work-id 00001
python3 ./scripts/css_token_audit.py
bin/dev-studio
```

## Recovery after Xcode / Command Line Tools updates

Major macOS, Xcode, or Command Line Tools updates can disturb local shell startup behavior and tool resolution. The most common symptoms are:

- `brew`, `conda`, `rbenv`, `ruby`, or `python3` suddenly not found
- `bundle` starts using `/usr/bin/ruby` instead of the repo Ruby
- the shell stops loading exports from `.bashrc`, `.bash_profile`, or `.zshrc`
- previously working `ffmpeg` or `heif-convert` commands disappear from `PATH`

Recommended recovery checklist:

1. Confirm the shell you are actually using:

```bash
echo "$SHELL"
ps -p $$ -o command=
```

2. Re-open the terminal, then check whether the expected tools resolve:

```bash
which brew
which python3
which conda
which rbenv
which ruby
which bundle
```

3. If Homebrew is missing from `PATH`, restore the standard shell init line and reload the shell:

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

For persistence, that line should usually live in your shell startup file.

4. If `conda` no longer initializes correctly, re-run:

```bash
conda init zsh
```

Or for `bash`:

```bash
conda init bash
```

Then open a new shell and reactivate the environment:

```bash
conda activate dotlineform
```

5. If `rbenv` no longer initializes correctly, ensure your shell startup file contains:

```bash
eval "$(rbenv init - bash)"
```

For `zsh`, use:

```bash
eval "$(rbenv init - zsh)"
```

Then open a new shell and re-check:

```bash
rbenv version
ruby -v
bundle -v
```

6. If `bundle` is using the wrong Ruby after the update, reset to the repo version:

```bash
rbenv local 3.1.6
hash -r
ruby -v
bundle exec jekyll -v
```

7. If the update affected the Apple developer tools themselves, re-run:

```bash
xcode-select --install
```

If the CLT path looks wrong, check:

```bash
xcode-select -p
```

8. If `ffmpeg` or `heif-convert` disappeared after the update, verify the Homebrew installs:

```bash
brew list --versions ffmpeg libheif
ffmpeg -version | head -n 1
heif-convert --version
```

### Shell startup file note

On macOS, login-shell behavior often causes confusion:

- `zsh` usually reads `~/.zshrc`
- `bash` often reads `~/.bash_profile` for login shells, not `~/.bashrc`

If you keep your exports in `~/.bashrc`, make sure `~/.bash_profile` sources it:

```bash
if [ -f ~/.bashrc ]; then
  . ~/.bashrc
fi
```

That is one of the most likely fixes if a system update makes it look like your env vars or init hooks have vanished.

### Fast post-update validation

After any Xcode/CLT update, this is a good minimal smoke test:

```bash
which python3
python3 -V
python3 -c "import openpyxl; print(openpyxl.__version__)"
which ruby
ruby -v
bundle -v
ffmpeg -version | head -n 1
heif-convert --version
./scripts/audit_site_consistency.py --strict
```

## GitHub vs local setup

There is currently no checked-in `.github/workflows/` configuration in this repo. The site is configured as a GitHub Pages/Jekyll site, and the Ruby side is pinned by:

- `.ruby-version` -> `3.1.6`
- `Gemfile` -> `github-pages`
- `Gemfile.lock` -> `github-pages 232`, Bundler `2.6.9`, Jekyll `3.10.0`

The important practical difference is:

- GitHub Pages needs the Ruby/Jekyll stack to build and serve the site content
- local development also needs the Python/media toolchain because the repo's content-generation workflow happens outside GitHub Pages

In other words, GitHub Pages does not need to run:

- `openpyxl`
- `ffmpeg`
- `heif-convert`
- local filesystem lookups into your source-media directories

Those are local-only requirements because the workbook-driven generators and media pipeline run on your machine before the generated artifacts are committed.

Another local-only difference is Ruby selection. On macOS, it is easy to accidentally use `/usr/bin/ruby`, which can break local Bundler resolution. Using `rbenv` avoids that problem and makes local verification match the pinned repo versions more reliably.

For Codex/cloud sessions, keep this distinction explicit:

- use preinstalled Ruby for fast iteration on simple Ruby scripts when compatibility checks pass
- use pinned parity checks (Ruby/Bundler/Jekyll contract) before relying on publish-sensitive results

## Codex / AGENTS note

`AGENTS.md` already contains pertinent local runtime guidance for Codex, including:

- run Python commands from `dotlineform-site/`
- use the local Conda-managed Python interpreter
- prefer `./scripts/...` command forms
- rely on `DOTLINEFORM_PROJECTS_BASE_DIR` by default for source lookups
- pinned Ruby `3.1.6` and Bundler `2.6.9`
- preference for parity verification runs via pinned Bundler/Jekyll commands

This doc keeps the repo guidance generic and portable. Machine-specific interpreter paths should stay in `AGENTS.md`, not in user-facing repo docs.

---
doc_id: scripts-cloud-environments
title: Cloud Environments
last_updated: 2026-04-14
parent_id: scripts
sort_order: 35
---

# Cloud Environments (Codex + Codespaces + R2)

This guide defines a practical cloud-native setup for this repo while preserving the current local workflow.

## Goals

- run the full script and Jekyll workflow in cloud-hosted dev environments
- keep local and cloud command shapes consistent
- keep source-media and remote-media boundaries explicit
- avoid hardcoding machine-specific paths or credentials

## Scope

This page covers:

- Codex Cloud setup expectations
- GitHub Codespaces runtime/bootstrap setup
- Cloudflare R2 environment contract for media workflows
- compatibility checks for local versus non-local runs

## Baseline Runtime Contract

The target parity baseline for publish-sensitive checks remains:

- Python `3.12.7`
- Python package `openpyxl 3.1.5`
- Ruby `3.1.6`
- Bundler `2.6.9`
- Jekyll `3.10.0`
- `github-pages` gem `232`

Treat this as the compatibility target for local and cloud environments when you need predictable publish parity. Codex setup currently validates Ruby/Bundler availability but does **not** force Ruby `3.1.6` when a newer compatible Ruby is already active.

### Runtime modes

Cloud sessions can run in three practical modes:

- **Fast script mode**: use preinstalled cloud runtimes and skip optional media packages.
- **Fast + media mode**: same as fast mode, but include media packages when source conversion is needed (`ffmpeg`, `libheif` tools).
- **Parity mode**: use the pinned Ruby/Bundler/Jekyll stack to match local + GitHub Pages behavior.

Use parity mode for publish-sensitive flows (for example `bundle exec jekyll build --quiet`, docs rendering through Jekyll converters, and final verification before committing generated artifacts).

## Implementation Steps

### 1) Add Codex instruction contract (repo root)

Keep a repo-root `AGENTS.md` section specifically for cloud runs.

Required guidance:

- run from repo root (`dotlineform-site/`)
- prefer project-local script entrypoints (`./scripts/...`)
- keep generator runs dry-run by default
- verify Python, Ruby, and Jekyll versions before reporting environment issues
- never hardcode R2 credentials; use environment variables and platform secrets stores

### 2) Add Codespaces runtime files

Commit a `.devcontainer/` setup that installs:

- Python runtime at the pinned major/minor line
- Ruby `3.1.6` + Bundler `2.6.9`
- `ffmpeg`
- `libheif` toolchain (`heif-convert` availability)

Recommended bootstrap actions in `postCreateCommand`:

- install Python deps from `requirements.txt`
- run `bundle _2.6.9_ install`
- print version checks

### 2.1) Add a Codex setup script entrypoint

Use `.codex/setup.sh` as the single setup/bootstrap script for Codex cloud sessions.

Current behavior:

- run an apt phase (skipped when required commands already exist, or when apt/sudo is unavailable)
- create/reuse `.venv`, upgrade pip, and install `requirements.txt`
- verify Ruby runtime exists, detect Bundler, then run `bundle config set --local path vendor/bundle` + `bundle install`
- print version diagnostics (`python3`, `ruby`, `bundle`, optional `ffmpeg`) and local bundle config
- avoid interactive sudo prompts (non-interactive only)

Notes:

- `.codex/setup.sh` does not run docs/search/site builders by default; run those explicitly as follow-up verification.
- Optional media packages are controlled by `SETUP_INSTALL_MEDIA_PACKAGES=1` during setup apt install.
- apt package install can be skipped with `SETUP_SKIP_APT=1`; forced with `FORCE_APT_PACKAGES=1`.
- If Bundler is missing or incompatible with the lockfile, setup installs a fallback user Bundler (optionally pinned via `BUNDLER_FALLBACK_VERSION`).
- Keep Bundler/Jekyll checks pinned for parity verification runs.

### Calling setup.sh by runtime mode

Always run from repo root:

```bash
bash .codex/setup.sh
```

Fast script mode (default):

```bash
SETUP_SKIP_APT=1 bash .codex/setup.sh
```

Fast + media mode (force apt + install media dependencies where apt is available):

```bash
FORCE_APT_PACKAGES=1 SETUP_INSTALL_MEDIA_PACKAGES=1 bash .codex/setup.sh
```

Why force apt here:

- `.codex/setup.sh` skips apt when baseline commands already exist (`can_skip_apt_packages`).
- that baseline check currently does not validate `ffmpeg`/`libheif` tools.
- in cloud images that already have Python/build tooling but not media tooling, using only `SETUP_INSTALL_MEDIA_PACKAGES=1` can still skip apt and leave media dependencies missing.

Parity mode (force apt refresh and pin fallback Bundler when needed):

```bash
FORCE_APT_PACKAGES=1 BUNDLER_FALLBACK_VERSION=2.6.9 bash .codex/setup.sh
```

Codespaces post-create mode:

- `.devcontainer/post-create.sh` calls `bash .codex/setup.sh` directly.
- Ensure the image already contains system dependencies expected by setup, because post-create usually runs as non-root and setup will skip apt when sudo is unavailable.

If Codex Cloud supports setup script paths in environment config, point that field to:

```bash
bash .codex/setup.sh
```

### 3) Keep dependency declarations machine-readable

- Python deps in `requirements.txt`
- Ruby deps in `Gemfile` + `Gemfile.lock`
- Ruby runtime in `.ruby-version`

### 4) Define cloud-safe env vars

Minimum shared variables for media/generation scripts:

- `DOTLINEFORM_PROJECTS_BASE_DIR`
- `DOTLINEFORM_MEDIA_BASE_DIR`
- optional `MAKE_SRCSET_JOBS`

R2-related variables should be configured through cloud secret stores, for example:

- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`
- `R2_ENDPOINT`

### 5) Keep remote-media boundary explicit

- treat canonical source media under `DOTLINEFORM_PROJECTS_BASE_DIR` as separate from remote media origins
- use `_config.yml` `media_base` values for remote URL rendering
- do not couple cleanup flows to remote storage state

## Local + Cloud Compatibility Workflow

Use the same command sequence in both environments:

1. environment checks
2. dry-run source/build checks
3. docs/search/site validation

Example check sequence:

```bash
./scripts/audit_site_consistency.py --strict
python3 ./scripts/validate_catalogue_source.py
python3 ./scripts/catalogue_json_build.py --work-id 00001
./scripts/build_docs.rb
./scripts/build_search.rb
bundle exec jekyll build --quiet
```

## Verification Matrix

### Codex-run checks

- verify active versions for Python/Ruby/Bundler/Jekyll
- run at least one dry-run catalogue build
- run docs and search builders in dry-run mode where supported
- run one Jekyll build smoke check

### Manual checks

- open home page and one work page in local preview
- open `/docs/` and confirm new docs render
- verify media URLs resolve to intended origin for the active environment

## Benefits

- faster cloud bootstrap for script-heavy work by reusing preinstalled runtimes
- explicit parity fallback for publish-sensitive checks
- predictable onboarding for non-local development sessions without forcing unnecessary runtime installs

## Risks

- runtime drift can mask compatibility issues if parity checks are skipped
- Linux cloud images may differ from macOS behavior for image conversion tooling
- unavailable source media roots in cloud sessions can block generation commands
- accidental credential handling in logs/docs if secret boundaries are not respected

## Version-Drift and Incompatibility Handling

Potential future incompatibilities and how they surface:

- **Ruby/Bundler lockfile mismatch**: setup output will show Bundler mismatch against `Gemfile.lock`; bundler install retries with fallback and surfaces hard failure if unresolved.
- **Python dependency floor changes**: pip install errors in setup python phase will fail early before generator/build commands run.
- **Jekyll/github-pages drift**: incompatibilities appear during explicit follow-up checks (`./scripts/build_docs.rb`, `bundle exec jekyll build --quiet`) even if setup itself passes.
- **Media toolchain drift**: `ffmpeg`/`heif-convert` failures appear in media generation commands; setup only verifies `ffmpeg` when present.

Recommended response loop:

1. rerun setup with parity-oriented flags (`FORCE_APT_PACKAGES=1 BUNDLER_FALLBACK_VERSION=2.6.9`)
2. run full parity checks (`./scripts/build_docs.rb`, `./scripts/build_search.rb`, `bundle exec jekyll build --quiet`)
3. if mismatch persists, update pinned versions in `.ruby-version`, `Gemfile.lock`, and cloud runtime files together (plus docs) in one change set

## Codespaces Consistency Notes

Current Codespaces wiring is consistent:

- `postCreateCommand` runs `.devcontainer/post-create.sh`
- post-create delegates to `.codex/setup.sh`
- Dockerfile preinstalls `ffmpeg` and `libheif-examples`, so media tooling is available even when setup apt is skipped

Watch-outs:

- if Dockerfile package/runtime pins change, re-run setup and parity checks in Codespaces to ensure post-create still succeeds without sudo
- if setup begins requiring new system packages, add them to Dockerfile to avoid post-create apt-skip gaps

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Local Setup](/docs/?scope=studio&doc=local-setup)
- [Scoped JSON Catalogue Build](/docs/?scope=studio&doc=scripts-build-catalogue-json)
- [Pipeline Config JSON](/docs/?scope=studio&doc=config-pipeline-json)
- [Jekyll Site Config](/docs/?scope=studio&doc=config-jekyll-site-config)

---
doc_id: scripts-cloud-environments
title: Cloud Environments (Codex + Codespaces + R2)
last_updated: 2026-04-07
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

The current pinned runtime remains:

- Python `3.12.7`
- Python package `openpyxl 3.1.5`
- Ruby `3.1.6`
- Bundler `2.6.9`
- Jekyll `3.10.0`
- `github-pages` gem `232`

Treat this as a shared baseline for local and cloud environments.

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

Current intent:

- install and verify the pinned Ruby/Bundler/Python runtime
- install repo Python/Ruby dependencies
- run a docs-builder smoke check (`./scripts/build_docs.rb`)

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
2. dry-run generation checks
3. docs/search/site validation

Example check sequence:

```bash
./scripts/audit_site_consistency.py --strict
./scripts/build_catalogue.py --dry-run --no-confirm
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

- one runtime contract across local and cloud
- fewer false environment failures from mismatched Ruby/Bundler
- predictable onboarding for non-local development sessions

## Risks

- Linux cloud images may differ from macOS behavior for image conversion tooling
- unavailable source media roots in cloud sessions can block generation commands
- accidental credential handling in logs/docs if secret boundaries are not respected

## Related References

- [Scripts](/docs/?scope=studio&doc=scripts)
- [Local Setup](/docs/?scope=studio&doc=local-setup)
- [Build Catalogue](/docs/?scope=studio&doc=scripts-main-pipeline)
- [Pipeline Config JSON](/docs/?scope=studio&doc=config-pipeline-json)
- [Jekyll Site Config](/docs/?scope=studio&doc=config-jekyll-site-config)

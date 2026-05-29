---
doc_id: local-setup-github-codex
title: Local Setup GitHub And Codex Notes
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: local-setup
---
# Local Setup GitHub And Codex Notes

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

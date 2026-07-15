---
doc_id: local-setup-environment
title: Local Setup Environment
added_date: 2026-05-19
last_updated: 2026-07-15
parent_id: local-setup
---
# Local Setup Environment

## Local Source

Use the gitignored repo-local `.env.local` for machine-specific workspace roots, runner overrides, concurrency, and publishing credentials.

```bash
$EDITOR .env.local
```

Local runners/services load it server-side. Browser code must never read it or receive credentials. In cloud/Codespaces, use configured environment variables and secret stores instead.

The shared loader gives `.env.local` precedence over inherited process values for local runs; if the file is absent, process environment remains available for cloud/container use.

## Stable Variable Families

### External Workspaces

`DOTLINEFORM_PROJECTS_BASE_DIR` is the base for marker-rooted external workspaces such as:

- `data-sharing/` — exports, shared import staging, metadata, review previews;
- `docs-viewer/` — external local scopes;
- catalogue/media working roots owned by media configuration/resolvers.

Create the required child workspace before using that capability. There is no repo-local fallback for these external roots.

### Runners

Each local app/server owns host, port, logging, and enable/disable overrides in its runner/server source. `bin/local-all` composes sibling enable flags; it does not change their independent ownership.

Read the runner and `.env.local.example` if present for exact current variable names. Do not maintain an exhaustive list here.

### Media Concurrency/Manifests

Media/srcset scripts may read shared concurrency or per-run manifest variables. Prefer per-command/internal orchestration for temporary manifest paths rather than persisting them globally.

### Remote Publishing

R2 account/key/bucket/endpoint values belong only in `.env.local` or a platform secret store. Publisher errors may name missing variables but must not print values.

## Change Method

- Add a variable only for a real environment-specific choice; stable product policy belongs in checked config.
- Define/default/read it in one runner/service owner.
- Keep browser runtime projection free of secrets and private absolute paths.
- Use marker paths in responses/docs when an external workspace must be displayed.
- Update this page only when a variable family, precedence rule, or workspace ownership changes.

## Operating Baseline

- run commands from `dotlineform-site/`;
- use the configured Miniconda interpreter locally;
- use project-local `bin/`/script entrypoints;
- keep canonical catalogue/tag/docs source in its current app-owned tree;
- treat generated media and local logs/reports as disposable/ignored outputs unless a focused workflow says otherwise.

## Weak Spots

- `.env.local` is shell syntax and can become an unvalidated second config file.
- One base directory serves several external-workspace families; misconfigured ownership can affect multiple apps.
- Runner variable inventories drift quickly, so code discovery is required for exact names/defaults.
- Local precedence over process environment can surprise a shell user who expects an exported override to win.

---
draft: false
doc_id: d-20260519-210908-965f46
title: Local Setup Environment
added_date: 2026-05-19 21:09:08
last_updated: "2026-11-18"
parent_id: d-20260413-000000-d314b7
---
# Local Setup Environment

## Local Source

Use the gitignored repo-local `.env.local` for machine-specific workspace roots, runner overrides, concurrency, and publishing credentials.

```bash
$EDITOR .env.local
```

Local runners/services load it server-side. Browser code must never read it or receive credentials. In cloud/Codespaces, use configured environment variables and secret stores instead.

Precedence belongs to each entry point. The common builder bootstrap loads `.env.local` over inherited values. The standalone Docs Viewer service reads `.env.local` and then applies inherited values and explicit runner arguments. Keep local settings consistent across a workflow that uses both.

## Stable Variable Families

### External Workspaces

`DOTLINEFORM_DOCS_BASE_DIR` selects the existing Docs workspace containing Working and Preview. `DOTLINEFORM_PROJECTS_BASE_DIR` independently selects the existing Projects workspace for Catalogue staging, configured original Work media and project-owned files. Point each variable at its own configured root. [Workspace roles](../reference/Source_Organisation.md#storage-and-roles) · [Catalogue media authoring](Catalogue_Save_And_Refresh.md#work-media-authoring)

A Processing application launched from the GUI does not read `.env.local`. Its ignored project-local output configuration receives the same external base plus one exact project identity; Studio and Catalogue continue to resolve their roots from the server environment and checked media configuration.

### Runners

Each local app/server owns host, port, logging, and enable/disable overrides in its runner/server source. `bin/local-all` composes sibling enable flags; it does not change their independent ownership.

Read the runner and `.env.local.example` if present for exact current variable names. Do not maintain an exhaustive list here.

Set `DOCS_VIEWER_MANAGEMENT_ENABLED=1` to use authoring controls at the local `/docs/` route. [Local runners](Local_Runners.md#default-boundaries)

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
- keep canonical Catalogue and document source with their respective owners;
- treat generated media and local logs/reports as disposable/ignored outputs unless a focused workflow says otherwise.

## Weak Spots

- `.env.local` is shell syntax and can become an unvalidated second config file.
- The two configured bases have independent owners and must be available for the operations that use them.
- Runner variable inventories drift quickly, so code discovery is required for exact names/defaults.

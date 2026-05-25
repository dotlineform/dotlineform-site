---
doc_id: site-request-committed-manage-mode-scope-storage
title: Committed Manage-Mode Scope Storage Request
added_date: 2026-05-25
last_updated: 2026-05-25
ui_status: draft
parent_id: change-requests
sort_order: 93000
viewable: true
---
# Committed Manage-Mode Scope Storage Request

Status:

- requested

## Summary

Define the storage contract for repo-tracked Docs Viewer scopes that are manage-mode only.

The current New Scope workflow distinguishes public, local committed, and local uncommitted modes, but local committed scope previews still use the same generated output roots as public scopes: `assets/data/docs/scopes/<scope>/` and `assets/data/search/<scope>/index.json`.
That makes manage-mode internal docs look deployable and places internal generated runtime payloads under the public static asset tree.

This request is the near-term path for Studio and any archive/internal scopes that should live in the repo but should not publish as public Docs Viewer routes.

## Goal

Make `local_committed` mean repo-tracked manage-mode scope.

The desired end state is:

- public read-only scopes continue to publish static runtime payloads under `assets/`
- committed manage-mode scopes are available through `/docs/?scope=<scope>&mode=manage` and travel with the repo
- committed manage-mode scopes do not create public read-only routes
- committed manage-mode scopes do not publish generated runtime payloads under `assets/`
- committed manage-mode generated docs/search payloads live under a tracked Docs Viewer-owned non-public generated-data path
- the existing `studio` scope is migrated to the committed manage-mode contract
- New Scope preview/apply accurately shows different write sets for public read-only and committed manage-mode scopes

## Current Behaviour

The New Scope preview currently reports the same generated runtime output roots for all publishing modes when immediate generated writes are enabled:

- `assets/data/docs/scopes/<scope>/`
- `assets/data/docs/scopes/<scope>/index.json`
- `assets/data/docs/scopes/<scope>/by-id/`
- `assets/data/search/<scope>/index.json`

For a repo-tracked manage-mode scope, source Markdown can reasonably live in the repo, but generated runtime payloads should not look like public site assets.

## Required Contract

### Public Read-Only Scope

Public read-only scopes are deployable static site scopes.

They should use:

- source root: `docs-viewer/source/<scope>/`
- generated docs output: `assets/data/docs/scopes/<scope>/`
- generated search output: `assets/data/search/<scope>/index.json`
- optional public route: `/<scope>/`

Generated payloads under `assets/` are public runtime assets.

### Committed Manage-Mode Scope

Committed manage-mode scopes should travel with the repo but should not publish static runtime payloads.
Studio is the primary example.

They should use:

- manage-mode access only: `/docs/?scope=<scope>&mode=manage`
- no public read-only route
- repo-tracked source Markdown
- generated runtime output under a tracked Docs Viewer-owned non-public generated-data path, not `assets/` or `var/`
- explicit `.gitignore` exceptions or an equivalent tracked-path strategy if the selected path is otherwise ignored

The implementation must choose and document the exact tracked non-public path.
A candidate shape is `docs-viewer/generated/docs/<scope>/` for generated docs payloads and `docs-viewer/generated/search/<scope>/index.json` for generated search payloads, but the final path should be selected with the runtime reader and builder contracts in mind.

## Studio Migration

The existing `studio` scope should migrate to committed manage-mode.

Migration requirements:

- `studio` remains reachable through the local Docs Viewer manage-mode route
- generated Studio docs/search runtime payloads move out of `assets/data/docs/scopes/studio/` and `assets/data/search/studio/`
- the replacement generated Studio payloads live under the selected tracked Docs Viewer-owned non-public path
- local Studio startup, live rebuild, Docs Viewer service reads, and Docs Viewer search reads all use the new committed manage-mode output path
- public static site builds do not need Studio generated payloads under `assets/`
- docs and tests stop treating `studio` generated runtime assets as public static assets

## Relationship To Workspace Mount Architecture

This request deliberately does not solve true non-repo local scopes.

External user/application data belongs in [Docs Viewer Workspace Mount Architecture Request](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-workspace-mount-architecture).
That larger request will eventually generalize scope path resolution so Docs Viewer can mount repo-backed and non-repo workspaces through the same abstraction.

This near-term request is still useful because it fixes the immediate publication-boundary problem for Studio and local committed scopes.
The expected implementation and tests should be written so they can migrate into the workspace model later.

## Decisions

- Committed manage-mode source Markdown stays under `docs-viewer/source/<scope>/`.
  This request does not change Docs Viewer source ownership; it only changes where committed manage-mode generated runtime payloads live.
- Committed manage-mode generated JSON is tracked, the same as public scope generated JSON.
  Manage-mode status changes where the generated payloads live, not whether they are committed.
- Committed manage-mode generated JSON should not live under `var/`.
  In this repo, `var/` means local working output, backups, logs, staging, caches, and test artifacts.
  Use a tracked Docs Viewer-owned generated-data path, such as `docs-viewer/generated/docs/<scope>/` and `docs-viewer/generated/search/<scope>/index.json`.
- Generated docs payload readers should resolve from each scope's configured `output` field.
  The scope config already states the generated docs output folder.
- Generated search payload readers should resolve from an explicit scope config field, such as `search_output`.
  Public scopes should configure docs/search outputs under `assets/`; committed manage-mode scopes should configure docs/search outputs under `docs-viewer/generated/`.
  Public read-only routes remain static and portable because their configured outputs remain public assets, while manage-mode reads can be served by the local Docs Viewer service from the configured non-public generated paths.

## Committed Manage-Mode Output Contract

Committed manage-mode generated docs payloads should use:

- docs payload root: `docs-viewer/generated/docs/<scope>/`
- docs index: `docs-viewer/generated/docs/<scope>/index.json`
- docs by-id payloads: `docs-viewer/generated/docs/<scope>/by-id/`
- docs references payloads, when present: `docs-viewer/generated/docs/<scope>/references/`

Committed manage-mode generated search payloads should use:

- search payload root: `docs-viewer/generated/search/<scope>/`
- search index: `docs-viewer/generated/search/<scope>/index.json`

Generated JSON under `docs-viewer/generated/` is tracked for `local_committed` scopes.
It is generated runtime data, not source Markdown, but it travels with the repo so local manage-mode scopes can load without requiring every checkout to rebuild before first use.

`docs-viewer/generated/` is not a public static asset path.
The path sits under the Docs Viewer-owned package boundary rather than `assets/`, and the public Jekyll config excludes `docs-viewer/` from public builds.
Public read-only routes therefore continue to publish from configured `assets/data/docs/scopes/<scope>/` and `assets/data/search/<scope>/index.json` paths, while committed manage-mode scopes are served through the local Docs Viewer service from configured non-public generated outputs.

## Implementation Tasks

### Task 1. Define Committed Manage-Mode Output Paths

Status:

- completed

Choose the path contract for committed manage-mode generated docs/search payloads.

Required output:

- exact docs payload root
- exact search payload root
- tracked generated JSON behavior
- docs explaining why these outputs are not public static assets

### Task 2. Extend Scope Config For Non-Public Outputs

Status:

- completed

Update the scope config model so a scope can distinguish public static output from committed manage-mode output.

The builder and runtime should not infer public-ness only from the presence of `assets/data/...` paths.
The existing `output` field should remain the generated docs payload root.
Add an explicit generated search output field, such as `search_output`, so search readers and builders do not assume `assets/data/search/<scope>/index.json`.

Implementation note:

- `docs-viewer/config/scopes/docs_scopes.json` now carries `search_output` for each configured scope.
- Python scope config readers expose `DocsScopeConfig.search_output`.
- Docs generated-read helpers, source config reporting, scope lifecycle planning, and Ruby Docs Viewer builders use the configured `search_output`.
- Existing public/static behavior is preserved for current scopes by setting `search_output` to the existing `assets/data/search/<scope>/index.json` paths; moving Studio to `docs-viewer/generated/search/studio/index.json` remains part of the Studio migration task.

### Task 3. Update New Scope Preview And Apply

Status:

- completed

Change the New Scope lifecycle planner so the created/changed file list reflects the selected publishing mode.

Required behavior:

- public read-only previews continue to show `assets/` generated output
- committed manage-mode previews show tracked non-public source and generated output
- preview copy makes the public-vs-manage-mode boundary explicit before apply

Implementation note:

- create preview and create apply now share the same planned scope config record.
- public read-only scopes plan generated docs/search outputs under `assets/data/docs/scopes/<scope>/` and `assets/data/search/<scope>/index.json`.
- committed manage-mode scopes plan generated docs/search outputs under `docs-viewer/generated/docs/<scope>/` and `docs-viewer/generated/search/<scope>/index.json`.
- preview/apply responses include a `storage_contract` object that states whether generated output is public static asset data and lists the docs/search output paths shown in the preview modal.
- the UI labels `local_committed` as a committed manage-mode scope and renders the storage contract before the file write set.

### Task 4. Migrate Studio To Committed Manage-Mode

Status:

- not started

Move the existing `studio` generated runtime payload contract from public `assets/` paths to the selected committed manage-mode paths.

Update affected readers, builders, startup scripts, smoke tests, and docs.

### Task 5. Add Guardrails

Status:

- not started

Add checks that prevent manage-mode-only generated runtime payloads from being written under public `assets/` roots unless the scope is explicitly public read-only.

At minimum, cover:

- scope lifecycle preview/apply tests
- docs build output path tests
- Docs Viewer service reads for committed manage-mode scopes
- search reads for committed manage-mode scopes
- a regression check that Studio no longer requires generated payloads under `assets/`

### Task 6. Update Documentation

Status:

- not started

Update the owning Docs Viewer docs after implementation:

- New Scopes Builder
- Portable Scope Setup
- data model or projection-contract docs that distinguish source, public generated assets, and committed manage-mode generated runtime payloads
- local Studio operating guidance

## Acceptance Criteria

- `local_committed` in the New Scope UI and docs means repo-tracked manage-mode scope.
- Creating a committed manage-mode scope does not write generated runtime payloads under `assets/`.
- Studio no longer depends on generated docs/search payloads under public `assets/` paths.
- Public read-only scopes continue to work from static `assets/` payloads.
- The preview write set is mode-specific and matches the actual apply behavior.

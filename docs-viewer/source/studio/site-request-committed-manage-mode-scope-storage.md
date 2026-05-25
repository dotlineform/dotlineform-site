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
- committed manage-mode generated docs/search payloads live under a tracked non-public path
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
- generated runtime output under a tracked non-public path, not `assets/`
- explicit `.gitignore` exceptions or an equivalent tracked-path strategy if the selected path is otherwise ignored

The implementation must choose and document the exact tracked non-public path.
A candidate shape is `var/docs-viewer/committed/scopes/<scope>/` for generated docs payloads and `var/docs-viewer/committed/search/<scope>/index.json` for generated search payloads, but the final path should be selected with the runtime reader and builder contracts in mind.

## Studio Migration

The existing `studio` scope should migrate to committed manage-mode.

Migration requirements:

- `studio` remains reachable through the local Docs Viewer manage-mode route
- generated Studio docs/search runtime payloads move out of `assets/data/docs/scopes/studio/` and `assets/data/search/studio/`
- the replacement generated Studio payloads live under the selected tracked non-public path
- local Studio startup, live rebuild, Docs Viewer service reads, and Docs Viewer search reads all use the new committed manage-mode output path
- public static site builds do not need Studio generated payloads under `assets/`
- docs and tests stop treating `studio` generated runtime assets as public static assets

## Relationship To Workspace Mount Architecture

This request deliberately does not solve true non-repo local scopes.

External user/application data belongs in [Docs Viewer Workspace Mount Architecture Request](/docs/?scope=studio&mode=manage&doc=site-request-docs-viewer-workspace-mount-architecture).
That larger request will eventually generalize scope path resolution so Docs Viewer can mount repo-backed and non-repo workspaces through the same abstraction.

This near-term request is still useful because it fixes the immediate publication-boundary problem for Studio and local committed scopes.
The expected implementation and tests should be written so they can migrate into the workspace model later.

## Open Design Questions

- Should committed manage-mode source Markdown stay under `docs-viewer/source/<scope>/`, or move under a Studio-owned source path?
- Should committed manage-mode generated payloads be tracked under `var/`, or should they be reproducible local cache with only source/config tracked?
- What non-public path naming should distinguish committed manage-mode generated payloads from disposable local runtime output?
- How should generated payload readers resolve a committed manage-mode scope whose output root is outside `assets/` while keeping public read-only routes static and portable?

## Implementation Tasks

### Task 1. Define Committed Manage-Mode Output Paths

Status:

- not started

Choose the path contract for committed manage-mode generated docs/search payloads.

Required output:

- exact docs payload root
- exact search payload root
- tracked/ignored behavior
- docs explaining why these outputs are not public static assets

### Task 2. Extend Scope Config For Non-Public Outputs

Status:

- not started

Update the scope config model so a scope can distinguish public static output from committed manage-mode output.

The builder and runtime should not infer public-ness only from the presence of `assets/data/...` paths.

### Task 3. Update New Scope Preview And Apply

Status:

- not started

Change the New Scope lifecycle planner so the created/changed file list reflects the selected publishing mode.

Required behavior:

- public read-only previews continue to show `assets/` generated output
- committed manage-mode previews show tracked non-public source and generated output
- preview copy makes the public-vs-manage-mode boundary explicit before apply

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

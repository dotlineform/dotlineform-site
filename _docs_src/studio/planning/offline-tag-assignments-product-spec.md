---
doc_id: offline-tag-assignments-product-spec
title: Offline Tag Assignments Product Spec
last_updated: 2026-03-28
parent_id: plan
---

# Offline Tag Assignments Product Spec

Status:

- locked v1 planning spec
- no implementation details in this document beyond product-facing behavior

## Summary

Offline tag-assignment editing stages final per-series assignment rows in browser `localStorage`, keyed by `series_id`.

This applies when:

- the local server is unavailable
- a live save fails and the editor falls back to offline mode

The staged data is session-wide across series and is managed from the Series Tags page.

## Scope

Primary surfaces:

- Series Tag Editor
- Series Tags page
- local write server assignment import flow

Primary goals:

- offline editing behaves like a real save workflow across series
- staged local assignment state is visually distinct from repo-backed assignment state
- staged data can be exported and later imported when the local server is available

## Save Semantics

Offline mode uses debounced autosave plus the existing `Save Tags` action.

Behavior:

- when local server mode is available, existing save behavior stays in place
- when local server mode is unavailable, changes are staged into `localStorage`
- when a live save fails, the editor switches to offline mode and stages locally
- offline stage advances the editor baseline so subsequent diffs are calculated from the staged row, not the repo JSON
- on page load, a staged row for the current series overlays the repo-backed row before editor state is built

## Staged Data Model

Offline storage uses one global session in `localStorage`.

Per-series staged data includes:

- `base_series_updated_at_utc`
- `base_row_snapshot`
- `staged_row`
- `staged_at_utc`

The staged payload stores final normalized series rows, not incremental patch operations.

Assignment rows in staged storage, export payloads, and import payloads must preserve the `tag_assignments.json` object schema:

- `{ "tag_id": "<group>:<slug>", "w_manual": 0.3|0.6|0.9, "alias"?: "<alias>" }`

The optional `alias` field is historical metadata only, but it must round-trip unchanged through offline staging, export, import, and conflict detection.

## Session Hub

The Series Tags page owns the offline session controls.

Session strip responsibilities:

- show staged series count
- show session last updated time
- provide `Copy JSON`
- provide `Download JSON`
- provide `Clear session`
- provide `Import assignments` when the local server is available
- surface import preview and conflict results

## Mobile Export Behavior

Mobile use is in scope.

Export priorities:

- `Copy JSON` is the primary export path
- `Download JSON` is secondary

`Share JSON` is out of scope for v1.

## Assignment State Styling

Local-vs-repo assignment state is shown in both:

- Series Tag Editor
- Series Tags page

Locked styling rules:

- no icon-only markers
- local markers are text captions below the chip
- captions use `--font-caption`
- locally added or locally modified assignments show caption `local`
- locally deleted repo assignments use struck-through chip text plus caption `delete`
- no ghost styling is used for pending deletion
- the same chip-state treatment is used in the editor and on the Series Tags page

These markers indicate local assignment state, not non-canonical tags. Canonicality still comes from the tag registry.

Local assignment state is determined by persisted assignment-row equality, not only by visible chip text. An alias-only difference still counts as a local staged modification even though alias metadata is not shown in the UI.

## Import and Conflict Handling

A new assignment import flow is added to the local write server.

Conflict model:

- conflict granularity is per series row
- no tag-level merge logic in v1
- if the current repo row matches the stored base snapshot, the staged row can auto-apply
- if the current repo row differs from the stored base snapshot, including optional hidden metadata such as `alias`, that series is a conflict
- for each conflicting series, the user chooses `overwrite` or `skip`
- `overwrite` means full replacement of the target series row from staged data
- `skip` leaves the repo row unchanged

Validation failures are not conflicts:

- missing series ids
- invalid work ids
- malformed payload rows

Import flow:

- preview endpoint returns per-series status
- conflict review UI lives on the Series Tags page
- apply endpoint imports all approved rows in one request

## UI Text

All new user-facing copy must be stored in `assets/studio/data/studio_config.json` under `ui_text`.

This includes:

- session strip labels
- offline save and status messages
- chip captions
- import preview and conflict copy
- clear-session copy
- export copy

## Benefits

- offline mode behaves like a true staged-save workflow across series
- users can distinguish repo-backed assignments from local staged changes
- conflict handling stays understandable because it is series-row based
- mobile use is supported because copy/export is first-class

## Risks

- editor and list UI become more stateful and visually complex
- `localStorage` is suitable for drafts, not durable archival storage
- assignment import preview and apply add meaningful server and UI scope
- series-level conflict handling is deliberately simpler than merge logic

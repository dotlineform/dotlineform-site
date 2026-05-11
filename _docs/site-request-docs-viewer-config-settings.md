---
doc_id: site-request-docs-viewer-config-settings
title: Docs Viewer Config And Settings Request
added_date: 2026-05-11
last_updated: "2026-05-11 19:46"
ui_status: proposed
parent_id: change-requests
sort_order: 28
hidden: false
---
# Docs Viewer Config And Settings Request

Status:

- proposed

## Summary

Clarify the Docs Viewer configuration model and add a management UI for user-editable settings.

The current portable viewer work introduced a useful split:

- `scripts/docs/docs_scopes.json` is the source-side install/build registry
- `assets/docs-viewer/data/docs-viewer-config.json` is the browser-facing generated scope registry
- `assets/data/docs/scopes/<scope>/index.json.viewer_options` carries per-corpus viewer behavior inside generated docs output

That split is functional, but it now needs a clearer contract.
Some options are installation choices, some are generated data behavior, and some should eventually be editable by a user in Docs Viewer manage mode.

## Problem

The same broad idea, Docs Viewer configuration, is spread across several files with different owners and lifecycles.
This makes it harder to answer basic questions:

- which settings are part of installing a Docs Viewer corpus
- which settings are generated and should not be edited directly
- which settings are safe for a user to change in the browser
- which settings belong to the public read-only viewer versus local management mode
- which settings should be copied into another Jekyll project

The immediate example is `show_updated_date`.
It is defined in `scripts/docs/docs_scopes.json`, projected into generated `index.json.viewer_options`, and consumed by the browser runtime.
That may be acceptable for data-tree behavior, but it is less clear for a user-facing display preference that could reasonably be changed from a settings modal.

## Goals

- document the purpose and ownership of each Docs Viewer config file
- classify settings as install-time, generated-data, user-editable, or runtime-only
- decide which settings should remain in generated docs indexes and which should move into browser config
- add a management-mode settings button and modal for safe user-editable settings
- keep public read-only routes free of local write behavior
- avoid reintroducing hardcoded scope lists or route maps in the viewer runtime

## Non-Goals

- replacing the whole portable Docs Viewer config system in one slice
- moving Docs Search ownership at the same time
- making public read-only routes write settings
- adding account/auth concepts
- treating generated JSON files as hand-edited source files

## Current Config Surfaces

| Surface | Current purpose | Edit model |
| --- | --- | --- |
| `scripts/docs/docs_scopes.json` | source roots, generated output paths, route bases, default docs, validation/build behavior | install-time source config |
| `assets/docs-viewer/data/docs-viewer-config.json` | browser-safe scope registry generated from scope config | generated; do not hand edit |
| `assets/data/docs/scopes/<scope>/index.json.viewer_options` | options bundled with generated docs tree data | generated; do not hand edit |
| `assets/docs-viewer/data/ui-text.json` | Docs Viewer UI copy | package/source config for now |
| `assets/studio/data/studio_config.json` | remaining Studio-owned UI/status settings consumed by Docs Viewer | transitional dependency |

## Settings Classification

Install-time settings:

- source root
- generated output root
- public route base
- default doc id
- whether generated viewer links include `scope`
- nested-source and unresolved-parent validation policy

Generated-data settings:

- non-loadable doc ids
- manage-only tree root ids
- any future behavior tightly coupled to generated tree shape

Candidate user-editable settings:

- show or hide updated dates
- default recent-doc count
- per-scope display preferences
- possibly future nav/tree display defaults

Runtime-only settings:

- active selected scope
- active selected doc
- search query
- management mode availability
- transient local server capability state

## Proposed UX

Add a Settings button to the Docs Viewer management toolbar.

The button opens a modal scoped to the active Docs Viewer scope.
The first version should be deliberately small and only expose low-risk display settings.
It should make the distinction between local management settings and public viewer output clear through behavior, not explanatory in-app text.

Initial controls could include:

- show updated dates
- recently added limit

The modal should:

- load current effective settings for the active scope
- save through the local docs-management server
- trigger or request the minimal rebuild needed for generated browser/config payloads
- leave public read-only routes with no write surface
- show a clear unavailable state if the management server is not running

## Storage Direction

Use a source-side settings file as the editable record rather than editing generated files.
The exact file can be decided in implementation, but the design should preserve these rules:

- generated files are outputs, not the source of truth
- browser config is generated from source-side config/settings
- user-editable settings have an explicit allowlist
- settings writes stay under the Docs Viewer local server allowlist

Possible storage shapes:

- extend `scripts/docs/docs_scopes.json` with a clearly named user-editable settings section
- add a separate `scripts/docs/docs_viewer_settings.json`
- add per-scope settings files under a Docs Viewer-owned config directory

The implementation should choose the smallest shape that keeps install-time config understandable and does not make generated payloads hand-edited.

## Implementation Slices

### 1. Inventory And Contract

Document every current Docs Viewer config surface, what reads it, what writes it, and whether it is source or generated.

Acceptance:

- there is one docs page that explains the config lifecycle
- each current config file has an owner and edit model
- `viewer_options` has a documented purpose or replacement plan

### 2. Move Display Settings Out Of Generated Index Options

Decide whether `show_updated_date` belongs in the browser config projection or a user settings projection.
Move it out of `index.json.viewer_options` if it is treated as scope UI config rather than tree-data behavior.

Acceptance:

- generated docs index options only contain data-tree behavior
- browser runtime still renders updated dates according to the effective scope setting
- rebuild output is deterministic

### 3. Add Management Settings Modal

Add a management toolbar Settings button and modal for the first user-editable settings.

Acceptance:

- settings are shown for the active configured scope
- saving writes only allowlisted source-side settings
- public routes do not expose the settings button or write code path
- the modal has empty/error/unavailable states

### 4. Wire Settings Rebuilds

Make settings saves update the generated browser config or docs data payloads required by the changed setting.

Acceptance:

- saved settings survive a page reload
- generated browser config and docs payloads stay in sync
- no manual generated-file edits are required

### 5. Update Portable Setup

Update [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) with the final config model.

Acceptance:

- install-time config and user-editable settings are described separately
- downstream copy/setup steps identify which files are source and which files are generated
- the management settings UI is included in the portable boundary

## Risks

- A settings UI can make generated config feel editable unless the source/generated distinction is strict.
- Moving options between config layers can cause unnecessary rebuild churn if not staged carefully.
- Exposing too many settings early could create a weak settings schema before the portable package boundary is stable.

## Related Docs

- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)

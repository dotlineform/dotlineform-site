---
doc_id: site-request-docs-viewer-config-settings
title: Docs Viewer Config And Settings Request
added_date: 2026-05-11
last_updated: "2026-05-14 14:45"
ui_status: done
parent_id: archive
sort_order: 37000
hidden: false
---
# Docs Viewer Config And Settings Request

Status:

- Implemented

One caveat: the first settings UI is intentionally narrow. It only exposes scoped show_updated_date; recently_added_limit is still deferred because it is global, not active-scope scoped. So the original change request is complete for the agreed first editable setting, not for every candidate setting listed as future work.

## Summary

Maintain the current Docs Viewer configuration model, add a management UI for guarded source-config edits, and keep a management-only read report for inspecting effective source config.

The current Docs Viewer config model is:

- `scripts/docs/docs_scopes.json` is the source-side install/build registry
- `assets/docs-viewer/data/docs-viewer-config.json` is the browser-facing generated scope registry
- `assets/data/docs/scopes/<scope>/index.json.viewer_options` carries per-corpus viewer behavior inside generated docs output

That split is the intended model.
The remaining work is not to add another layer, but to expose selected source config fields through manage-mode controls with validation and clear warnings.

The read-only source config report now makes all configured scope settings visible from `/docs/` manage mode, with a scope dropdown for filtering, without turning config inspection into a write surface.

## Problem

The same broad idea, Docs Viewer configuration, is spread across several files with different owners and lifecycles.
The current config docs and source config report now answer the stable model questions:

- which settings are part of installing a Docs Viewer corpus
- which settings are generated and should not be edited directly
- which settings belong to the public read-only viewer versus local management mode
- which settings should be copied into another Jekyll project
- what the current source config says for every configured Docs Viewer scope

The remaining problem is narrower: decide which existing source config fields are safe enough to edit through a manage-mode settings modal, and define the guardrails for those writes.

The immediate example is `show_updated_date`.
It is defined in `scripts/docs/docs_scopes.json`, projected into generated `index.json.viewer_options`, and consumed by the browser runtime.
The settings modal should edit that source config directly, with guardrails, rather than moving the setting to another config layer.

The previous inspection problem has been addressed by the manage-mode source config report.
Source config no longer needs to be audited only by opening JSON files directly.

## Goals

- document the purpose and ownership of each Docs Viewer config file
- classify settings as install-time, generated-data, user-editable, or runtime-only
- keep the current source/generated config split
- define which source config fields can be edited safely from manage mode
- add a management-mode settings button and modal for safe user-editable settings
- keep the `/docs/` manage-mode source config report available for inspection
- keep public read-only routes free of local write behavior
- avoid reintroducing hardcoded scope lists or route maps in the viewer runtime

## Non-Goals

- replacing the whole portable Docs Viewer config system in one slice
- moving Docs Search ownership at the same time
- moving existing options into new config files or layers just to support the UI
- making public read-only routes write settings
- exposing the config report on public read-only routes
- letting the config report mutate source config
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

## Aspect 1. Editable Settings UX

Add a Settings button to the Docs Viewer management toolbar.

The button opens a modal scoped to the active Docs Viewer scope.
The first version should be deliberately small and only expose low-risk display settings.
It should make the distinction between local management settings and public viewer output clear through behavior, not explanatory in-app text.

Initial scoped controls should begin with:

- show updated dates

`recently_added_limit` remains a candidate, but it is global under `docs_viewer` rather than scoped to the active Docs Viewer scope, so it should wait until the settings UI explicitly supports global fields.

The modal should:

- load current effective settings for the active scope
- save allowlisted changes back to the source config through the local docs-management server
- trigger or request the minimal rebuild needed for generated browser/config payloads
- leave public read-only routes with no write surface
- show a clear unavailable state if the management server is not running
- provide warnings or guardrails for risky source config edits

## Aspect 2. Source Config Report

Status:

- implemented

Add a `/docs/` scope, manage-mode, read-only Docs Viewer report that displays source config in readable form.

The report should:

- be available only from `/docs/?scope=studio&mode=manage`
- read source config through the local docs-management server
- show config for all configured Docs Viewer scopes
- include a scope dropdown so the view can show all scopes or one selected scope
- present source config in grouped, readable sections rather than raw JSON alone
- identify source-owned values, generated projections, and runtime-only values where useful
- include file/source references such as `scripts/docs/docs_scopes.json` where that helps audit ownership
- avoid any save, edit, delete, or rebuild controls

Candidate sections:

- scope identity and title
- source roots and nested-source policy
- generated docs and search output paths
- route base and default doc settings
- browser config projection
- viewer options generated into scope indexes
- manage-only or non-loadable tree behavior
- source config warnings, such as missing defaults or unsupported paths

This report complements the editable settings modal.
The report is for inspection and audit.
The modal is for allowlisted user-editable settings.

## Source Config Edit Direction

Use the existing source config as the editable record rather than editing generated files or creating a new settings layer just to support the UI.
Manage mode is expected to be equivalent to directly editing the source JSON, but with validation, warnings, and narrower controls for common edits.

The design should preserve these rules:

- generated files are outputs, not the source of truth
- browser config is generated from source config
- user-editable settings have an explicit allowlist
- settings writes stay under the Docs Viewer local server allowlist
- generated payloads are never hand-edited
- server-side validation should prevent malformed JSON, invalid paths, duplicate scope ids, and unsupported option values
- warning states should make high-impact source config changes explicit before save
- the UI should not hide that it is editing source config in manage mode

## Implementation Slices

### 1. Inventory And Contract

Status:

- implemented

Document every current Docs Viewer config surface, what reads it, what writes it, and whether it is source or generated.

Acceptance:

- there is one docs page that explains the config lifecycle
- each current config file has an owner and edit model
- `viewer_options` is documented as generated per-corpus viewer behavior

### 2. Add Source Config Read Model

Status:

- implemented for the read-only source config report

Define a read-only server response that exposes source config for all Docs Viewer scopes in a browser-safe form.

Acceptance:

- reads are available only through local manage-mode capability
- every configured scope is represented
- response data is structured enough for readable grouped display
- server does not expose arbitrary local files or raw filesystem traversal
- the response distinguishes source config from generated projections where practical

### 3. Add Manage-Only Source Config Report

Status:

- implemented

Add a Docs Viewer report-backed document or equivalent manage-only report surface for source config.

Acceptance:

- report is available from `/docs/?scope=studio&mode=manage`
- report shows all scopes by default
- scope dropdown filters to one scope
- public read-only routes do not expose the report
- report has no write controls
- unavailable/error states are clear when the management server is not running

### 4. Define Source Config Edit Allowlist And Guardrails

Status:

- implemented

Define the source config fields that the management settings modal can edit and the validation/warning rules for each field.

The first implemented contract is deliberately narrow:

- scoped `show_updated_date` is allowlisted
- route, source-root, output-root, validation-policy, tree-behavior, and import-media-storage fields are blocked from the settings modal
- global `docs_viewer.recently_added_limit` is deferred until the settings UI has a global-settings section
- generated `viewer_options.show_updated_date` mismatches produce a rebuild warning
- candidate setting changes validate type, scope existence, rebuild need, and affected generated artifacts

The read-only contract is served by `GET /docs/source-config-settings`.
It does not write source config and does not introduce another config layer.

Acceptance:

- the first editable fields remain in the existing source config
- no new config file or layer is introduced just to support the settings UI
- each editable field has validation rules
- risky source config changes require a clear warning before save
- browser runtime still renders according to the generated projection of the source config

### 5. Add Management Settings Modal

Status:

- implemented

Add a management toolbar Settings item to the Actions button and modal for the first user-editable settings.

Acceptance:

- settings are shown for the active configured scope
- saving writes only allowlisted source config fields
- public routes do not expose the settings button or write code path
- the modal has empty/error/unavailable states

### 6. Wire Settings Rebuilds

Status:

- implemented

Make settings saves update the generated browser config or docs data payloads required by the changed setting.

Acceptance:

- saved settings survive a page reload
- generated browser config and docs payloads stay in sync
- no manual generated-file edits are required

### 7. Update Portable Setup

Status:

- implemented

Update [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup) with the final config model.

Acceptance:

- install-time config and manage-mode editable source config fields are described clearly
- downstream copy/setup steps identify which files are source and which files are generated
- the management settings UI is included in the portable boundary
- the read-only source config report is described as a local management inspection tool

## Risks

- A settings UI can make source config edits feel lower-risk than editing JSON directly unless warnings and validation are clear.
- Direct source config editing can break routes, generated outputs, or scope availability if guardrails are too weak.
- Exposing too many settings early could create a weak settings schema before the portable package boundary is stable.
- Future report additions could leak implementation detail into public UI if they are not kept behind local manage mode.

## Related Docs

- [Portable Docs Viewer Request](/docs/?scope=studio&doc=site-request-portable-docs-viewer)
- [Docs Viewer Portable Setup](/docs/?scope=studio&doc=docs-viewer-portable-setup)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)

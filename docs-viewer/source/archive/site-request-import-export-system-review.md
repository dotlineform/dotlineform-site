---
doc_id: site-request-import-export-system-review
title: Import/Export System Review Request
added_date: 2026-05-09
last_updated: "2026-05-13 11:48"
ui_status: done
parent_id: data-sharing
sort_order: 1000
viewable: true
---
# Import/Export System Review Request

Status:

- closed

## Closeout

This review is closed as an architecture decision and handoff.

The Docs management service cleanup is now complete through Slice 8, and Docs Viewer management has also completed the follow-on scoped management and local/import packaging work recorded in [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management).
Implementation ownership has moved to [Studio Data Sharing Module Implementation Request](/docs/?scope=studio&doc=site-request-studio-import-export-module), which defines the separate portable Data Sharing module, the optional Docs Viewer documents adapter, and the tags adapter path.

## Summary

Review the shared Studio import/export system as its own architecture and extensibility problem.

This follows the completed [Export Import Adapter Boundary Request](/docs/?scope=studio&doc=site-request-export-import-adapters), which established the first adapter boundary, and the [Docs Management Service Slices](/docs/?scope=studio&doc=site-request-script-structural-review-docs-management-server), which intentionally left structured import/export adapter orchestration out of the final Docs management service cleanup.

The goal is to make the import/export system easier to extend across Library, Catalogue, Analysis, and future data domains without letting one workflow's assumptions leak into the shared shell.

## Problem

The current system has useful first-generation boundaries, but it is still early in its life:

- Library document export/import is the only real implemented adapter path.
- `/studio/export/` and `/studio/import/` share UI and service transport, but their adapter extension contracts are still evolving.
- `export_import_adapters.py`, `docs-viewer/services/docs_export.py`, and `docs-viewer/services/docs_import.py` are likely to grow as new data domains are added.
- The Docs management service still orchestrates structured import/export calls, but that is a local-service integration concern rather than the right place to decide adapter architecture.
- Future Catalogue and Analysis workflows will need validation, preview, apply, and backup models that are not document-shaped.

Without a separate review, new requirements could drift into whichever layer is easiest to edit first: the Studio page shell, Docs management service handlers, Library-specific code, or adapter config.

## Review Goals

- Define the durable ownership boundary between shared Studio shell, local service orchestration, adapter registry/config, and domain adapters.
- Decide how adapters declare export, staged-file, preview, apply, validation, backup, and activity capabilities.
- Keep Library document behavior stable while making its assumptions explicit.
- Identify which import/export behavior belongs in `export_import_adapters.py`, `docs-viewer/services/docs_export.py`, `docs-viewer/services/docs_import.py`, or future domain-specific modules.
- Decide whether the shared UI needs adapter-provided presentation contracts for preview rows, selectable records, warnings, counts, and apply confirmations.
- Keep local write safety visible: explicit staging roots, preview roots, source-write targets, backups, dry-run behavior, and confirmation gates.
- Produce a practical slice plan before implementation.

## Non-Goals

- Do not fold this work into Docs management service Slice 8.
- Do not implement Catalogue or Analysis import/apply workflows before their adapter contracts are understood.
- Do not redesign `/studio/export/` or `/studio/import/` for visual polish unless architecture changes require small UI contract updates.
- Do not create a broad plugin framework before there are enough real adapters to justify it.
- Do not change existing Library response payloads or generated preview behavior without a focused compatibility decision.

## Initial Review Questions

- Which concepts are truly shared lifecycle concerns, and which are Library document adapter behavior?
- Should export and import adapters share one registry contract, or should export, preview, and apply capabilities be separate declarations?
- How should adapter configs declare paths without exposing internal adapter terminology to the user?
- What is the minimum preview/apply result contract the Studio shell needs to render domain-specific workflows?
- How should adapters declare write safety: backup targets, allowlisted write roots, dry-run behavior, and confirmation requirements?
- Which future adapter is the best second implementation to test the contract: Catalogue data, Analysis tag registry, or another Library workflow?
- What direct tests should pin the adapter registry and service contract before any broader refactor?

## Candidate Modules And Routes

- `assets/studio/js/data-export.js`
- `assets/studio/js/data-import.js`
- `assets/studio/data/export_import_adapters.json`
- `docs-viewer/services/export_import_adapters.py`
- `docs-viewer/services/docs_export.py`
- `docs-viewer/services/docs_import.py`
- `docs-viewer/services/docs_management_server.py`
- `/studio/export/`
- `/studio/import/`

## Relationship To Docs-Management Cleanup

Docs-management server Slice 8 should close the local-service restructuring without taking over this broader request.

For Slice 8, structured import/export orchestration should be marked `leave` or `defer`, with this request as the follow-up owner.
The Docs management service can keep local HTTP integration, response status mapping, activity timing, and rebuild/write follow-through where needed, while the adapter review decides the import/export system's extensibility model.

## Draft Deliverables

1. Inventory current Library document assumptions across the shared shell, config, server handlers, and adapter modules.
2. Draw the proposed ownership boundary for shared shell, adapter registry, adapter modules, and local service integration.
3. Define the minimum adapter capability contract for export, staged-file listing, preview, and apply.
4. Choose the second adapter or workflow that should validate the contract.
5. Produce implementation slices with targeted tests and compatibility notes.

## Acceptance Criteria

- Clear recommendation for whether the current adapter registry shape is sufficient or needs another split.
- Explicit owner for each major behavior: config discovery, staged-file discovery, preview shaping, apply validation, backup planning, source writes, result display, and activity logging.
- Written guidance on what should remain in Docs management service versus adapter-owned modules.
- A slice plan that preserves current Library behavior while making future data-domain adapters easier to add.
- Tests identified for registry resolution, service contracts, and at least one domain adapter workflow.

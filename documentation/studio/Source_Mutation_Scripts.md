---
draft: false
doc_id: d-20260607-222033-c0b57a
title: Source Mutation Scripts
added_date: "2026-06-07 22:20:33"
last_updated: "2026-10-15"
parent_id: d-20260607-222033-2a494e
---
# Docs Viewer Source Mutation Scripts

Common Title/Summary editing belongs to the combined Source session and `/docs/source/save`, described in [Source Editor Scripts](Source_Editor_Scripts.md). Subject changes belong to the unsaved Source buffer. [Source Mutation Endpoints](Source_Mutation_Endpoints.md) describes the exact Draft, Selected, Position and Delete request/response boundaries; [Management Operations](Management_Operations.md) owns their completion/failure behavior. Scope lifecycle, generic metadata/field planners and preview/apply Delete routes remain retired without aliases.

## `docs-viewer/services/docs_management_mutations.py`

Constructs create-only source, exact identity, committed metadata and updated ordinary tree for New. The plan carries prepared source/report/configuration and known IDs into completion. It does not plan Position, Draft, Subject or Delete.

## `docs-viewer/services/docs_management_mutation_service.py`

Writes the create-only plan and invokes the existing in-process prepared document/Links generation, logs completion and returns diagnostics. A generation failure after source creation carries the committed New target/record so Source can open it while preserving the error. It does not restore or retry Create.

## `docs-viewer/services/docs_management_draft.py`

Resolves the exact owner/source, retains parsed field spans, rewrites only Draft and passes prepared input into generation. It preserves unrelated source text/dates, returns the committed record and distinguishes persisted source from generation failure. No revision check or metadata prefetch participates.

## `docs-viewer/services/docs_selected_documents.py`

Owns Working Selected parsing, row projection and persistence. Star reads required source metadata; Unstar removes exact membership without a source read. Builders carry supplied Selected state when available and refresh only known selected metadata. Publish owns public eligibility filtering.

## `docs-viewer/services/docs_management_position.py`

Reads canonical Index, moves the complete node through `docs_index_order.py` and completes metadata-only generation through `project_document_position`. It reports committed position/record and generation progress without changing source/body/dates or Links. Host root placement belongs to the Position UI.

## `docs-viewer/services/docs_management_delete.py`

Accepts one confirmed ordinary-root selection or singular configured collection target. It resolves ownership once, reads tree/Selected once, removes exact confined source paths and updates Index/Selected without mutating the design-time default or projecting browser configuration. It passes known deleted IDs, remaining parent map, configuration and Selected into `complete_document_deletion`, retaining completed effects and target/phase on failure. It has no preview, revision, restoration, recovery build or public-cleanup machinery.

## `docs-viewer/services/docs_write_rebuild.py`

Hosts the existing exact/complete build orchestration and prepared in-process handoff. `project_document_position` reuses saved generated navigation/by-ID metadata without Markdown rendering. `complete_document_deletion` passes empty surviving sources and known deleted IDs into the existing ordinary/collection builders for exact generated/Links removals. Saved navigation is parsed without corpus field audits or unselected by-ID preflights. Import's separately owned rollback behavior remains independent.

## Browser Owners

`docs-viewer-management-draft-workflow.js` submits the intended boolean once and projects its committed record. `docs-viewer-position-modal.js` derives ordinary/host-root destinations from loaded data; `docs-viewer-management-actions.js` projects completed Position and awaits one Index refresh.

Ordinary Delete in `docs-viewer-management-actions.js` and flat Delete in `docs-viewer-management-collection-delete-workflow.js` confirm locally and call one `/docs/delete` request. They forward completed effects to retained views and keep global busy state through service/display completion. Shared route/navigation owners await surviving-caller or fallback display and release deleted retained callers. Listener/display failures remain visible separately from incomplete service work.

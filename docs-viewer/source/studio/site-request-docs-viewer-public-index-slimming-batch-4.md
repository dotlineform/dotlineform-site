---
doc_id: site-request-docs-viewer-public-index-slimming-batch-4
title: Docs Viewer Public Index Slimming Batch 4
added_date: 2026-06-05
last_updated: 2026-06-05
ui_status: done
parent_id: site-request-docs-viewer-public-index-slimming-tasks
viewable: true
---
# Batch 4: Info Panel Hydration and Rendering

This is the delivery specification for [Batch 4 in Docs Viewer Public Index Slimming Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-tasks).

### Batch 4: Info Panel Hydration and Rendering

Summary: Shape selected by-id metadata as needed, hydrate info-panel state from selected by-id payloads, and split public reader metadata rendering from manage metadata surfaces.

| ID | status | action |
| --- | --- | --- |
| 4.1 | done | Update public and manage by-id payload shaping only as needed for selected-document info-panel hydration, keeping public read-only metadata limited to title, summary, and last updated and avoiding management-only metadata in public by-id payloads. |
| 4.2 | done | Refactor the info-panel context so selected-document metadata hydrates from by-id payloads for both public read-only and local/manage routes. |
| 4.3 | done | Split public read-only info-panel rendering from manage-mode metadata rendering, with public read-only limited to title, summary, and last updated. |

## Steer for these tasks

- Info-panel metadata should come from the selected by-id payload, not tree rows and not `index.json`.
- Public read-only info panels should show only title, summary, and last updated.
- Manage mode can keep its richer metadata surface but should not force public tree or by-id payloads to carry management metadata.
- Preserve current selected-document and routing behavior while moving metadata ownership.

## Deliverables

- By-id payload shaping adjustments needed for selected-document info-panel hydration.
- Info-panel context hydration from selected by-id payloads for public and manage routes.
- Public read-only info-panel rendering limited to reader-facing fields.
- Manage metadata rendering preserved without widening public payloads.

## Implementation and policy guidance

- Do not mirror manage metadata surfaces into public read-only routes.
- Do not expose source path, visibility state, UI status internals, management-only fields, or editable metadata concepts in public info-panel rendering.
- Avoid adding metadata to `index-tree.json` just to satisfy info-panel rendering.

## Proposed verification set

- Focused generated-output checks for public by-id reader metadata.
- JavaScript syntax/import checks for changed info-panel modules.
- Public and manage browser checks that open the info panel and confirm selected by-id metadata is used.
- Negative assertions that public info panel omits management-only metadata.

## completed verification

- 2026-06-05: Python syntax checks passed for `docs-viewer/build/build_docs.py`, `docs-viewer/tests/python/test_build_docs_python.py`, and `docs-viewer/tests/smoke/docs_viewer_metadata_info_view_modules.py`.
- 2026-06-05: Focused generated-output pytest passed: `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_build_docs_python.py -q`.
- 2026-06-05: JavaScript syntax checks passed for `docs-viewer/runtime/js/docs-viewer-view-context.js` and `docs-viewer/runtime/js/docs-viewer-metadata-info-view.js`.
- 2026-06-05: Focused metadata info module smoke passed: `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_metadata_info_view_modules.py --site-root .`.
- 2026-06-05: Reduced Docs Viewer smoke profile passed: `$HOME/miniconda3/bin/python3 studio/commands/run_checks.py --profile docs-viewer-smoke`; summary at `var/test-runs/20260605-190324/summary.md`.

## follow-on tasks

- Batch 3 handoff: route tree loading now reads `index_tree_url` through `readDocsIndexTree`; recently-added mode reads `recently_added_url` through `readRecentlyAdded`.
- Batch 3 handoff: normalized tree docs are deliberately slim and should not be widened for info-panel needs; use selected by-id payload hydration for title, summary, last updated, and any manage-only metadata.
- Batch 3 handoff: browser scope config still carries full `index_url` as `docsIndexUrl` for report/internal rich-index reads; do not reintroduce that path into public route boot or recently-added mode.
- Batch 3 handoff: management metadata modal and info-panel code may still assume metadata is present on selected tree/index records; Batch 4 should move those reads to selected by-id payload state.
- Batch 3a handoff: `docs_viewer_app_shell_modules.py` was deleted; Batch 4 verification should use focused Python/syntax checks plus the reduced `docs-viewer-smoke` profile when browser coverage is warranted.
- Batch 3a handoff: do not add broad browser module-contract smokes for info-panel hydration; prefer focused tests for data shaping and one public/manage route check for rendered behavior.

## task close

- Batch 5 handoff added.
- This document and the tracker row were set to `done`.

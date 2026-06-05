---
doc_id: site-request-docs-viewer-public-index-slimming-batch-5
title: Docs Viewer Public Index Slimming Batch 5
added_date: 2026-06-05
last_updated: 2026-06-05
ui_status: planned
parent_id: site-request-docs-viewer-public-index-slimming-tasks
viewable: true
---
# Batch 5: Public Flat Index Retirement

This is the delivery specification for [Batch 5 in Docs Viewer Public Index Slimming Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-tasks).

### Batch 5: Public Flat Index Retirement

Summary: Remove remaining Docs Viewer public runtime dependencies on rich flat-index data, then retire public flat `index.json` from generated public route outputs.

| ID | status | action |
| --- | --- | --- |
| 5.1 | planned | Remove public info-panel metadata reads and tree construction reads from public flat `index.json`, then retire public flat `index.json` from Docs Viewer-generated public route outputs after Docs Viewer-owned tree, selected-document, search, and recently-added dependencies have moved. |
| 5.2 | planned | Review and remove public runtime exposure of rich flat-index fields such as `last_updated`, `source_path`, `viewer_url`, `content_text_length`, and other management/tooling metadata after dependent Docs Viewer call sites have moved. |

## Steer for these tasks

- Do this only after builder outputs, runtime loading, search inputs, recently-added, and info-panel dependencies have moved.
- Removal is the risky step; use request/fixture assertions to prove old public `index.json` is no longer part of the Docs Viewer route contract.
- Keep Data Sharing or other tooling needs classified under their owning request instead of preserving rich public flat indexes for them.

## Deliverables

- No public tree construction reads from public flat `index.json`.
- No public info-panel metadata reads from public flat `index.json`.
- Public Docs Viewer-generated route outputs no longer publish flat public `assets/data/docs/scopes/<scope>/index.json` for runtime use.
- Public runtime exposure of rich flat-index fields removed after dependent call sites have moved.

## Implementation and policy guidance

- Do not keep rich public flat indexes only to support old tree-construction paths or tooling consumers.
- Do not add public runtime fallbacks to old `index.json`.
- Treat any remaining rich-metadata consumer as a bug, a selected by-id hydration case, a search/build input case, a manage-only case, or a separate tooling ownership case.

## Proposed verification set

- Stale-reference scans for public `index.json` route loading and rich public flat-index fields.
- Generated-output contract tests that public route outputs no longer require rich flat-index fields.
- Public browser request assertions proving `index.json` is not requested.
- Focused syntax/import checks for changed builders and runtime modules.

## completed verification

- Not started.

## follow-on tasks

- Batch 4 handoff: public route boot and metadata info rendering no longer depend on public flat `index.json`; info-panel metadata now comes from the selected by-id payload context.
- Batch 4 handoff: public by-id payload generation now emits reader metadata only (`title`, optional `summary`, `last_updated`, plus rendered `content_html`) and omits management-only fields such as `doc_id`, `source_path`, `viewer_url`, `ui_status`, `viewable`, `parent_id`, `added_date`, and report metadata.
- Batch 4 handoff: remaining rich flat-index reads found during implementation are non-info-panel paths: browser config still carries `index_url`/`docsIndexUrl`; manage document reports use `docsIndexUrl` through `readScopeIndex`; local generated payload reads validate selected payloads against the rich flat index; Data Sharing export/import and docs broken-link tooling still read rich flat indexes under their owning requests.
- Batch 4 handoff: Batch 5 should keep public route request assertions focused on ensuring `/library/` and `/analysis/` do not request `assets/data/docs/scopes/<scope>/index.json` for route boot, tree construction, recently-added, selected-document loading, or info-panel rendering.

## task close

- Add a handoff note to Batch 6 with exact negative assertions that final verification must cover.
- Set this document and the tracker row status to `done` when the batch is complete.

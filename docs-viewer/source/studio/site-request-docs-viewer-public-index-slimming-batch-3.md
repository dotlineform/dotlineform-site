---
doc_id: site-request-docs-viewer-public-index-slimming-batch-3
title: Docs Viewer Public Index Slimming Batch 3
added_date: 2026-06-05
last_updated: 2026-06-05
ui_status: done
parent_id: site-request-docs-viewer-public-index-slimming-tasks
viewable: true
---
# Batch 3: Runtime Loading and Boundary Check

This is the delivery specification for [Batch 3 in Docs Viewer Public Index Slimming Tasks](/docs/?scope=studio&doc=site-request-docs-viewer-public-index-slimming-tasks).

### Batch 3: Runtime Loading and Boundary Check

Summary: Add tree payload adapters, switch public and manage route loading to `index-tree.json` and the small recently-added payload, and coordinate with the entrypoint split request if shared-core ownership issues appear.

| ID | status | action |
| --- | --- | --- |
| 3.1 | done | Add public and manage tree payload adapters that preserve the shared-core boundary owned by [Docs Viewer Public/Manage Entrypoint Split Request](/docs/?scope=studio&doc=site-request-docs-viewer-public-manage-entrypoints); do not move manage-only controls, services, drag/drop, context menus, mutation calls, source/edit workflows, or local-service reads into public payloads or shared payload adapters. |
| 3.2 | done | Coordinate with the entrypoint split request if tree payload switching exposes shared-core public/manage mode switches or manage-only rendering in shared modules; this request owns the payload/data contract, while the entrypoint split request owns the shared-core cleanup work. |
| 3.3 | done | Switch public and manage route config/data loading so frontend index-panel rendering reads route-appropriate `index-tree.json` payloads and recently-added reads its small generated payload; missing required payloads should surface as visible data-load failures with no fallback to `index.json`. |

## Steer for these tasks

- The adapter should bridge the new tree payload to the existing renderer contract without making public code aware of manage-only capabilities.
- Missing `index-tree.json` is a visible load failure, not a reason to fallback to `index.json`.
- Recently-added should load from its own route-appropriate payload.
- Coordinate explicitly if this exposes shared-core public/manage mode switches that belong to the entrypoint split request.

## Deliverables

- Public tree payload adapter.
- Manage tree payload adapter using the same tree record structure.
- Route config/data loading switched to route-appropriate `index-tree.json`.
- Recently-added runtime loading switched to the small generated payload.
- Visible missing-payload behavior with no `index.json` fallback.
- Boundary notes for any entrypoint split coordination needed.

## Implementation and policy guidance

- Do not move management controls, services, drag/drop, context menus, mutation calls, source/edit workflows, or local-service reads into public payloads or shared public adapters.
- Keep shared-core and shared-renderer cleanup within the entrypoint split request unless the payload switch requires an explicitly coordinated change.
- Avoid compatibility shims for old `index.json` runtime loading.

## Proposed verification set

- JavaScript syntax/import checks for changed runtime modules.
- Focused browser or module smoke for public and manage tree loading.
- Request/asset assertions proving route-appropriate `index-tree.json` and recently-added payloads load.
- Negative request assertions proving public routes do not request public `index.json`.

## completed verification

- `$HOME/miniconda3/bin/python3 -m py_compile docs-viewer/build/build_docs.py docs-viewer/build/build_search.py docs-viewer/services/docs_generated_reads.py docs-viewer/services/docs_management_routes.py docs-viewer/services/docs_management_read_service.py docs-viewer/services/docs_viewer_service.py docs-viewer/tests/python/test_build_docs_python.py docs-viewer/tests/python/test_docs_generated_reads.py docs-viewer/tests/python/test_docs_management_service.py docs-viewer/tests/smoke/docs_viewer_service_manage.py docs-viewer/tests/smoke/docs_viewer_management_workflows.py docs-viewer/tests/smoke/docs_viewer_management_scope_ui.py`
- `$HOME/miniconda3/bin/python3 -m pytest docs-viewer/tests/python/test_build_docs_python.py docs-viewer/tests/python/test_docs_generated_reads.py docs-viewer/tests/python/test_docs_management_service.py`
- Batch 3 originally used the now-retired app-shell mega-smoke; Batch 3a replaced that with the reduced Docs Viewer smoke profile.
- `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- `$HOME/miniconda3/bin/python3 docs-viewer/tests/smoke/docs_viewer_management_workflows.py`
- `$HOME/miniconda3/bin/python3 docs-viewer/build/build_docs.py --scope studio --diagnostics`

## follow-on tasks

- Batch 2 handoff: `docs-viewer/build/build_docs.py` now writes `index-tree.json` and `recently-added.json` beside each scope's generated docs root.
- Public route paths are `assets/data/docs/scopes/<scope>/index-tree.json` and `assets/data/docs/scopes/<scope>/recently-added.json`; manage/local route paths are `docs-viewer/generated/docs/<scope>/index-tree.json` and `docs-viewer/generated/docs/<scope>/recently-added.json`.
- `index-tree.json` uses schema `docs_index_tree_v1` with top-level `schema`, `generated_at`, `viewer_options`, and `docs`; row fields are limited to `doc_id`, `title`, `content_url`, optional non-empty `parent_id`, optional `viewable: false`, and optional non-empty `ui_status`.
- `recently-added.json` uses schema `docs_recently_added_v1` with top-level `schema`, `generated_at`, `limit`, and `docs`; row fields are limited to `doc_id`, `title`, `content_url`, `added_date`, optional `parent_id`, and optional `parent_title`.
- Public compact payloads filter out non-viewable docs, descendants of non-viewable docs, and descendants of `manage_only_tree_root_ids`; manage compact tree payloads preserve non-viewable rows with `viewable: false`.
- The search builder now derives docs search entries from configured source roots and no longer accepts `--source-index`; runtime search remains on the separate `search_index_url`.
- Batch 3 added `docs-viewer-tree-payload-adapter.js`; tree rows intentionally normalize only `doc_id`, `title`, `content_url`, optional `parent_id`, optional `viewable: false`, and optional `ui_status`.
- Public and manage route loading now uses `index_tree_url`; recently-added mode uses `recently_added_url`; public route-loading smokes assert no request to public docs `index.json`.
- Full `index_url` remains in browser scope config as `docsIndexUrl` for report/internal rich-index reads, not for public route boot or recently-added mode.
- Missing `index-tree.json` or `recently-added.json` is surfaced as a visible load failure; no runtime fallback to `index.json` was added.

## task close

- Batch 4 handoff added.
- Tracker row can be marked `done`.

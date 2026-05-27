---
doc_id: docs-viewer-javascript-inventory
title: Docs Viewer JavaScript Inventory
added_date: 2026-05-20
last_updated: 2026-05-27
ui_status: review
parent_id: studio-javascript-payload-inventory
sort_order: 7020
viewable: true
---
# Docs Viewer JavaScript Inventory

This document is the Docs Viewer-specific review slice of [JavaScript Inventory Policy](/docs/?scope=studio&doc=studio-javascript-payload-inventory).
It uses the same four-risk scoring model as the parent inventory, but limits the table and follow-up notes to browser JavaScript under `docs-viewer/runtime/js/`.

## Current Summary

Measured on 2026-05-21 from [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory).

- Docs Viewer browser JavaScript files in the full inventory: 35
- Files above target score 4: 14
- General risk themes: shared runtime composition, management coordinator growth, import workflow ownership, scope lifecycle, search/bookmark controller boundaries, and lazy management loading.

| Score | Files |
| ---: | ---: |
| 9 | 0 |
| 8 | 1 |
| 7 | 0 |
| 6 | 6 |
| 5 | 7 |
| 4 | 21 |

## Current Priorities

| Docs rank | Full rank | File | Maint. | Struct. | Perf. | Arch. | Risk | Focus |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | `docs-viewer/runtime/js/docs-viewer.js` | 2 | 2 | 3 | 1 | 8 | Shared Docs Viewer runtime after index-panel state owner extraction; route loading and payload composition remain. |
| 2 | 9 | `docs-viewer/runtime/js/docs-viewer-management-modals.js` | 2 | 2 | 1 | 1 | 6 | Docs Viewer management modal controller after transient modal shell and metadata parent-picker extraction. |
| 3 | 15 | `docs-viewer/runtime/js/docs-viewer-management.js` | 2 | 2 | 1 | 1 | 6 | Docs Viewer management coordinator after shared action workflow helper extraction. |
| 4 | 18 | `docs-viewer/runtime/js/docs-viewer-bookmarks.js` | 2 | 2 | 1 | 1 | 6 | Docs Viewer bookmark/favourite support. |
| 5 | 19 | `docs-viewer/runtime/js/docs-viewer-management-actions.js` | 2 | 2 | 1 | 1 | 6 | Docs Viewer management support module. |
| 6 | 20 | `docs-viewer/runtime/js/docs-viewer-scope-lifecycle.js` | 2 | 2 | 1 | 1 | 6 | Docs Viewer runtime support module. |
| 7 | 33 | `docs-viewer/runtime/js/docs-html-import.js` | 2 | 1 | 1 | 2 | 6 | Docs import controller after explicit workflow handoff and focused module-smoke coverage. |
| 8 | 34 | `docs-viewer/runtime/js/docs-html-import-workflow.js` | 2 | 1 | 1 | 1 | 5 | Docs import preview/write workflow helper. |
| 9 | 35 | `docs-viewer/runtime/js/docs-viewer-config-controller.js` | 2 | 1 | 1 | 1 | 5 | Docs Viewer config/scope setup. |
| 10 | 36 | `docs-viewer/runtime/js/docs-viewer-search-controller.js` | 2 | 1 | 1 | 1 | 5 | Docs Viewer search helper or controller. |
| 11 | 54 | `docs-viewer/runtime/js/docs-viewer-document-controller.js` | 1 | 2 | 1 | 1 | 5 | Docs Viewer document rendering/controller support. |
| 12 | 55 | `docs-viewer/runtime/js/docs-viewer-reports.js` | 1 | 2 | 1 | 1 | 5 | Docs Viewer runtime support module. |
| 13 | 25 | `docs-viewer/runtime/js/reports/docs-broken-links-report.js` | 2 | 1 | 1 | 1 | 5 | Docs Broken Links report module after the old Studio route controller was retired. |
| 14 | 56 | `docs-viewer/runtime/js/docs-viewer-router.js` | 1 | 2 | 1 | 1 | 5 | Docs Viewer routing and history helper. |
| 15 | 59 | `docs-viewer/runtime/js/docs-html-import-modals.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 16 | 60 | `docs-viewer/runtime/js/docs-html-import-render.js` | 1 | 1 | 1 | 1 | 4 | Docs import result rendering helper. |
| 17 | 61 | `docs-viewer/runtime/js/docs-viewer-data.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 18 | 62 | `docs-viewer/runtime/js/docs-viewer-drag-drop.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 19 | 63 | `docs-viewer/runtime/js/docs-viewer-favourites.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer bookmark/favourite support. |
| 20 | 64 | `docs-viewer/runtime/js/docs-viewer-management-capabilities.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 21 | 65 | `docs-viewer/runtime/js/docs-viewer-management-client.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 22 | 66 | `docs-viewer/runtime/js/docs-viewer-management-config.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 23 | 67 | `docs-viewer/runtime/js/docs-viewer-management-interactions.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 24 | 68 | `docs-viewer/runtime/js/docs-viewer-management-render.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 25 | 69 | `docs-viewer/runtime/js/docs-viewer-render.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer rendering helper. |
| 26 | 70 | `docs-viewer/runtime/js/docs-viewer-search.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer search helper or controller. |
| 27 | 71 | `docs-viewer/runtime/js/docs-viewer-sidebar.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 28 | 72 | `docs-viewer/runtime/js/docs-viewer-tree.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 29 | 73 | `docs-viewer/runtime/js/reports/change-history-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 30 | 74 | `docs-viewer/runtime/js/reports/docs-index-table-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 31 | 75 | `docs-viewer/runtime/js/reports/reports-list-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 32 | 76 | `docs-viewer/runtime/js/reports/semantic-references-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 33 | 77 | `docs-viewer/runtime/js/reports/source-config-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 34 | 152 | `docs-viewer/runtime/js/docs-viewer-management-action-workflow.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management normalize-order and viewability target workflow helper. |
| 35 | 153 | `docs-viewer/runtime/js/docs-viewer-index-panel.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer index panel state, persistence migration, toggle projection, and document-pane visibility helper. |
| 36 | 154 | `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js` | 1 | 1 | 1 | 1 | 4 | App-shell-owned index panel chrome renderer and projection applier. |

## Follow-Up Notes

### `docs-viewer/runtime/js/docs-viewer.js`

- Current risk score: 8.
- Track separately from the all-script target-score plan because it is the shared Docs Viewer entry runtime.
- 2026-05-27 owner note: management action-area shell coordination moved to `docs-viewer/runtime/js/docs-viewer-app-shell.js`; `docs-viewer.js` only initializes that owner before existing route boot and waits for it before management/theme binding.
- 2026-05-27 owner note: header-control composition moved to `docs-viewer/runtime/js/docs-viewer-header-controls-renderer.js`, coordinated by the app shell before `docs-viewer.js` reads the preserved control IDs.
- 2026-05-27 owner note: index panel chrome composition moved to `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`, coordinated by the app shell before `docs-viewer.js` reads the preserved `docsViewerSidebarToggle`, `docsViewerSidebarExpand`, and `docsViewerNav` IDs. The entry module still owns index panel state transitions and storage until a broader panel-layout owner exists.
- Useful future slices should reduce shared-runtime coupling or route-load cost, such as generated-payload loading, loadable-doc visibility state, broader panel-layout ownership, or management lazy-boundary hardening.
- Do not turn the entry file into a thin pass-through layer if that makes the viewer boot sequence harder to inspect.
- Preserve `docs-viewer/runtime/js/docs-viewer-sidebar.js` as the tree renderer inside the panel rather than making the tree index own panel state.

### `docs-viewer/runtime/js/docs-viewer-app-shell.js`

- Added 2026-05-27 as the app-shell owner for management action-area coordination.
- Current scope is intentionally narrow: render route-provided header controls through `docs-viewer/runtime/js/docs-viewer-header-controls-renderer.js`, render index panel chrome through `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`, clear the management action mount, import `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js` only when route intent allows management, and return the rendered rows before existing management/theme binding continues.
- The existing lazy management controller continues to own backend reachability, capability refresh, command wiring, and status projection.
- Revisit the inventory table and score during the next full JavaScript inventory refresh; the expected target score for this focused renderer is 4 or lower while it stays limited to shell rendering.

### `docs-viewer/runtime/js/docs-viewer-header-controls-renderer.js`

- Added 2026-05-27 as the focused renderer for scope picker, recently-added button, search input, and management-action mount composition.
- Keep this module static and side-effect-light: it should preserve existing control refs and render only into an explicit app-shell mount from route context.

### `docs-viewer/runtime/js/docs-viewer-management-actions-renderer.js`

- Added 2026-05-27 as the focused renderer for management action markup.
- Keep this module static and side-effect-light: it should preserve existing control refs and render only into an explicit app-shell mount.

### `docs-viewer/runtime/js/docs-viewer-index-panel-renderer.js`

- Added 2026-05-27 as the focused renderer for index panel shell chrome.
- Keep this module limited to rendering the sidebar container, toolbar controls, nav mount, and applying index-panel projection to DOM refs. Do not move tree row rendering, drag/drop behavior, search/recent behavior, or document payload rendering into it.

### Docs Import And Management

- Keep import result rendering in `docs-viewer/runtime/js/docs-html-import-render.js`.
- Keep preview/write orchestration in `docs-viewer/runtime/js/docs-html-import-workflow.js`.
- Keep management-only workflows behind the lazy management boundary.
- Keep normalize-order choice shaping and make-viewable target resolution in `docs-viewer/runtime/js/docs-viewer-management-action-workflow.js`.
- Move command-specific write behavior to `docs-viewer/runtime/js/docs-viewer-management-actions.js` or a workflow-specific module when it gains independent state.

### Reports, Search, And Bookmarks

- Keep reports self-contained and loaded through the report allowlist.
- Extract shared report table or pager helpers only after at least two reports need the same behavior.
- Keep search and bookmark storage/controller behavior focused; revisit if grouping, sync, export, or cross-scope behavior is added.

## Refresh Notes

1. Refresh [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) first using the parent inventory scoring model.
2. Copy the Docs Viewer subset into this document and preserve the category columns.
3. Update follow-up notes only for files whose risk category changed or where new implementation work is planned.
4. Keep `docs-viewer/runtime/js/docs-viewer.js` separate from the all-script implementation plan unless the user explicitly starts that shared-runtime track.

## Related References

- [JavaScript Inventory Policy](/docs/?scope=studio&doc=studio-javascript-payload-inventory)
- [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory)
- [JavaScript Inventory Implementation Plan](/docs/?scope=studio&doc=javascript-inventory-implementation-plan)

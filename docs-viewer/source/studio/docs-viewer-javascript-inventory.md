---
doc_id: docs-viewer-javascript-inventory
title: Docs Viewer JavaScript Inventory
added_date: 2026-05-20
last_updated: 2026-05-21
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

## Follow-Up Notes

### `docs-viewer/runtime/js/docs-viewer.js`

- Current risk score: 8.
- Track separately from the all-script target-score plan because it is the shared Docs Viewer entry runtime.
- Useful future slices should reduce shared-runtime coupling or route-load cost, such as generated-payload loading, loadable-doc visibility state, index panel surface activation, or management lazy-boundary hardening.
- Do not turn the entry file into a thin pass-through layer if that makes the viewer boot sequence harder to inspect.
- Preserve `docs-viewer/runtime/js/docs-viewer-sidebar.js` as the tree renderer inside the panel rather than making the tree index own panel state.

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

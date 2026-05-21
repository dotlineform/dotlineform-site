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
It uses the same four-risk scoring model as the parent inventory, but limits the table and follow-up notes to browser JavaScript under `assets/docs-viewer/js/`.

The shared entry runtime `assets/docs-viewer/js/docs-viewer.js` remains listed for completeness, but implementation work for that file is handled separately from the all-script risk-reduction plan.

## Upcoming Index Panel Work

A forthcoming change request is expected to introduce a generic Docs Viewer index panel with `collapsed`, `normal`, and `expanded` states.
The initial panel content will remain the existing tree index, but the expanded state is intended to create a reusable workspace for later semantic or graph-based index surfaces.
The graph index itself should be a separate project.

Treat that change request as distinct from this inventory, but use this inventory to identify prerequisite risk work before implementation.
The likely prerequisite is to establish a focused index panel/layout owner so `assets/docs-viewer/js/docs-viewer.js` does not absorb another broad interactive-surface responsibility.
Related follow-up should preserve `assets/docs-viewer/js/docs-viewer-sidebar.js` as the tree renderer inside the panel rather than making the tree index own panel state.

## Current Summary

Measured on 2026-05-21 from [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory).

- Docs Viewer browser JavaScript files in the full inventory: 32
- Files above target score 4, excluding `assets/docs-viewer/js/docs-viewer.js`: 12
- Main remaining risk themes: shared runtime composition, management coordinator growth, import workflow ownership, scope lifecycle, search/bookmark controller boundaries, and lazy management loading.

| Score | Files |
| ---: | ---: |
| 9 | 1 |
| 7 | 2 |
| 6 | 4 |
| 5 | 6 |
| 4 | 19 |

## Current Priorities

| Docs rank | Full rank | File | Maint. | Struct. | Perf. | Arch. | Risk | Focus |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | `assets/docs-viewer/js/docs-viewer.js` | 2 | 2 | 3 | 2 | 9 | Shared Docs Viewer runtime composition and route loading. |
| 2 | 14 | `assets/docs-viewer/js/docs-viewer-management-modals.js` | 2 | 2 | 1 | 2 | 7 | Docs Viewer management support module. |
| 3 | 15 | `assets/docs-viewer/js/docs-viewer-management.js` | 2 | 2 | 1 | 2 | 7 | Docs Viewer management coordinator. |
| 4 | 18 | `assets/docs-viewer/js/docs-viewer-bookmarks.js` | 2 | 2 | 1 | 1 | 6 | Docs Viewer bookmark/favourite support. |
| 5 | 19 | `assets/docs-viewer/js/docs-viewer-management-actions.js` | 2 | 2 | 1 | 1 | 6 | Docs Viewer management support module. |
| 6 | 20 | `assets/docs-viewer/js/docs-viewer-scope-lifecycle.js` | 2 | 2 | 1 | 1 | 6 | Docs Viewer runtime support module. |
| 7 | 33 | `assets/docs-viewer/js/docs-html-import.js` | 2 | 1 | 1 | 2 | 6 | Docs import controller after explicit workflow handoff and focused module-smoke coverage. |
| 8 | 34 | `assets/docs-viewer/js/docs-html-import-workflow.js` | 2 | 1 | 1 | 1 | 5 | Docs import preview/write workflow helper. |
| 9 | 35 | `assets/docs-viewer/js/docs-viewer-config-controller.js` | 2 | 1 | 1 | 1 | 5 | Docs Viewer config/scope setup. |
| 10 | 36 | `assets/docs-viewer/js/docs-viewer-search-controller.js` | 2 | 1 | 1 | 1 | 5 | Docs Viewer search helper or controller. |
| 11 | 54 | `assets/docs-viewer/js/docs-viewer-document-controller.js` | 1 | 2 | 1 | 1 | 5 | Docs Viewer document rendering/controller support. |
| 12 | 55 | `assets/docs-viewer/js/docs-viewer-reports.js` | 1 | 2 | 1 | 1 | 5 | Docs Viewer runtime support module. |
| 13 | 56 | `assets/docs-viewer/js/docs-viewer-router.js` | 1 | 2 | 1 | 1 | 5 | Docs Viewer routing and history helper. |
| 14 | 59 | `assets/docs-viewer/js/docs-html-import-modals.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 15 | 60 | `assets/docs-viewer/js/docs-html-import-render.js` | 1 | 1 | 1 | 1 | 4 | Docs import result rendering helper. |
| 16 | 61 | `assets/docs-viewer/js/docs-viewer-data.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 17 | 62 | `assets/docs-viewer/js/docs-viewer-drag-drop.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 18 | 63 | `assets/docs-viewer/js/docs-viewer-favourites.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer bookmark/favourite support. |
| 19 | 64 | `assets/docs-viewer/js/docs-viewer-management-capabilities.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 20 | 65 | `assets/docs-viewer/js/docs-viewer-management-client.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 21 | 66 | `assets/docs-viewer/js/docs-viewer-management-config.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 22 | 67 | `assets/docs-viewer/js/docs-viewer-management-interactions.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 23 | 68 | `assets/docs-viewer/js/docs-viewer-management-render.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 24 | 69 | `assets/docs-viewer/js/docs-viewer-render.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer rendering helper. |
| 25 | 70 | `assets/docs-viewer/js/docs-viewer-search.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer search helper or controller. |
| 26 | 71 | `assets/docs-viewer/js/docs-viewer-sidebar.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 27 | 72 | `assets/docs-viewer/js/docs-viewer-tree.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 28 | 73 | `assets/docs-viewer/js/reports/change-history-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 29 | 74 | `assets/docs-viewer/js/reports/docs-index-table-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 30 | 75 | `assets/docs-viewer/js/reports/reports-list-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 31 | 76 | `assets/docs-viewer/js/reports/semantic-references-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 32 | 77 | `assets/docs-viewer/js/reports/source-config-report.js` | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |

## Follow-Up Notes

### `assets/docs-viewer/js/docs-viewer.js`

- Current risk score: 9.
- Track separately from the all-script target-score plan because it is the shared Docs Viewer entry runtime.
- Useful future slices should reduce shared-runtime coupling or route-load cost, such as generated-payload loading, loadable-doc visibility state, index panel ownership, or management lazy-boundary hardening.
- Do not turn the entry file into a thin pass-through layer if that makes the viewer boot sequence harder to inspect.

### Docs Import And Management

- Keep import result rendering in `assets/docs-viewer/js/docs-html-import-render.js`.
- Keep preview/write orchestration in `assets/docs-viewer/js/docs-html-import-workflow.js`.
- Keep management-only workflows behind the lazy management boundary.
- Move command-specific write behavior to `assets/docs-viewer/js/docs-viewer-management-actions.js` or a workflow-specific module when it gains independent state.

### Reports, Search, And Bookmarks

- Keep reports self-contained and loaded through the report allowlist.
- Extract shared report table or pager helpers only after at least two reports need the same behavior.
- Keep search and bookmark storage/controller behavior focused; revisit if grouping, sync, export, or cross-scope behavior is added.

## Refresh Notes

1. Refresh [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) first using the parent inventory scoring model.
2. Copy the Docs Viewer subset into this document and preserve the category columns.
3. Update follow-up notes only for files whose risk category changed or where new implementation work is planned.
4. Keep `assets/docs-viewer/js/docs-viewer.js` separate from the all-script implementation plan unless the user explicitly starts that shared-runtime track.

## Related References

- [JavaScript Inventory Policy](/docs/?scope=studio&doc=studio-javascript-payload-inventory)
- [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory)
- [JavaScript Inventory Implementation Plan](/docs/?scope=studio&doc=javascript-inventory-implementation-plan)

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
It uses the same four-risk scoring model as the parent inventory, but limits the table and follow-up tasks to browser JavaScript under `assets/docs-viewer/js/`.

Use this document after material Docs Viewer feature additions or refactors to confirm that new work still fits the intended viewer boundaries:

- shared reader/search/history behavior stays in the shared runtime and focused helpers
- management-only workflows stay behind the lazy management boundary
- import, report, modal, status, and write orchestration work has a clear owner
- the all-script JavaScript risk-reduction work can be reviewed separately from remaining Docs Viewer-specific follow-up

## Upcoming Index Panel Work

A forthcoming change request is expected to introduce a generic Docs Viewer index panel with `collapsed`, `normal`, and `expanded` states.
The initial panel content will remain the existing tree index, but the expanded state is intended to create a reusable workspace for later semantic or graph-based index surfaces.
The graph index itself should be a separate project.

Treat that change request as distinct from this inventory, but use this inventory to identify prerequisite risk work before implementation.
The likely prerequisite is to establish a focused index panel/layout owner so `assets/docs-viewer/js/docs-viewer.js` does not absorb another broad interactive-surface responsibility.
Related follow-up should preserve `assets/docs-viewer/js/docs-viewer-sidebar.js` as the tree renderer inside the panel rather than making the tree index own panel state.

## Current Summary

Measured on 2026-05-20 from [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory).

- Docs Viewer browser JavaScript files in the full inventory: 30
- Highest current Docs Viewer risk score: 10
- High-priority Docs Viewer threshold: 9 or higher
- Main remaining risk themes: Docs Import workflow ownership, shared runtime composition, management coordinator growth, and report/module review boundaries

## Current Priorities

| Docs rank | Full rank | File | Risk score | Focus |
| ---: | ---: | --- | ---: | --- |
| 1 | 3 | `assets/docs-viewer/js/docs-html-import.js` | 10 | Docs import preview/write workflow and result rendering. |
| 2 | 4 | `assets/docs-viewer/js/docs-viewer.js` | 9 | Shared Docs Viewer runtime composition and route loading. |
| 3 | 8 | `assets/docs-viewer/js/docs-viewer-management.js` | 8 | Docs Viewer management coordinator. |
| 4 | 19 | `assets/docs-viewer/js/docs-viewer-management-modals.js` | 7 | Docs Viewer management support module. |
| 5 | 25 | `assets/docs-viewer/js/reports/change-history-report.js` | 6 | Docs Viewer report module. |
| 6 | 31 | `assets/docs-viewer/js/docs-viewer-bookmarks.js` | 6 | Docs Viewer bookmark/favourite support. |
| 7 | 34 | `assets/docs-viewer/js/docs-viewer-search-controller.js` | 6 | Docs Viewer search helper or controller. |
| 8 | 36 | `assets/docs-viewer/js/docs-viewer-scope-lifecycle.js` | 6 | Docs Viewer runtime support module. |
| 9 | 46 | `assets/docs-viewer/js/docs-viewer-management-actions.js` | 5 | Docs Viewer management support module. |
| 10 | 48 | `assets/docs-viewer/js/docs-viewer-document-controller.js` | 5 | Docs Viewer document rendering/controller support. |
| 11 | 51 | `assets/docs-viewer/js/docs-viewer-config-controller.js` | 5 | Docs Viewer config/scope setup. |
| 12 | 52 | `assets/docs-viewer/js/reports/docs-index-table-report.js` | 5 | Docs Viewer report module. |
| 13 | 53 | `assets/docs-viewer/js/reports/semantic-references-report.js` | 5 | Docs Viewer report module. |
| 14 | 55 | `assets/docs-viewer/js/reports/source-config-report.js` | 5 | Docs Viewer report module. |
| 15 | 59 | `assets/docs-viewer/js/docs-viewer-management-config.js` | 5 | Docs Viewer management support module. |
| 16 | 67 | `assets/docs-viewer/js/docs-viewer-router.js` | 5 | Docs Viewer routing and history helper. |
| 17 | 69 | `assets/docs-viewer/js/docs-viewer-reports.js` | 5 | Docs Viewer runtime support module. |
| 18 | 70 | `assets/docs-viewer/js/docs-viewer-management-interactions.js` | 5 | Docs Viewer management support module. |
| 19 | 72 | `assets/docs-viewer/js/docs-html-import-modals.js` | 5 | Docs Viewer runtime support module. |
| 20 | 83 | `assets/docs-viewer/js/docs-viewer-management-client.js` | 4 | Docs Viewer management support module. |
| 21 | 85 | `assets/docs-viewer/js/docs-viewer-management-capabilities.js` | 4 | Docs Viewer management support module. |
| 22 | 96 | `assets/docs-viewer/js/docs-viewer-data.js` | 4 | Docs Viewer runtime support module. |
| 23 | 105 | `assets/docs-viewer/js/docs-viewer-sidebar.js` | 3 | Docs Viewer runtime support module. |
| 24 | 112 | `assets/docs-viewer/js/docs-viewer-favourites.js` | 2 | Docs Viewer bookmark/favourite support. |
| 25 | 114 | `assets/docs-viewer/js/docs-viewer-search.js` | 2 | Docs Viewer search helper or controller. |
| 26 | 116 | `assets/docs-viewer/js/docs-viewer-drag-drop.js` | 2 | Docs Viewer runtime support module. |
| 27 | 118 | `assets/docs-viewer/js/reports/reports-list-report.js` | 2 | Docs Viewer report module. |
| 28 | 119 | `assets/docs-viewer/js/docs-viewer-management-render.js` | 2 | Docs Viewer management support module. |
| 29 | 122 | `assets/docs-viewer/js/docs-viewer-tree.js` | 2 | Docs Viewer runtime support module. |
| 30 | 125 | `assets/docs-viewer/js/docs-viewer-render.js` | 2 | Docs Viewer rendering helper. |

## Priority Details

### `assets/docs-viewer/js/docs-html-import.js`

- Risk score: 10
- Classification: mixed management workflow controller
- Current role: lazy Docs Import controller for staged source selection, preview, write, result rendering, activity context, and local management-service interaction

**Why This Is Priority Work**

- The file combines UI text loading, scope selection, file selection, import preview, confirmation, write calls, replacement decisions, result rendering, and management-service fallback handling.
- It is lazy and management-only, so transfer-size risk is secondary.
- Maintenance risk remains high because Docs Import crosses HTML and Markdown conversion, media handling, create/overwrite semantics, and local write-service contracts.

**Direction**

- Keep import result rendering in `assets/docs-viewer/js/docs-html-import-render.js`, which owns media plans, warnings, replacement docs, and final status markup.
- Keep preview/write orchestration in `assets/docs-viewer/js/docs-html-import-workflow.js`, which owns service calls, replacement decisions, and write-mode transitions.
- Keep scope selection and route readiness in the controller while passing explicit inputs to conversion and workflow modules.
- Do not split small string-format helpers unless they belong to one of those complete responsibilities.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | done | Moved import result rendering into `assets/docs-viewer/js/docs-html-import-render.js` for media plans, warnings, replacement docs, and final status markup. |
| 2 | done | Extracted preview/write orchestration into `assets/docs-viewer/js/docs-html-import-workflow.js`, which owns service calls, replacement decisions, and write-mode transitions. |
| 3 | proposed | Keep scope selection and route readiness in the controller with explicit inputs to conversion and workflow modules. Anticipated improvement: -1 from architectural risk. |
| 4 | proposed | Add focused checks for preview, replacement, write-mode fallback, and result rendering. Anticipated improvement: -1 from maintenance risk. |

### `assets/docs-viewer/js/docs-viewer.js`

- Risk score: 9
- Classification: mixed shared viewer runtime controller
- Current role: shared entry controller for route boot, scope setup, document loading, sidebar/search/bookmark/controller wiring, global status, and lazy management loading

**Why This Is Priority Work**

- This is the shared runtime for `/docs/`, `/library/`, and `/analysis/`, so performance exposure and architectural consistency matter.
- Router, document pane behavior, search, bookmarks, config, and management have useful focused modules, but the entry controller still owns enough composition and state coordination that new features can drift back into it.
- Recent status work improved ownership by giving document, search, and management feedback separate display channels; the same principle should guide future additions.

**Direction**

- Keep the entry module as the orchestration shell: DOM lookup, boot/config, controller wiring, global route state, and lazy management boundary.
- Add or extend focused modules when a new feature owns a complete responsibility, such as generated-payload loading, route-state projection, status display, or scope behavior.
- Keep management dynamic-loading behind the existing lazy boundary.
- Do not turn the entry file into a thin pass-through layer if that makes the viewer boot sequence harder to inspect.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | proposed | Extract generated-payload loading and loadable-doc visibility state into a focused module when scope or payload behavior next changes. Anticipated improvement: -1 to -2 from maintenance and structural risk. |
| 2 | proposed | Audit the management lazy boundary after management feature additions and move any newly eager setup back behind dynamic loading. Anticipated improvement: -1 to -2 from performance risk if route-load exposure changes. |
| 3 | in progress | Keep status ownership split by feature channel: global/manage, document pane, and search/results pane. Anticipated improvement: -1 from maintenance and architectural risk once this pattern is preserved across follow-up changes. |
| 4 | proposed | Add focused verification around payload loading, scope switching, document visibility state, and status-channel behavior after extraction. Anticipated improvement: -1 from maintenance risk. |

### `assets/docs-viewer/js/docs-viewer-management.js`

- Risk score: 8
- Classification: management coordinator
- Current role: lazy management-mode coordinator for toolbar rendering, status-pill events, metadata/import modal coordination, settings reads, busy/message/reload callbacks, and navigation handoff

**Why This Is Priority Work**

- The module is correctly lazy, but it remains a broad coordinator for many management workflows.
- Several focused owners already exist, so the risk is not raw size alone; it is the chance that future management features re-enter the coordinator instead of the action, render, capability, modal, or lifecycle modules.
- Management status messages still intentionally use the top-level row, so this file is the owner of that display channel.

**Direction**

- Keep command-specific write behavior in `docs-viewer-management-actions.js`.
- Keep status-pill and management-only markup in `docs-viewer-management-render.js`.
- Keep modal shell behavior in `docs-viewer-management-modals.js` and scope create/delete flows in `docs-viewer-scope-lifecycle.js`.
- Add a new management workflow module only when the workflow has its own state machine or service orchestration.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | proposed | Move any newly added management command orchestration out to `docs-viewer-management-actions.js` or a workflow-specific module. Anticipated improvement: -1 from maintenance risk. |
| 2 | proposed | Keep management status ownership explicit and avoid reusing document/search status helpers for management feedback. Anticipated improvement: -1 from architectural risk. |
| 3 | proposed | Add focused checks around management status messages, capability availability, and lazy import behavior when management features change. Anticipated improvement: -1 from maintenance risk. |

### `assets/docs-viewer/js/docs-viewer-management-modals.js`

- Risk score: 7
- Classification: management modal support module
- Current role: reusable management modal shell plus metadata/settings modal helpers and field-state coordination

**Why This Is Priority Work**

- This is a support module rather than a route shell, but it owns several modal shapes and can grow quickly as management actions expand.
- The current boundary is useful as long as it stays focused on modal lifecycle, field state, and reusable modal presentation.

**Direction**

- Keep generic modal shell behavior here.
- Keep command-specific workflow decisions out of this file.
- If one modal family gains complex state or service behavior, extract that family rather than expanding the shared modal helper.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | proposed | Extract a modal family only when it gains independent validation, state, or workflow rules. Anticipated improvement: -1 from maintenance risk. |
| 2 | proposed | Keep metadata/settings modal inputs explicit and avoid broad reads of management state. Anticipated improvement: -1 from structural risk. |

### `assets/docs-viewer/js/reports/change-history-report.js`

- Risk score: 6
- Classification: report module
- Current role: manage-only change-history report rendering, pagination, generated-data reads, and error display

**Why This Is Priority Work**

- Report modules are intentionally self-contained, but this one is the highest-risk report because it combines data fetches, result shaping, pager state, and rendering.
- The pattern it sets matters for future report-backed docs.

**Direction**

- Keep report modules self-contained and loaded only through the report allowlist.
- Extract shared report table or pager helpers only if at least two reports need the same behavior.
- Keep generated-data read checks in the report context rather than hardcoding route assumptions.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | proposed | Extract reusable report pager/table helpers only after another report needs the same behavior. Anticipated improvement: -1 from maintenance risk. |
| 2 | proposed | Add focused report checks for empty, error, pagination, and generated-data unavailable states. Anticipated improvement: -1 from maintenance risk. |

### `assets/docs-viewer/js/docs-viewer-bookmarks.js`

- Risk score: 6
- Classification: bookmark controller
- Current role: bookmark UI state, IndexedDB storage orchestration, bookmark row rendering, and bookmark events

**Why This Is Priority Work**

- The controller owns both storage orchestration and visible bookmark UI behavior.
- It remains acceptable while bookmark behavior is small, but future bookmark grouping, sync, export, or cross-scope behavior could make the file a mixed workflow controller.

**Direction**

- Keep pure bookmark record helpers in `docs-viewer-favourites.js`.
- Extract rendering only if bookmark display grows beyond the current row and edit affordance.
- Keep storage errors routed to the global/failure status channel unless a bookmark-local display is introduced.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | proposed | Extract bookmark row rendering if bookmark display grows into multiple controls or views. Anticipated improvement: -1 from maintenance risk. |
| 2 | proposed | Add focused checks for storage unavailable, save/remove/rename rollback, and cross-scope bookmark keys. Anticipated improvement: -1 from maintenance risk. |

### `assets/docs-viewer/js/docs-viewer-search-controller.js`

- Risk score: 6
- Classification: search controller
- Current role: search index loading, recently-added mode, search result rendering coordination, result counts, and result-panel status display

**Why This Is Priority Work**

- This controller coordinates async data loading, search mode, URL state, result rendering, and status display.
- Recent status-channel work moved search/recent messages into the results panel; future search changes should preserve that ownership.

**Direction**

- Keep pure matching and ordering logic in `docs-viewer-search.js`.
- Keep search/recent panel status display local to this controller or a results-panel helper.
- Extract a results-panel renderer only if result markup, filters, or batching grow.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | in progress | Preserve the results-panel status channel for counts, empty states, and search errors. Anticipated improvement: -1 from architectural risk once the pattern is stable. |
| 2 | proposed | Extract result-panel rendering if filters or result controls grow beyond the current list and more button. Anticipated improvement: -1 from maintenance risk. |
| 3 | proposed | Add focused checks for search loading, no results, result counts, and recent-mode display. Anticipated improvement: -1 from maintenance risk. |

### `assets/docs-viewer/js/docs-viewer-scope-lifecycle.js`

- Risk score: 6
- Classification: management workflow module
- Current role: scope create/delete modal flows, preview summaries, selected delete target, apply result summaries, and lifecycle endpoint coordination through the management client

**Why This Is Priority Work**

- The module has a clear workflow owner, but the workflow is broad enough to revisit after any new scope lifecycle behavior.
- Scope creation touches route creation, source roots, generated data, search, and manifest records, so small UI changes can imply larger service contracts.

**Direction**

- Keep scope lifecycle flow state here rather than pushing it back into `docs-viewer-management.js`.
- Keep endpoint wrappers in `docs-viewer-management-client.js`.
- Extract preview/result rendering only if new lifecycle operations share the same summary model.

**Score Reduction Tasks**

| # | Status | Task |
| ---: | --- | --- |
| 1 | proposed | Keep future scope lifecycle operations inside this workflow module or a sibling lifecycle module. Anticipated improvement: -1 from architectural risk. |
| 2 | proposed | Add focused checks for create/delete required fields, preview summaries, blocked deletes, and apply result summaries. Anticipated improvement: -1 from maintenance risk. |

## Watch Areas

These files are currently medium or low risk. Revisit them when they gain new responsibilities, not merely because they are touched.

- `assets/docs-viewer/js/docs-viewer-management-actions.js`: keep write/action orchestration here; split only if a command becomes its own workflow state machine.
- `assets/docs-viewer/js/docs-viewer-document-controller.js`: keep document pane visibility, payload rendering, report mount handoff, and document-local errors here; extract only if rendering or status behavior grows.
- `assets/docs-viewer/js/docs-viewer-config-controller.js`: keep config and scope setup here; revisit if scope config becomes editable beyond the current management settings path.
- `assets/docs-viewer/js/reports/docs-index-table-report.js`, `assets/docs-viewer/js/reports/semantic-references-report.js`, and `assets/docs-viewer/js/reports/source-config-report.js`: keep each report self-contained unless shared report controls emerge.
- `assets/docs-viewer/js/docs-viewer-router.js`: keep route/history mechanics here; avoid moving DOM rendering or payload fetch implementation into the router.
- `assets/docs-viewer/js/docs-viewer-reports.js`: keep report allowlist and access checks narrow.
- `assets/docs-viewer/js/docs-viewer-management-interactions.js`: keep drag/drop and context-menu interactions here; do not add write orchestration.
- `assets/docs-viewer/js/docs-html-import-modals.js`: keep import modal support here; move workflow decisions to the importer workflow if extracted.
- `assets/docs-viewer/js/docs-viewer-management-client.js` and `assets/docs-viewer/js/docs-viewer-management-capabilities.js`: keep HTTP wrappers and capability probing focused and side-effect-light.
- `assets/docs-viewer/js/docs-viewer-data.js`: keep generated-data fetch helpers route-neutral.
- `assets/docs-viewer/js/docs-viewer-sidebar.js`: keep sidebar/meta rendering focused.
- `assets/docs-viewer/js/docs-viewer-favourites.js`, `assets/docs-viewer/js/docs-viewer-search.js`, `assets/docs-viewer/js/docs-viewer-tree.js`, and `assets/docs-viewer/js/docs-viewer-render.js`: preserve these as pure or mostly pure helpers.
- `assets/docs-viewer/js/docs-viewer-drag-drop.js` and `assets/docs-viewer/js/docs-viewer-management-render.js`: keep as narrow support modules.
- `assets/docs-viewer/js/reports/reports-list-report.js`: remains low risk while it stays a small report registry listing.

## Rerun Notes

1. Refresh [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) first using the parent inventory scoring model.
2. Copy every row whose file path starts with `assets/docs-viewer/js/` into the current priorities table above.
3. Preserve the full-inventory rank so Docs Viewer risk can still be compared with site-wide JavaScript risk.
4. Update detail sections for files with risk score 6 or higher, and any lower-scored file that gained new ownership risk.
5. Keep tasks phrased as complete responsibility slices, with the expected risk category improvement.
6. Cross-check [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary) before adding new runtime, management, import, or report responsibilities.

## Related References

- [JavaScript Inventory Policy](/docs/?scope=studio&doc=studio-javascript-payload-inventory)
- [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [Docs Viewer Management Current State](/docs/?scope=studio&doc=docs-viewer-management-current)

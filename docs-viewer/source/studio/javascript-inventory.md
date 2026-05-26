---
doc_id: javascript-inventory
title: Javascript Inventory
added_date: 2026-05-20
last_updated: 2026-05-21
ui_status: review
parent_id: studio-javascript-payload-inventory
sort_order: 7010
viewable: true
---
# Javascript Inventory

This document lists all browser JavaScript files under `assets/`, scored with the four-risk model defined in [JavaScript Inventory Policy](/docs/?scope=studio&doc=studio-javascript-payload-inventory).

Rescored on 2026-05-21 from the current filesystem inventory.
Category scores may range from 0 to 3 under the current policy.
The normal acceptable target remains 4 or lower; no current row uses a category score of 0.
`docs-viewer/runtime/js/docs-viewer.js` remains in the table for completeness, but implementation work for that shared entry runtime is tracked separately.

## Summary

- Browser JavaScript files under `assets/`: 170
- Total browser JavaScript lines under `assets/`: 44,549
- Files above target score 4, excluding `docs-viewer/runtime/js/docs-viewer.js`: 55
- Target score: 4 or lower, with 4 meaning every risk category is present but low.

| Score | Files |
| ---: | ---: |
| 9 | 0 |
| 8 | 1 |
| 7 | 0 |
| 6 | 17 |
| 5 | 37 |
| 4 | 115 |

## Current Inventory

| Rank | File | Family | Maint. | Struct. | Perf. | Arch. | Risk | Focus |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `docs-viewer/runtime/js/docs-viewer.js` | Docs Viewer separate track | 2 | 2 | 3 | 1 | 8 | Shared Docs Viewer runtime after index-panel state owner extraction; route loading and payload composition remain. |
| 2 | `assets/studio/js/tag-studio.js` | Tag routes | 2 | 1 | 1 | 1 | 5 | Series tag editor route shell after shared route-state projection, shared save-mode re-probe lifecycle extraction, and selected-work/tag-entry interaction state extraction; route boot, shell rendering, event wiring, save handoff, and status/result rendering remain route-local. |
| 3 | `assets/studio/js/catalogue-work-actions.js` | Catalogue editors | 2 | 1 | 2 | 1 | 6 | Work action coordinator after shared save/build/action presentation projection, bulk build-target projection, and Work action record/store sync extraction; service request construction, action sequencing, route refresh, delete navigation, and media refresh remain route-local. |
| 4 | `assets/studio/js/catalogue-work-editor.js` | Catalogue editors | 1 | 2 | 1 | 1 | 5 | Catalogue work route shell after state construction moved to `catalogue-work-editor-state.js` and DOM event binding moved to `catalogue-work-editor-events.js`; validation, update coordination, selection/action context handoff, and Work-specific route-state transitions remain route-local. |
| 5 | `assets/studio/js/bulk-add-work.js` | Studio routes and shared runtime | 2 | 1 | 1 | 1 | 5 | Bulk import/add route shell after shared operational route helper adoption and preview/apply workflow extraction; endpoint calls, activity context, service probing, and event handoff remain route-local. |
| 6 | `assets/studio/js/tag-registry.js` | Tag routes | 2 | 1 | 1 | 1 | 5 | Tag registry route shell after render, modal lifecycle, import-mode, service workflow, shared save-session, and modal workflow extraction; list/filter route handoff and import orchestration remain route-local. |
| 7 | `assets/js/catalogue-search.js` | Public runtime | 2 | 1 | 1 | 1 | 5 | Public catalogue/search route shell after query normalization/evaluation, result ordering, result HTML projection, and metric view-model construction moved to `search/catalogue-search-runtime.js`; route loading, policy/config handoff, DOM event wiring, and instrumentation recording remain local. |
| 8 | `docs-viewer/runtime/js/docs-viewer-management.js` | Docs Viewer non-entry | 2 | 2 | 1 | 1 | 6 | Docs Viewer management coordinator after shared action workflow helper extraction. |
| 9 | `docs-viewer/runtime/js/docs-viewer-management-modals.js` | Docs Viewer non-entry | 2 | 2 | 1 | 1 | 6 | Docs Viewer management modal controller after transient modal shell and metadata parent-picker extraction. |
| 10 | `assets/studio/js/tag-aliases-modals.js` | Tag routes | 2 | 2 | 1 | 1 | 6 | Tag modal rendering after shared shell/focus lifecycle extraction. |
| 11 | `assets/studio/js/tag-registry-modals.js` | Tag routes | 2 | 2 | 1 | 1 | 6 | Tag registry modal rendering after shared shell/focus lifecycle extraction. |
| 12 | `assets/studio/js/tag-aliases.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag aliases route shell after mutation-state, save/import workflow, shared save-session, and modal workflow extraction; list filtering, import orchestration, service action sequencing, and route-state handoff remain route-local. |
| 13 | `assets/studio/js/catalogue-moment-editor.js` | Catalogue editors | 1 | 2 | 1 | 1 | 5 | Catalogue moment route shell after state construction moved to `catalogue-moment-editor-state.js` and DOM event binding moved to `catalogue-moment-editor-events.js`; import/action workflow context, preview sequencing, and dirty-state coordination remain route-local. |
| 14 | `assets/studio/js/catalogue-series-editor.js` | Catalogue editors | 1 | 2 | 1 | 1 | 5 | Catalogue series route shell after state construction moved to `catalogue-series-editor-state.js` and DOM event binding moved to `catalogue-series-editor-events.js`; validation, membership workflow handoff, and action context coordination remain route-local. |
| 15 | `assets/studio/js/catalogue-work-detail-editor.js` | Catalogue editors | 1 | 2 | 1 | 1 | 5 | Catalogue work-detail route shell after state construction moved to `catalogue-work-detail-editor-state.js` and DOM event binding moved to `catalogue-work-detail-editor-events.js`; validation, loaded/new/bulk transitions, and action context coordination remain route-local. |
| 16 | `docs-viewer/runtime/js/docs-viewer-bookmarks.js` | Docs Viewer non-entry | 2 | 2 | 1 | 1 | 6 | Docs Viewer bookmark/favourite support. |
| 17 | `docs-viewer/runtime/js/docs-viewer-management-actions.js` | Docs Viewer non-entry | 2 | 2 | 1 | 1 | 6 | Docs Viewer management support module. |
| 18 | `docs-viewer/runtime/js/docs-viewer-scope-lifecycle.js` | Docs Viewer non-entry | 2 | 2 | 1 | 1 | 6 | Docs Viewer runtime support module. |
| 19 | `assets/studio/js/catalogue-series-actions.js` | Catalogue editors | 2 | 1 | 2 | 1 | 6 | Series action coordinator after shared save/build/action presentation projection; membership mutation, service sequencing, route refresh, and delete navigation remain route-local. |
| 20 | `assets/studio/js/catalogue-work-detail-actions.js` | Catalogue editors | 2 | 1 | 2 | 1 | 6 | Work-detail action coordinator after shared save/build/action presentation projection and bulk build-target projection; single/bulk mutation, service sequencing, route refresh, delete navigation, and media refresh remain route-local. |
| 21 | `assets/studio/js/catalogue-moment-import.js` | Catalogue editors | 2 | 2 | 1 | 1 | 6 | Catalogue route support module. |
| 22 | `assets/studio/js/catalogue-work-sections.js` | Catalogue editors | 2 | 2 | 1 | 1 | 6 | Catalogue section rendering/helper. |
| 23 | `assets/studio/js/data-sharing-prepare.js` | Data sharing | 2 | 2 | 1 | 1 | 6 | Data sharing package preparation route shell after workflow, render, service, and module-smoke coverage. |
| 24 | `assets/studio/js/data-sharing-review.js` | Data sharing | 2 | 1 | 1 | 1 | 5 | Returned-package review route shell after scope/action normalization, apply-action menu state, preview selection state, and result-button projection moved to `data-sharing-review-workflow.js`; service requests, result modal handoff, and route boot remain local. |
| 25 | `docs-viewer/runtime/js/reports/docs-broken-links-report.js` | Docs Viewer non-entry | 2 | 1 | 1 | 1 | 5 | Docs Broken Links report module after the old Studio route controller was retired; scope selection, local Docs API request payloads, sorting, and result rendering are report-local. |
| 26 | `assets/studio/js/project-state.js` | Studio routes and shared runtime | 2 | 1 | 1 | 1 | 5 | Project state route after shared operational required-element, route-state, service-status, and run/open button projection helper adoption; report rendering, service calls, and activity context remain route-local. |
| 27 | `assets/studio/js/catalogue-status.js` | Studio routes and shared runtime | 2 | 1 | 2 | 1 | 6 | Catalogue status route/helper. |
| 28 | `assets/studio/js/series-tags.js` | Tag routes | 2 | 1 | 2 | 1 | 6 | Series Tags route shell after scoring, report rendering, and offline-session activation extraction. |
| 29 | `assets/studio/js/studio-audits.js` | Studio routes and shared runtime | 2 | 1 | 1 | 1 | 5 | Studio audit route after shared operational required-element, ready/busy projection, and audit run-button state adoption; audit normalization, result rendering, and service sequencing remain route-local. |
| 30 | `assets/studio/js/studio-works.js` | Studio routes and shared runtime | 2 | 1 | 2 | 1 | 6 | Browser runtime support module. |
| 31 | `assets/studio/js/thumbnail-quality.js` | Studio routes and shared runtime | 2 | 1 | 1 | 1 | 5 | Thumbnail quality route after shared operational required-element, ready/busy projection, and refresh-button service gating adoption; payload rendering and preview refresh sequencing remain route-local. |
| 32 | `docs-viewer/runtime/js/docs-html-import.js` | Docs Viewer non-entry | 2 | 1 | 1 | 2 | 6 | Docs import controller after explicit workflow handoff and focused module-smoke coverage. |
| 33 | `assets/studio/js/catalogue-moment-actions.js` | Catalogue editors | 2 | 1 | 1 | 1 | 5 | Moment action coordinator after shared preview blocker extraction, save/build normalization, and shared action presentation projection. |
| 34 | `docs-viewer/runtime/js/docs-html-import-workflow.js` | Docs Viewer non-entry | 2 | 1 | 1 | 1 | 5 | Docs import preview/write workflow helper. |
| 35 | `docs-viewer/runtime/js/docs-viewer-config-controller.js` | Docs Viewer non-entry | 2 | 1 | 1 | 1 | 5 | Docs Viewer config/scope setup. |
| 36 | `docs-viewer/runtime/js/docs-viewer-search-controller.js` | Docs Viewer non-entry | 2 | 1 | 1 | 1 | 5 | Docs Viewer search helper or controller. |
| 37 | `assets/js/work.js` | Public runtime | 1 | 1 | 1 | 1 | 4 | Public work route shell after series link, back-link, and prev/next navigation projection moved to `public-catalogue-runtime.js`; DOM insertion, series-index loading, refresh handoff, and keyboard navigation remain local. |
| 38 | `assets/studio/js/activity-log.js` | Studio routes and shared runtime | 2 | 1 | 1 | 1 | 5 | Activity log or activity context support. |
| 39 | `assets/studio/js/catalogue-field-registry-review.js` | Studio routes and shared runtime | 2 | 1 | 1 | 1 | 5 | Catalogue route support module. |
| 40 | `assets/studio/js/catalogue-series-selection.js` | Catalogue editors | 2 | 1 | 1 | 1 | 5 | Catalogue selection UI helper. |
| 41 | `assets/studio/js/catalogue-work-detail-selection.js` | Catalogue editors | 2 | 1 | 1 | 1 | 5 | Catalogue selection UI helper. |
| 42 | `assets/studio/js/catalogue-work-form.js` | Catalogue editors | 2 | 1 | 1 | 1 | 5 | Catalogue route support module. |
| 43 | `assets/studio/js/catalogue-work-selection.js` | Catalogue editors | 2 | 1 | 1 | 1 | 5 | Catalogue selection UI helper. |
| 44 | `assets/studio/js/data-sharing-review-apply.js` | Data sharing | 2 | 1 | 1 | 1 | 5 | Data sharing review apply orchestration helper. |
| 45 | `assets/studio/js/series-tag-editor-page.js` | Studio routes and shared runtime | 2 | 1 | 1 | 1 | 5 | Tag route runtime. |
| 46 | `assets/studio/js/studio-config.js` | Studio routes and shared runtime | 2 | 1 | 1 | 1 | 5 | Studio config loader/accessor. |
| 48 | `assets/studio/js/studio-modal.js` | Studio routes and shared runtime | 2 | 1 | 1 | 1 | 5 | Shared Studio modal primitive. |
| 49 | `assets/studio/js/tag-aliases-service.js` | Tag routes | 2 | 1 | 1 | 1 | 5 | Tag service/write orchestration helper. |
| 50 | `assets/studio/js/tag-groups.js` | Tag routes | 2 | 1 | 1 | 1 | 5 | Tag route runtime. |
| 51 | `assets/studio/js/tag-studio-render.js` | Tag routes | 2 | 1 | 1 | 1 | 5 | Tag route rendering helper. |
| 52 | `assets/studio/js/tag-studio-save-controller.js` | Tag routes | 2 | 1 | 1 | 1 | 5 | Tag manual patch/save helper. |
| 53 | `docs-viewer/runtime/js/docs-viewer-document-controller.js` | Docs Viewer non-entry | 1 | 2 | 1 | 1 | 5 | Docs Viewer document rendering/controller support. |
| 54 | `docs-viewer/runtime/js/docs-viewer-reports.js` | Docs Viewer non-entry | 1 | 2 | 1 | 1 | 5 | Docs Viewer runtime support module. |
| 55 | `docs-viewer/runtime/js/docs-viewer-router.js` | Docs Viewer non-entry | 1 | 2 | 1 | 1 | 5 | Docs Viewer routing and history helper. |
| 56 | `assets/studio/js/catalogue-work-route-state.js` | Catalogue editors | 1 | 2 | 1 | 1 | 5 | Work loaded/new/bulk state transition helper; ready/busy detail projection now delegates to shared route boot. |
| 57 | `assets/studio/js/series-tags-modals.js` | Tag routes | 1 | 2 | 1 | 1 | 5 | Tag modal rendering and lifecycle helper. |
| 58 | `docs-viewer/runtime/js/docs-html-import-modals.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 59 | `docs-viewer/runtime/js/docs-html-import-render.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs import result rendering helper. |
| 60 | `docs-viewer/runtime/js/docs-viewer-data.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 61 | `docs-viewer/runtime/js/docs-viewer-drag-drop.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 62 | `docs-viewer/runtime/js/docs-viewer-favourites.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer bookmark/favourite support. |
| 63 | `docs-viewer/runtime/js/docs-viewer-management-capabilities.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 64 | `docs-viewer/runtime/js/docs-viewer-management-client.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 65 | `docs-viewer/runtime/js/docs-viewer-management-config.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 66 | `docs-viewer/runtime/js/docs-viewer-management-interactions.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 67 | `docs-viewer/runtime/js/docs-viewer-management-render.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 68 | `docs-viewer/runtime/js/docs-viewer-render.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer rendering helper. |
| 69 | `docs-viewer/runtime/js/docs-viewer-search.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer search helper or controller. |
| 70 | `docs-viewer/runtime/js/docs-viewer-sidebar.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 71 | `docs-viewer/runtime/js/docs-viewer-tree.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 72 | `docs-viewer/runtime/js/reports/change-history-report.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 73 | `docs-viewer/runtime/js/reports/docs-index-table-report.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 74 | `docs-viewer/runtime/js/reports/reports-list-report.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 75 | `docs-viewer/runtime/js/reports/semantic-references-report.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 76 | `docs-viewer/runtime/js/reports/source-config-report.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 77 | `assets/js/public-catalogue-runtime.js` | Public runtime | 1 | 1 | 1 | 1 | 4 | Public catalogue URL, payload, thumbnail, and work navigation projection helper. |
| 78 | `assets/js/moment.js` | Public runtime | 1 | 1 | 1 | 1 | 4 | Public moment route runtime after shared public catalogue runtime helper adoption. |
| 79 | `assets/js/search/search-performance.js` | Public runtime | 1 | 1 | 1 | 1 | 4 | Public catalogue/search route runtime. |
| 80 | `assets/js/search/search-policy.js` | Public runtime | 1 | 1 | 1 | 1 | 4 | Public catalogue/search route runtime. |
| 81 | `assets/js/site-nav.js` | Public runtime | 1 | 1 | 1 | 1 | 4 | Public navigation enhancement. |
| 82 | `assets/js/swipe-nav.js` | Public runtime | 1 | 1 | 1 | 1 | 4 | Public navigation enhancement. |
| 83 | `assets/js/theme-toggle.js` | Public runtime | 1 | 1 | 1 | 1 | 4 | Public site runtime module. |
| 84 | `assets/studio/js/activity-log-modals.js` | Studio routes and shared runtime | 1 | 1 | 1 | 1 | 4 | Activity log or activity context support. |
| 85 | `assets/studio/js/analysis-tag-scoring.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag route runtime. |
| 86 | `assets/studio/js/catalogue-editor-action-modals.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue editor route/controller. |
| 87 | `assets/studio/js/catalogue-editor-dirty-state.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue editor route/controller. |
| 88 | `assets/studio/js/catalogue-editor-embedded-items.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue editor route/controller. |
| 89 | `assets/studio/js/catalogue-editor-modal-formatters.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue editor route/controller. |
| 90 | `assets/studio/js/catalogue-editor-readiness.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue editor route/controller. |
| 91 | `assets/studio/js/catalogue-editor-records.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue editor route/controller. |
| 92 | `assets/studio/js/catalogue-editor-service-client.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue editor route/controller. |
| 93 | `assets/studio/js/catalogue-media-preview.js` | Studio routes and shared runtime | 1 | 1 | 1 | 1 | 4 | Catalogue route support module. |
| 94 | `assets/studio/js/catalogue-moment-fields.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue route support module. |
| 95 | `assets/studio/js/catalogue-moment-form.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue route support module. |
| 96 | `assets/studio/js/catalogue-moment-sections.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue section rendering/helper. |
| 97 | `assets/studio/js/catalogue-moment-selection.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue selection UI helper. |
| 98 | `assets/studio/js/catalogue-series-fields.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue route support module. |
| 99 | `assets/studio/js/catalogue-series-form.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue route support module. |
| 100 | `assets/studio/js/catalogue-series-membership.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue route support module. |
| 101 | `assets/studio/js/catalogue-series-sections.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue section rendering/helper. |
| 102 | `assets/studio/js/catalogue-work-detail-fields.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue route support module. |
| 103 | `assets/studio/js/catalogue-work-detail-form.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue route support module. |
| 104 | `assets/studio/js/catalogue-work-detail-sections.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue section rendering/helper. |
| 105 | `assets/studio/js/catalogue-work-editor-modals.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue editor route/controller. |
| 106 | `assets/studio/js/catalogue-work-fields.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Catalogue route support module. |
| 107 | `assets/studio/js/data-sharing-adapters.js` | Data sharing | 1 | 1 | 1 | 1 | 4 | Data sharing workflow adapter helper. |
| 108 | `assets/studio/js/data-sharing-prepare-docs.js` | Data sharing | 1 | 1 | 1 | 1 | 4 | Data sharing prepare docs-index projection helper. |
| 109 | `assets/studio/js/data-sharing-prepare-modals.js` | Data sharing | 1 | 1 | 1 | 1 | 4 | Data sharing modal/result helper. |
| 110 | `assets/studio/js/data-sharing-prepare-render.js` | Data sharing | 1 | 1 | 1 | 1 | 4 | Data sharing prepare rendering helper. |
| 111 | `assets/studio/js/data-sharing-prepare-service.js` | Data sharing | 1 | 1 | 1 | 1 | 4 | Data sharing prepare service/write helper. |
| 112 | `assets/studio/js/data-sharing-prepare-workflow.js` | Data sharing | 1 | 1 | 1 | 1 | 4 | Data sharing prepare workflow projection helper. |
| 113 | `assets/studio/js/data-sharing-review-modals.js` | Data sharing | 1 | 1 | 1 | 1 | 4 | Data sharing modal/result helper. |
| 114 | `assets/studio/js/data-sharing-review-render.js` | Data sharing | 1 | 1 | 1 | 1 | 4 | Data sharing review preview rendering helper. |
| 116 | `assets/studio/js/series-tags-import-workflow.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Series Tags import preview/apply workflow helper. |
| 117 | `assets/studio/js/series-tags-render.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Series Tags report and table rendering helper. |
| 118 | `assets/studio/js/studio-activity-context.js` | Studio routes and shared runtime | 1 | 1 | 1 | 1 | 4 | Activity log or activity context support. |
| 119 | `assets/studio/js/studio-data.js` | Studio routes and shared runtime | 1 | 1 | 1 | 1 | 4 | Browser runtime support module. |
| 120 | `assets/studio/js/studio-route-state.js` | Studio routes and shared runtime | 1 | 1 | 1 | 1 | 4 | Studio route ready/busy state helper. |
| 121 | `assets/studio/js/studio-static-route.js` | Studio routes and shared runtime | 1 | 1 | 1 | 1 | 4 | Browser runtime support module. |
| 122 | `assets/studio/js/studio-transport.js` | Studio routes and shared runtime | 1 | 1 | 1 | 1 | 4 | Studio service transport helper. |
| 123 | `assets/studio/js/studio-ui.js` | Studio routes and shared runtime | 1 | 1 | 1 | 1 | 4 | Studio UI selector/class registry. |
| 124 | `assets/studio/js/tag-aliases-domain.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag domain logic helper. |
| 125 | `assets/studio/js/tag-aliases-import-mode.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag route runtime. |
| 126 | `assets/studio/js/tag-aliases-render.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag route rendering helper. |
| 127 | `assets/studio/js/tag-aliases-save.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag manual patch/save helper. |
| 128 | `assets/studio/js/tag-assignments-offline-session.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag assignment offline-session workflow helper. |
| 129 | `assets/studio/js/tag-assignments-offline.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag route runtime. |
| 130 | `assets/studio/js/tag-registry-domain.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag domain logic helper. |
| 131 | `assets/studio/js/tag-registry-import-mode.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag registry import-mode availability helper. |
| 132 | `assets/studio/js/tag-registry-render.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag registry list/control rendering helper. |
| 133 | `assets/studio/js/tag-registry-save.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag manual patch/save helper. |
| 134 | `assets/studio/js/tag-registry-service.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag service/write orchestration helper. |
| 135 | `assets/studio/js/tag-registry-state.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag registry mutation-state projection helper. |
| 136 | `assets/studio/js/tag-registry-workflow.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag registry save/import workflow helper. |
| 137 | `assets/studio/js/tag-studio-domain.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag domain logic helper. |
| 138 | `assets/studio/js/tag-studio-index.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag analytics index route. |
| 139 | `assets/studio/js/tag-studio-modals.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag modal rendering and lifecycle helper. |
| 140 | `assets/studio/js/tag-studio-save.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag manual patch/save helper. |
| 141 | `assets/studio/js/tag-studio-state.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag editor state helper. |
| 142 | `assets/studio/js/tag-studio-suggestions.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag suggestion helper. |
| 143 | `assets/studio/js/tag-studio-interactions.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Series tag editor selected-work, tag-entry, weight, restore, metrics, and dirty-save enablement interaction state owner. |
| 144 | `assets/studio/js/tag-aliases-modal-workflow.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag Aliases modal workflow owner for create/edit, promote, and demote state transitions, validation projection, tag selection, and popup matching. |
| 145 | `studio/ui-catalogue/assets/js/ui-catalogue-demo.js` | UI catalogue | 1 | 1 | 1 | 1 | 4 | Catalogue route support module. |
| 146 | `assets/studio/js/catalogue-editor-route-boot.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Shared Catalogue editor boot, route-state projection, required-element, and lookup-loading helper. |
| 147 | `assets/studio/js/catalogue-editor-action-workflow.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Shared Catalogue save/build normalization, action presentation projection, pending build target projection, and action preview result contract helper. |
| 148 | `assets/studio/js/tag-aliases-state.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag aliases mutation-state projection helper. |
| 149 | `assets/studio/js/tag-aliases-workflow.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag aliases save/import workflow fallback helper. |
| 150 | `assets/studio/js/tag-studio-route-state.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Series tag editor route ready/busy projection helper. |
| 151 | `assets/studio/js/tag-modal-shell.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Shared tag modal shell, focus lifecycle, status, and escaping helper. |
| 152 | `docs-viewer/runtime/js/docs-viewer-management-modal-shell.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer transient management modal shell, focus lifecycle, and choice/text/confirm helper. |
| 153 | `docs-viewer/runtime/js/docs-viewer-management-parent-picker.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer metadata parent-picker matching, popup, active option, and resolution helper. |
| 154 | `docs-viewer/runtime/js/docs-viewer-management-action-workflow.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer management normalize-order and viewability target workflow helper. |
| 155 | `docs-viewer/runtime/js/docs-viewer-index-panel.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer index panel state, persistence migration, toggle projection, and document-pane visibility helper. |
| 156 | `assets/studio/js/catalogue-work-editor-state.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Work editor state factory for required elements, initial route state, derived panel nodes, media config, modal host, and route-state option projection. |
| 157 | `assets/studio/js/catalogue-work-editor-events.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Work editor event binder that attaches DOM listeners and delegates to injected selection, embedded-item, action, and route-state callbacks. |
| 158 | `assets/studio/js/catalogue-work-detail-editor-state.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Work-detail editor state factory for required elements, initial route state, media config, and shared route-state options. |
| 159 | `assets/studio/js/catalogue-work-detail-editor-events.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Work-detail editor event binder that delegates media refresh and action button listeners to injected callbacks. |
| 160 | `assets/studio/js/catalogue-series-editor-state.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Series editor state factory for required elements, initial route state, series type defaults, and membership state maps. |
| 161 | `assets/studio/js/catalogue-series-editor-events.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Series editor event binder that delegates selection, actions, prose import, and membership events to injected callbacks. |
| 162 | `assets/studio/js/catalogue-moment-editor-state.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Moment editor state factory for required elements, initial edit/import route state, import aliases, and preview state defaults. |
| 163 | `assets/studio/js/catalogue-moment-editor-events.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Moment editor event binder that delegates selection, edit actions, import actions, media refresh, and prose import to injected callbacks. |
| 164 | `assets/studio/js/catalogue-work-action-records.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Work action record projection and state-store synchronization helper for single, bulk, create, and publication action responses. |
| 165 | `assets/studio/js/tag-route-save-session.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Shared Tag route save-session helper for service probing, patch fallback state, busy wrapping, focus/pageshow re-probing, and patch-result view projection. |
| 166 | `assets/studio/js/tag-registry-modal-workflow.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag Registry modal workflow owner for create/edit/delete/demote state transitions, validation projection, and apply-result handoff. |
| 167 | `assets/studio/js/studio-operational-route.js` | Studio routes and shared runtime | 1 | 1 | 1 | 1 | 4 | Shared operational Studio route helper for required elements, ready/busy projection, service availability display, and run-button disabled state. |
| 168 | `assets/studio/js/bulk-add-work-workflow.js` | Studio routes and shared runtime | 1 | 1 | 1 | 1 | 4 | Bulk Add Work preview/apply workflow owner for summary rendering, blocked-row details, run-state projection, and status/result shaping. |
| 169 | `assets/studio/js/data-sharing-review-workflow.js` | Data sharing | 1 | 1 | 1 | 1 | 4 | Data Sharing review workflow owner for scope/action normalization, apply-action menu state, selected preview state, control disabled projection, and result-button visibility. |
| 170 | `assets/js/search/catalogue-search-runtime.js` | Public runtime | 1 | 1 | 1 | 1 | 4 | Public catalogue search runtime owner for entry normalization, query matching, result ordering, result HTML projection, cache reuse, and query metric projection. |

## Rerun Notes

Use [JavaScript Inventory Implementation Plan](/docs/?scope=studio&doc=javascript-inventory-implementation-plan) for batching and slice selection.
Refresh this table after material browser JavaScript refactors, after adding new route modules, or before starting a new risk-reduction batch.

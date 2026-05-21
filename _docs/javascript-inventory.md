---
doc_id: javascript-inventory
title: Javascript Inventory
added_date: 2026-05-20
last_updated: 2026-05-21
parent_id: studio-javascript-payload-inventory
sort_order: 7010
hidden: false
---
# Javascript Inventory

This document lists all browser JavaScript files under `assets/`, scored with the four-risk model defined in [JavaScript Inventory Policy](/docs/?scope=studio&doc=studio-javascript-payload-inventory).

Rescored on 2026-05-21 from the current filesystem inventory.
The minimum possible score is 4 because each file receives a score of 1 to 3 for maintenance, structural, performance, and architectural risk.
`assets/docs-viewer/js/docs-viewer.js` remains in the table for completeness, but implementation work for that shared entry runtime is tracked separately.

## Summary

- Browser JavaScript files under `assets/`: 152
- Total browser JavaScript lines under `assets/`: 42,586
- Files above target score 4, excluding `assets/docs-viewer/js/docs-viewer.js`: 56
- Target score: 4, meaning every risk category is at the low-risk floor.

| Score | Files |
| ---: | ---: |
| 9 | 1 |
| 8 | 0 |
| 7 | 5 |
| 6 | 26 |
| 5 | 25 |
| 4 | 95 |

## Current Inventory

| Rank | File | Family | Maint. | Struct. | Perf. | Arch. | Risk | Focus |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `assets/docs-viewer/js/docs-viewer.js` | Docs Viewer separate track | 2 | 2 | 3 | 2 | 9 | Shared Docs Viewer runtime composition and route loading. |
| 2 | `assets/studio/js/tag-studio.js` | Tag routes | 2 | 2 | 2 | 1 | 7 | Series tag editor route shell after route-state projection extraction; editor interaction orchestration remains route-local. |
| 3 | `assets/studio/js/catalogue-work-actions.js` | Catalogue editors | 2 | 2 | 2 | 1 | 7 | Catalogue action workflow helper after shared save outcome and preview blocker extraction. |
| 4 | `assets/studio/js/catalogue-work-editor.js` | Catalogue editors | 2 | 2 | 2 | 1 | 7 | Catalogue editor route shell after shared boot/readiness helper extraction; action workflows remain separate. |
| 5 | `assets/studio/js/bulk-add-work.js` | Studio routes and shared runtime | 2 | 2 | 2 | 1 | 7 | Bulk import/add route workflow. |
| 6 | `assets/studio/js/tag-registry.js` | Tag routes | 2 | 2 | 2 | 1 | 7 | Tag registry route shell after render, import-mode, and workflow extraction. |
| 7 | `assets/js/catalogue-search.js` | Public runtime | 2 | 2 | 1 | 1 | 6 | Public catalogue/search route runtime after lazy performance instrumentation loading, query-token reuse, and cached list expansion. |
| 8 | `assets/docs-viewer/js/docs-viewer-management.js` | Docs Viewer non-entry | 2 | 2 | 1 | 1 | 6 | Docs Viewer management coordinator after shared action workflow helper extraction. |
| 9 | `assets/docs-viewer/js/docs-viewer-management-modals.js` | Docs Viewer non-entry | 2 | 2 | 1 | 1 | 6 | Docs Viewer management modal controller after transient modal shell and metadata parent-picker extraction. |
| 10 | `assets/studio/js/tag-aliases-modals.js` | Tag routes | 2 | 2 | 1 | 1 | 6 | Tag modal rendering after shared shell/focus lifecycle extraction. |
| 11 | `assets/studio/js/tag-registry-modals.js` | Tag routes | 2 | 2 | 1 | 1 | 6 | Tag registry modal rendering after shared shell/focus lifecycle extraction. |
| 12 | `assets/studio/js/tag-aliases.js` | Tag routes | 2 | 1 | 2 | 1 | 6 | Tag aliases route shell after mutation-state and workflow extraction. |
| 13 | `assets/studio/js/catalogue-moment-editor.js` | Catalogue editors | 2 | 2 | 1 | 1 | 6 | Catalogue editor route shell after shared boot/readiness helper extraction; import/action workflows remain separate. |
| 14 | `assets/studio/js/catalogue-series-editor.js` | Catalogue editors | 2 | 2 | 1 | 1 | 6 | Catalogue editor route shell after shared boot/readiness helper extraction; membership/action workflows remain separate. |
| 15 | `assets/studio/js/catalogue-work-detail-editor.js` | Catalogue editors | 2 | 2 | 1 | 1 | 6 | Catalogue editor route shell after shared boot/readiness helper extraction; action workflows remain separate. |
| 16 | `assets/docs-viewer/js/docs-viewer-bookmarks.js` | Docs Viewer non-entry | 2 | 2 | 1 | 1 | 6 | Docs Viewer bookmark/favourite support. |
| 17 | `assets/docs-viewer/js/docs-viewer-management-actions.js` | Docs Viewer non-entry | 2 | 2 | 1 | 1 | 6 | Docs Viewer management support module. |
| 18 | `assets/docs-viewer/js/docs-viewer-scope-lifecycle.js` | Docs Viewer non-entry | 2 | 2 | 1 | 1 | 6 | Docs Viewer runtime support module. |
| 19 | `assets/studio/js/catalogue-series-actions.js` | Catalogue editors | 2 | 1 | 2 | 1 | 6 | Catalogue action workflow helper after shared save outcome and preview blocker extraction. |
| 20 | `assets/studio/js/catalogue-work-detail-actions.js` | Catalogue editors | 2 | 1 | 2 | 1 | 6 | Catalogue action workflow helper after shared save outcome and preview blocker extraction. |
| 21 | `assets/studio/js/catalogue-moment-import.js` | Catalogue editors | 2 | 2 | 1 | 1 | 6 | Catalogue route support module. |
| 22 | `assets/studio/js/catalogue-work-sections.js` | Catalogue editors | 2 | 2 | 1 | 1 | 6 | Catalogue section rendering/helper. |
| 23 | `assets/studio/js/data-sharing-prepare.js` | Data sharing | 2 | 2 | 1 | 1 | 6 | Data sharing package preparation route shell after workflow, render, service, and module-smoke coverage. |
| 24 | `assets/studio/js/data-sharing-review.js` | Data sharing | 2 | 2 | 1 | 1 | 6 | Returned-package review route shell and file/state coordination. |
| 25 | `assets/studio/js/docs-broken-links.js` | Studio routes and shared runtime | 2 | 2 | 1 | 1 | 6 | Docs broken-links audit route. |
| 26 | `assets/studio/js/project-state.js` | Studio routes and shared runtime | 2 | 2 | 1 | 1 | 6 | Project state route workflow. |
| 27 | `assets/studio/js/catalogue-status.js` | Studio routes and shared runtime | 2 | 1 | 2 | 1 | 6 | Catalogue status route/helper. |
| 28 | `assets/studio/js/series-tags.js` | Tag routes | 2 | 1 | 2 | 1 | 6 | Series Tags route shell after scoring, report rendering, and offline-session activation extraction. |
| 29 | `assets/studio/js/studio-audits.js` | Studio routes and shared runtime | 2 | 1 | 2 | 1 | 6 | Studio audit route workflow. |
| 30 | `assets/studio/js/studio-works.js` | Studio routes and shared runtime | 2 | 1 | 2 | 1 | 6 | Browser runtime support module. |
| 31 | `assets/studio/js/thumbnail-quality.js` | Studio routes and shared runtime | 2 | 1 | 2 | 1 | 6 | Thumbnail quality route workflow. |
| 32 | `assets/docs-viewer/js/docs-html-import.js` | Docs Viewer non-entry | 2 | 1 | 1 | 2 | 6 | Docs import controller after explicit workflow handoff and focused module-smoke coverage. |
| 33 | `assets/studio/js/catalogue-moment-actions.js` | Catalogue editors | 2 | 1 | 1 | 1 | 5 | Catalogue action workflow helper after shared preview blocker extraction. |
| 34 | `assets/docs-viewer/js/docs-html-import-workflow.js` | Docs Viewer non-entry | 2 | 1 | 1 | 1 | 5 | Docs import preview/write workflow helper. |
| 35 | `assets/docs-viewer/js/docs-viewer-config-controller.js` | Docs Viewer non-entry | 2 | 1 | 1 | 1 | 5 | Docs Viewer config/scope setup. |
| 36 | `assets/docs-viewer/js/docs-viewer-search-controller.js` | Docs Viewer non-entry | 2 | 1 | 1 | 1 | 5 | Docs Viewer search helper or controller. |
| 37 | `assets/js/work.js` | Public runtime | 2 | 1 | 1 | 1 | 5 | Public site runtime module. |
| 38 | `assets/studio/js/activity-log.js` | Studio routes and shared runtime | 2 | 1 | 1 | 1 | 5 | Activity log or activity context support. |
| 39 | `assets/studio/js/catalogue-field-registry-review.js` | Studio routes and shared runtime | 2 | 1 | 1 | 1 | 5 | Catalogue route support module. |
| 40 | `assets/studio/js/catalogue-series-selection.js` | Catalogue editors | 2 | 1 | 1 | 1 | 5 | Catalogue selection UI helper. |
| 41 | `assets/studio/js/catalogue-work-detail-selection.js` | Catalogue editors | 2 | 1 | 1 | 1 | 5 | Catalogue selection UI helper. |
| 42 | `assets/studio/js/catalogue-work-form.js` | Catalogue editors | 2 | 1 | 1 | 1 | 5 | Catalogue route support module. |
| 43 | `assets/studio/js/catalogue-work-selection.js` | Catalogue editors | 2 | 1 | 1 | 1 | 5 | Catalogue selection UI helper. |
| 44 | `assets/studio/js/data-sharing-review-apply.js` | Data sharing | 2 | 1 | 1 | 1 | 5 | Data sharing review apply orchestration helper. |
| 45 | `assets/studio/js/series-tag-editor-page.js` | Studio routes and shared runtime | 2 | 1 | 1 | 1 | 5 | Tag route runtime. |
| 46 | `assets/studio/js/studio-config.js` | Studio routes and shared runtime | 2 | 1 | 1 | 1 | 5 | Studio config loader/accessor. |
| 47 | `assets/studio/js/studio-dashboard.js` | Studio routes and shared runtime | 2 | 1 | 1 | 1 | 5 | Browser runtime support module. |
| 48 | `assets/studio/js/studio-modal.js` | Studio routes and shared runtime | 2 | 1 | 1 | 1 | 5 | Shared Studio modal primitive. |
| 49 | `assets/studio/js/tag-aliases-service.js` | Tag routes | 2 | 1 | 1 | 1 | 5 | Tag service/write orchestration helper. |
| 50 | `assets/studio/js/tag-groups.js` | Tag routes | 2 | 1 | 1 | 1 | 5 | Tag route runtime. |
| 51 | `assets/studio/js/tag-studio-render.js` | Tag routes | 2 | 1 | 1 | 1 | 5 | Tag route rendering helper. |
| 52 | `assets/studio/js/tag-studio-save-controller.js` | Tag routes | 2 | 1 | 1 | 1 | 5 | Tag manual patch/save helper. |
| 53 | `assets/docs-viewer/js/docs-viewer-document-controller.js` | Docs Viewer non-entry | 1 | 2 | 1 | 1 | 5 | Docs Viewer document rendering/controller support. |
| 54 | `assets/docs-viewer/js/docs-viewer-reports.js` | Docs Viewer non-entry | 1 | 2 | 1 | 1 | 5 | Docs Viewer runtime support module. |
| 55 | `assets/docs-viewer/js/docs-viewer-router.js` | Docs Viewer non-entry | 1 | 2 | 1 | 1 | 5 | Docs Viewer routing and history helper. |
| 56 | `assets/studio/js/catalogue-work-route-state.js` | Catalogue editors | 1 | 2 | 1 | 1 | 5 | Catalogue route support module. |
| 57 | `assets/studio/js/series-tags-modals.js` | Tag routes | 1 | 2 | 1 | 1 | 5 | Tag modal rendering and lifecycle helper. |
| 58 | `assets/docs-viewer/js/docs-html-import-modals.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 59 | `assets/docs-viewer/js/docs-html-import-render.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs import result rendering helper. |
| 60 | `assets/docs-viewer/js/docs-viewer-data.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 61 | `assets/docs-viewer/js/docs-viewer-drag-drop.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 62 | `assets/docs-viewer/js/docs-viewer-favourites.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer bookmark/favourite support. |
| 63 | `assets/docs-viewer/js/docs-viewer-management-capabilities.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 64 | `assets/docs-viewer/js/docs-viewer-management-client.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 65 | `assets/docs-viewer/js/docs-viewer-management-config.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 66 | `assets/docs-viewer/js/docs-viewer-management-interactions.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 67 | `assets/docs-viewer/js/docs-viewer-management-render.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer management support module. |
| 68 | `assets/docs-viewer/js/docs-viewer-render.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer rendering helper. |
| 69 | `assets/docs-viewer/js/docs-viewer-search.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer search helper or controller. |
| 70 | `assets/docs-viewer/js/docs-viewer-sidebar.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 71 | `assets/docs-viewer/js/docs-viewer-tree.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer runtime support module. |
| 72 | `assets/docs-viewer/js/reports/change-history-report.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 73 | `assets/docs-viewer/js/reports/docs-index-table-report.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 74 | `assets/docs-viewer/js/reports/reports-list-report.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 75 | `assets/docs-viewer/js/reports/semantic-references-report.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 76 | `assets/docs-viewer/js/reports/source-config-report.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer report module. |
| 77 | `assets/js/public-catalogue-runtime.js` | Public runtime | 1 | 1 | 1 | 1 | 4 | Public site runtime module. |
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
| 115 | `assets/studio/js/docs-viewer-scope-options.js` | Studio routes and shared runtime | 1 | 1 | 1 | 1 | 4 | Studio Docs Viewer scope option helper. |
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
| 143 | `assets/ui-catalogue/js/ui-catalogue-demo.js` | UI catalogue | 1 | 1 | 1 | 1 | 4 | Catalogue route support module. |
| 144 | `assets/studio/js/catalogue-editor-route-boot.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Shared Catalogue editor boot, readiness, required-element, and lookup-loading helper. |
| 145 | `assets/studio/js/catalogue-editor-action-workflow.js` | Catalogue editors | 1 | 1 | 1 | 1 | 4 | Shared Catalogue save outcome and action preview result contract helper. |
| 146 | `assets/studio/js/tag-aliases-state.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag aliases mutation-state projection helper. |
| 147 | `assets/studio/js/tag-aliases-workflow.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Tag aliases save/import workflow fallback helper. |
| 148 | `assets/studio/js/tag-studio-route-state.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Series tag editor route ready/busy projection helper. |
| 149 | `assets/studio/js/tag-modal-shell.js` | Tag routes | 1 | 1 | 1 | 1 | 4 | Shared tag modal shell, focus lifecycle, status, and escaping helper. |
| 150 | `assets/docs-viewer/js/docs-viewer-management-modal-shell.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer transient management modal shell, focus lifecycle, and choice/text/confirm helper. |
| 151 | `assets/docs-viewer/js/docs-viewer-management-parent-picker.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer metadata parent-picker matching, popup, active option, and resolution helper. |
| 152 | `assets/docs-viewer/js/docs-viewer-management-action-workflow.js` | Docs Viewer non-entry | 1 | 1 | 1 | 1 | 4 | Docs Viewer management normalize-order and viewability target workflow helper. |

## Rerun Notes

Use [JavaScript Inventory Implementation Plan](/docs/?scope=studio&doc=javascript-inventory-implementation-plan) for batching and slice selection.
Refresh this table after material browser JavaScript refactors, after adding new route modules, or before starting a new risk-reduction batch.

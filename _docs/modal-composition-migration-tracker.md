---
doc_id: modal-composition-migration-tracker
title: Modal Composition Migration Tracker
added_date: 2026-05-15
last_updated: "2026-05-15"
ui_status: in-progress
parent_id: ui-request-modal-composition-pattern
sort_order: 20
hidden: false
---
# Modal Composition Migration Tracker

Use this page to start or continue modal migration work quickly.

## Required Reading

Read these first, in order:

- [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)
- [Modal Shell Primitive](/docs/?scope=studio&doc=ui-primitive-modal-shell)
- [Modal Composition Pattern Request](/docs/?scope=studio&doc=ui-request-modal-composition-pattern), only if you need broader rationale

## Basic Rules

- Migrate at page or route level.
- A route is done only when all current modals on that route follow the modal shell contract.
- Split one route into smaller modal slices only for a concrete blocker, and record that blocker here.
- Preserve route ownership of writes, service calls, reloads, navigation, activity logging, and durable page status.
- Modal helpers may own shell rendering, focus, Escape/backdrop/cancel behavior, local required-field checks, returned values, and transient modal status.
- Use the shared Studio modal helper where the page is in Studio.
- Keep Docs Viewer portable implementation details only when needed, but require visual and behavioral parity with the shared contract.
- Do not redesign a modal unless redesign avoids throwaway migration code, prevents new technical debt, or removes a blocker.
- Verify migrated routes with representative modal browser checks, including focus and close behavior.

## Status Values

- `planned`: current modal page identified but not started
- `in-progress`: route is actively being migrated or verified
- `done`: all current modals on that page follow the chosen shell, focus, action-row, validation, CSS, and action-ownership contracts
- `blocked`: page cannot be completed without an explicit design, portability, service, or route-lifecycle decision

The priority order is easiest-first where practical, not scope reduction.
Every row is required before the modal composition request can be considered complete.

## Tracker

| Priority | Status | Page / route | Current modal set | Primary owner files | Migration notes |
| --- | --- | --- | --- | --- | --- |
| 1 | done | `/studio/activity/` | Activity detail notice modal | `assets/studio/js/activity-log.js`, `assets/studio/js/activity-log-modals.js` | Uses the shared `openNoticeModal()` shell. Verified notice body rendering, dialog semantics, compact sizing, close action, Escape/backdrop close behavior, focus return, and default-width modal action buttons with `tests/smoke/activity_log_modal.py`. |
| 2 | done | `/studio/data-sharing/prepare/` | Prepare result modal | `assets/studio/js/data-sharing-prepare.js`, `assets/studio/js/data-sharing-prepare-modals.js` | Uses the shared `openNoticeModal()` shell while keeping package preparation and page status route-owned. Verified structured result content, dialog semantics, default sizing, default-width close action, Escape/backdrop close behavior, focus return, and route-owned prepare payload with `tests/smoke/data_sharing_prepare.py --mock-docs-service`. |
| 3 | done | `/studio/data-sharing/review/` | Review result notice modal and apply confirmation modal | `assets/studio/js/data-sharing-review.js`, `assets/studio/js/data-sharing-review-modals.js` | Uses shared `openNoticeModal()` and `openConfirmDetailModal()` helpers. Verified result-modal dialog semantics, default-width close action, Escape/backdrop/action close behavior, focus return to the preview command, reopenable results, confirmation modal action row, cancel behavior, and route-owned returned-package preflight/apply writes with `tests/smoke/data_sharing_review.py --mock-docs-service`. |
| 4 | done | `/studio/catalogue-work-detail/` | Catalogue action confirmations for publication and delete flows | `assets/studio/js/catalogue-work-detail-editor.js`, `assets/studio/js/catalogue-work-detail-actions.js`, `assets/studio/js/catalogue-editor-action-modals.js` | Uses the shared `confirmCatalogueActionModal()` helper on top of the Studio modal shell. Verified compact confirmation sizing, dialog semantics, default-width action buttons, Escape/backdrop/cancel close behavior, focus return, and route-owned publication/delete apply requests with `tests/smoke/catalogue_work_detail_modal.py`. |
| 5 | planned | `/studio/catalogue-series/` | Catalogue action confirmations for prose overwrite, publication, and delete flows | `assets/studio/js/catalogue-series-editor.js`, `assets/studio/js/catalogue-series-actions.js`, `assets/studio/js/catalogue-editor-action-modals.js` | Similar to work-detail route; keep series membership and publication writes owned by page actions. |
| 6 | planned | `/studio/catalogue-moment/` | Catalogue action confirmations for publication, delete, and related moment actions | `assets/studio/js/catalogue-moment-editor.js`, `assets/studio/js/catalogue-moment-actions.js`, `assets/studio/js/catalogue-editor-action-modals.js` | Similar shared confirmation path; verify moment import/apply ownership does not move into modal helpers. |
| 7 | planned | `/studio/analytics/series-tag-editor/` | Save preview modal | `assets/studio/js/series-tag-editor-page.js`, `assets/studio/js/tag-studio.js`, `assets/studio/js/tag-studio-modals.js` | Single persistent preview modal; confirm clipboard/status behavior stays route-owned. |
| 8 | planned | `/studio/analytics/series-tags/` | Offline session modal and import modal | `assets/studio/js/series-tags.js`, `assets/studio/js/series-tags-modals.js` | Moderate complexity because file import, review rows, conflict resolution, and session actions share one page. |
| 9 | planned | `/studio/catalogue-work/` | Embedded download/link entry modals, embedded delete confirmation, build preview modal, and catalogue action confirmations | `assets/studio/js/catalogue-work-editor.js`, `assets/studio/js/catalogue-work-editor-modals.js`, `assets/studio/js/catalogue-work-actions.js`, `assets/studio/js/catalogue-editor-action-modals.js` | Complex route-owned workflow page; migrate all work-editor modals together unless a specific blocker is recorded. |
| 10 | planned | `/studio/analytics/tag-registry/` | Import, patch, edit, new-tag, demote, delete, and detail confirmation modals | `assets/studio/js/tag-registry.js`, `assets/studio/js/tag-registry-modals.js`, `assets/studio/js/studio-modal.js` | Complex route-owned workflow page with popups inside modals and local write flows. |
| 11 | planned | `/studio/analytics/tag-aliases/` | Import, patch, promotion, demote, edit/create, delete, and detail confirmation modals | `assets/studio/js/tag-aliases.js`, `assets/studio/js/tag-aliases-modals.js`, `assets/studio/js/studio-modal.js` | Similar complexity to Tag Registry; verify promote/demote/delete write ownership remains in route commands. |
| 12 | planned | `/docs/?mode=manage` | Metadata, import, settings, transient confirm/text/choice, and Docs HTML import filename-conflict modals | `_includes/docs_viewer_shell.html`, `_includes/docs_import_shell.html`, `assets/docs-viewer/js/docs-viewer-management.js`, `assets/docs-viewer/js/docs-viewer-management-modals.js`, `assets/docs-viewer/js/docs-html-import.js`, `assets/docs-viewer/js/docs-html-import-modals.js`, `assets/docs-viewer/css/docs-viewer-management.css` | Highest portability risk. Keep Docs Viewer portable implementation if needed, but require parity with the shared composition contract. |
| 13 | planned | `/studio/ui-catalogue/demos/` | Demo modal pattern | `studio/ui-catalogue/demos/`, `assets/ui-catalogue/js/ui-catalogue-demo.js`, `assets/ui-catalogue/css/ui-catalogue-demo.css` | Demo route should be updated after the production contract is stable so examples do not preserve obsolete modal anatomy. |

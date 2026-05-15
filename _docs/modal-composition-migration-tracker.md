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
| 5 | done | `/studio/catalogue-series/` | Catalogue action confirmations for prose overwrite, publication, and delete flows | `assets/studio/js/catalogue-series-editor.js`, `assets/studio/js/catalogue-series-actions.js`, `assets/studio/js/catalogue-editor-action-modals.js` | Uses the shared `confirmCatalogueActionModal()` helper on top of the Studio modal shell. Verified compact confirmation sizing, dialog semantics, default-width action buttons, Escape/backdrop/cancel close behavior, focus return, and route-owned prose import, publication, and delete apply requests with `tests/smoke/catalogue_series_modal.py`. |
| 6 | done | `/studio/catalogue-moment/` | Catalogue action confirmations for publication, delete, and related moment actions | `assets/studio/js/catalogue-moment-editor.js`, `assets/studio/js/catalogue-moment-actions.js`, `assets/studio/js/catalogue-editor-action-modals.js` | Uses the shared `confirmCatalogueActionModal()` helper on top of the Studio modal shell. Verified compact confirmation sizing, dialog semantics, default-width action buttons, Escape/backdrop/cancel close behavior, focus return, and route-owned prose import, publication, and delete apply requests with `tests/smoke/catalogue_moment_modal.py`. |
| 7 | done | `/studio/analytics/series-tag-editor/` | Save preview modal | `assets/studio/js/series-tag-editor-page.js`, `assets/studio/js/tag-studio.js`, `assets/studio/js/tag-studio-modals.js` | Uses the shared Studio modal frame for the persistent preview modal with standard Studio modal and cancel roles. Verified dialog semantics, default-width action buttons, Escape/backdrop/action close behavior, focus containment and return, and route-owned copy/status callback with `tests/smoke/series_tag_editor_modal.py`. |
| 8 | done | `/studio/analytics/series-tags/` | Offline session modal and import modal | `assets/studio/js/series-tags.js`, `assets/studio/js/series-tags-modals.js`, `assets/studio/js/studio-ui.js`, `assets/studio/css/studio.css` | Uses the shared Studio modal shell for compact session and wide import workflow modals. Verified dialog semantics, shell sizing, status slot placement, default-width action rows, focus entry and containment, Escape/backdrop/action close behavior, focus return, and route-owned session/import callbacks with `tests/smoke/series_tags_modal.py`. |
| 9 | done | `/studio/catalogue-work/` | Embedded download/link entry modals, embedded delete confirmation, build preview modal, and catalogue action confirmations | `assets/studio/js/catalogue-work-editor.js`, `assets/studio/js/catalogue-work-editor-modals.js`, `assets/studio/js/catalogue-work-actions.js`, `assets/studio/js/catalogue-editor-action-modals.js` | Uses the shared Studio modal frame and helpers for embedded entry, embedded delete, build-preview notice, prose overwrite, publication, and delete flows. Verified dialog semantics, compact/wide sizing, default-width action rows, entry validation status, focus containment/return where the opener remains stable, Escape/backdrop/action close behavior, and route-owned prose/publication/delete/build-preview requests with `tests/smoke/catalogue_work_modal.py`. |
| 10 | done | `/studio/analytics/tag-registry/` | Import, patch, edit, new-tag, demote, delete, and detail confirmation modals | `assets/studio/js/tag-registry.js`, `assets/studio/js/tag-registry-modals.js`, `assets/studio/js/studio-modal.js` | Uses the shared Studio modal frame for route-owned import, patch, edit, new-tag, demote, and delete workflow modals, plus the shared detail-confirm helper for demotion apply confirmation. Verified dialog semantics, wide workflow sizing for import/patch, default-width action rows, action ordering, primary action styling, focus entry, focus containment, Escape/backdrop/action close behavior, focus return, popup-compatible demote controls, and route-owned import/edit/create/demote/delete/copy callbacks with `tests/smoke/tag_registry_modal.py`. |
| 11 | done | `/studio/analytics/tag-aliases/` | Import, patch, promotion, demote, edit/create, delete, and detail confirmation modals | `assets/studio/js/tag-aliases.js`, `assets/studio/js/tag-aliases-modals.js`, `assets/studio/js/studio-modal.js` | Uses the shared Studio modal frame for route-owned import, patch, promotion, demote, and edit/create workflow modals, plus shared confirm helpers for alias delete and demotion apply confirmation. Verified dialog semantics, wide workflow sizing for import/patch, default-width action rows, action ordering, primary action styling, focus entry, focus containment, Escape/backdrop/action close behavior, focus return, popup-compatible demote/edit controls, and route-owned import/promote/demote/edit/copy callbacks with `tests/smoke/tag_aliases_modal.py`. |
| 12 | done | `/docs/?mode=manage` | Metadata, import, settings, transient confirm/text/choice, and Docs HTML import filename-conflict modals | `_includes/docs_viewer_shell.html`, `assets/docs-viewer/js/docs-viewer-management.js`, `assets/docs-viewer/js/docs-viewer-management-modals.js`, `assets/docs-viewer/js/docs-html-import.js`, `assets/docs-viewer/js/docs-html-import-modals.js`, `assets/docs-viewer/css/docs-viewer-management.css` | Uses the portable Docs Viewer `docsViewer__modal*` shell for management workflow modals and the Docs HTML import filename-conflict modal while preserving Docs Viewer route ownership of writes, service calls, reloads, and durable page state. Verified metadata, import, settings, transient confirm/text/choice, and filename-conflict modal dialog semantics, default-width action rows, focus entry, focus containment, Escape/action close behavior, focus return, and desktop/mobile sizing with `tests/smoke/docs_viewer_management_modal.py`, now included in `./scripts/run_checks.py --profile docs-viewer-smoke`. |
| 13 | done | `/studio/ui-catalogue/demos/` | Demo modal pattern | `studio/ui-catalogue/demos/primitives/modal-shell/index.md`, `assets/ui-catalogue/js/ui-catalogue-demo.js`, `assets/ui-catalogue/css/ui-catalogue-demo.css` | Demo modal anatomy now matches the finalized shell contract with a real hidden/open state, non-focusable backdrop, dialog semantics, header/body/status/action slots, default-width action rows, focus entry, focus containment, Escape/backdrop/action close behavior, focus return, and compact/wide responsive sizing. Verified notice, confirmation, short-input validation, and workflow modal variants on desktop/mobile with `tests/smoke/ui_catalogue_modal_demo.py`, now included in `./scripts/run_checks.py --profile studio-smoke`. |

---
draft: false
doc_id: d-20261010-223124-29fae8
title: Document Action Policy
added_date: "2026-10-10 22:31:24"
last_updated: "2026-10-10 22:51:38"
parent_id: d-20260428-000000-f5ff18
summary: Complete and accepted central configuration for Catalogue Work, collection-host and private-report document action restrictions.
ui_status: done
---
# Document Action Policy

## Requirements

Catalogue Work documents offer only Star and Copy link. All configured collection hosts and the current local private report documents omit Delete, Star and Draft. These are maintained structural documents with code owners. Future public report documents retain their ordinary action defaults, including Star. Action restrictions use exact identities and configured collection ownership without parent or placement validation; publication eligibility remains separately owned.

## Deliverables

One authoritative management-action config, its validated capabilities projection, central browser/service resolution, consistent menu/shortcut/contribution behavior and a bounded redundant-code review. Durable runtime documentation owns configuration and extension guidance. This resolves the Catalogue editing follow-on in Incremental Updates.

## Process

Maintain ordered action rules in the central config. Collection hosts derive from Working collection configuration. Private reports are selected by exact ordinary document IDs so future public reports are not implicitly restricted. Reload the owning service/page after adopting changes. Catalogue authoring continues through Work edits, Refresh and Regenerate; design maintenance owns template changes.

## Current State

Complete and accepted on 2026-10-10. The user accepted the delivery and authorized closure; individual manual scenarios were not itemised, so acceptance does not extend the recorded verification evidence. No document data, Search, publication eligibility or queues were changed; Publish and Git actions remain separate. [Runtime](../Docs_Viewer_Runtime.md#document-action-policy) owns the durable configuration and extension guidance. Retain this delivery for recent-work lookup pending manual archive.

## Delivery Steps

- [x] DA-0 — Readiness: user approved the three policies and central configuration on 2026-10-10; current owners and operation surfaces inspected. Existing selection has no starred hosts/reports. No hierarchy validation, publication changes or test work is required.
- [x] DA-1 — Added validated config, browser capabilities projection and exact-target service guards. Replaced hardcoded Catalogue New/Draft/Delete availability. Edit menus, Index actions/shortcuts and collection contributions consume the policy; checked-row Catalogue package preparation is also excluded. Configured hosts require no source hierarchy inspection.
- [x] DA-2 — Changed-source lint, Python syntax/import/config diagnostics, whitespace/sanitization review, public projection check and site validation passed. UI interaction remains manual; no tests were created, changed or run.
- [x] DA-3 — Distinct final source/diff review resolved the findings below; remaining evidence limits are explicit.
- [x] DA-4 — Updated Runtime, Configuration Map, Catalogue workflow owners, Development Checklist, Planned Features and the Incremental Updates follow-on. The user accepted the delivery and authorized closure on 2026-10-10.

## Review And Evidence

Review separated the Edit trigger from Source-editor availability so Catalogue Star/Copy remain reachable. Copy registration retains its normal capability while its handler checks live policy, avoiding a permanently disabled action when capabilities arrive after mounting. Collection list contributions reproject action policy through their active document context when capabilities change, so pending capabilities do not freeze package availability. The remaining checked-row Prepare package path now uses the same policy in its menu, dispatch and service owner. Restricted Star actions skip selection reads; a known restricted collection Delete skips workflow loading. No compatibility alias was introduced.

The shared Catalogue builder's document-only publication integration is retained deliberately. If a future config explicitly permits authoring, completed edits must still contribute to Publish. This is completion ownership, separate from action availability; the current policy prevents its authoring callers. Intrinsic Catalogue draft/schema constraints and existing ordinary Delete subtree processing remain with their owners, without a new host-placement or descendant-policy audit.

Selected checks passed: `bin/lint-python` and Python compilation for eight changed service sources (`docs_document_actions.py`, `docs_document_rebuild.py`, `docs_management_capabilities_service.py`, `docs_management_draft.py`, `docs_management_mutations.py`, `docs_management_source_service.py`, `docs_selected_documents.py`, and `docs_document_packages/service.py` under `docs-viewer/services/`); `bin/lint-js` for the eleven changed/new management modules named `docs-viewer-management-{actions-renderer,actions,collection-default-contribution,collection-delete-workflow,context-actions,document-actions,document-reports,edit-menu,index-controller,interactions}.js` plus `docs-viewer-management.js`, and shared `docs-viewer-app-runtime.js` under `docs-viewer/runtime/js/`. Review changes received only their affected lint/syntax/import checks.

Read-only imports of management/package services and the configured policy loader passed. The projection resolves three rules, four configured host IDs and 15 private report IDs. `bin/site-code-update` changed only the projected shared runtime callback; its exact diff was inspected. `bin/site-code-update --check` and `bin/site-validate` passed. Focused added-source sanitization found no private paths or credentials; `git diff --check` passed.

No browser automation or direct operation rejection/write/failure scenarios were run. No test specification was requested or approved. The user accepted closeout without itemising manual checks of Catalogue Star/Copy, host/private-report action omissions or an ordinary document's menu. Future unlisted public reports retain defaults by the policy contract; none currently exist to exercise.

Closeout is a status-only documentation edit. A new code review is not applicable; bounded documentation source/diff review reuses the implementation review and verification above. The delivery's parent identity matches Planned Features. No executable checks or document/Search rebuilds were repeated.

## Completion Gates

- [x] Central action projection and corresponding service guards are implemented and source-reviewed.
- [x] Structural ownership uses exact targets with no hierarchy validation.
- [x] Future unlisted public reports retain ordinary defaults, including Star.
- [x] Durable configuration guidance and scoped verification/review evidence are current.
- [x] User accepted the delivery and authorized closure on 2026-10-10; individual manual scenarios were not itemised.

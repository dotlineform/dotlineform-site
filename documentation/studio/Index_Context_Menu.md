---
draft: false
doc_id: d-20261002-100000-94ac6d
title: Index Context Menu
added_date: "2026-10-02 10:00:00"
last_updated: "2026-10-02 10:53:54"
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Index Context Menu

## Requirements And Deliverables

Move Index Export, Prepare package, Delete and Position into the existing Manage tree context menu. Every menu action uses the right-clicked node, independently of the displayed document. Subtree actions include collapsed descendants; collection detail actions retain their separate owner. Remove the second-row controls and their event/render paths without compatibility aliases.

The menu temporarily highlights its target and supports keyboard invocation and navigation. Operation modals identify the target by title and ID and describe descendant scope. Position and deletion of another subtree preserve the displayed document; deletion navigates to a surviving document only when it removes the displayed document. Existing service/capability and source-editing restrictions remain.

## Process

Right-click an Index node, or invoke its menu with Shift+F10/the context-menu key. Choose an action, review its named target in the existing modal, then complete or cancel that operation. Opening or dismissing the menu does not navigate the main pane.

## Delivery Steps

- [x] Readiness: user approved explicit menu targeting and modal identification on 2026-10-02. Management owns invocation/capabilities, the shared action resolver owns target/subtree resolution, and the route owner owns refreshing the tree without navigation.
- [x] Implementation: moved controls, captured explicit targets, identified modal targets, and added a tree refresh that preserves surviving display state.
- [x] Code review: inspected the bounded final diff for mixed targets, lost collection context, stale toolbar paths and focus/refresh side effects. Removed retired control/render/event paths and unused menu refs; modal focus now resolves the current row after replacement. Menu state respects hidden ancestors, source-editing restrictions and capability/busy state. Only subtree actions traverse descendants, and invocation checks only the requested action. No compatibility aliases were introduced.
- [x] Closeout: updated [Runtime](Docs_Viewer_Runtime.md); changed-source lint, whitespace and required public projection/site checks passed. Manual review remains with the user.

Verification budget: changed-source JavaScript lint and `git diff --check` address syntax/static and whitespace defects, with no service or document writes and an expected cost under a minute. If the shared route owner changes, run the required code projection, inspect its exact tracked delta, and run `bin/site-code-update --check` and `bin/site-validate`; these write only tracked public runtime projections and read the site, with an expected cost under a minute. No test code, test runs, browser automation, document/Search rebuild, Publish, commit or push is included. Manual review covers menu placement, highlight, keyboard interaction, modal identity and preservation of an unrelated displayed document/collection detail.

## Current State

Implementation complete. `bin/lint-js` passed for the 14 changed canonical JavaScript modules; `git diff --check` passed. `bin/site-code-update` updated only the shared route workflow projection under `site/`; its exact delta was reviewed, `bin/site-code-update --check` reported all 104 projected files current, and `bin/site-validate` passed. The public management boundary is unchanged: all menu assets remain local-only.

No tests were changed or run; the user confirmed that the test suite needs a complete refactor and should be left aside for this delivery. No live document operations, browser checks, Docs/Search rebuild, Publish, commit or push ran. Manual review should check a right-clicked node different from the main-pane document, target names/IDs and descendant scope in each modal, a collection detail surviving an unrelated Position/Delete, disabled mutations while editing source, keyboard dismissal/restoration, and menu fit under desktop resizing/zoom.

Runtime now owns the durable behavior. Retain this delivery for the user's manual review; recommend retirement once that review is complete. No documents were deleted.

### Prepare Package Loading Correction

Manual review reported “load failed”. A direct read of `/docs/packages/documents` reproduced an empty server response; the source reader still called the removed three-argument builder API and skipped rendering setup outside a full Build. Corrected the builder call, initialized its Catalogue cache at construction and loaded saved related-links inputs before package rendering. Reviewed the three-file production diff, with no aliases, builds or relationship writes. Updated [Package Prepare](Package_Prepare.md) to describe current context-menu targeting and source-reading ownership.

Verification budget: bounded read-only service/HTTP diagnostics and changed-source Python lint address the actual loading exception without tests or package writes. The corrected handler and restarted local endpoint both returned `ok: true` with 41 ordinary records; the endpoint returned HTTP 200. Python lint passed for the three changed files, and whitespace validation passed. The existing `bin/local-all` runner was restarted to activate Python changes before the user's later instruction arrived; future restarts are left to the user. No package preparation, document/Search rebuild, Publish, commit or push was performed.

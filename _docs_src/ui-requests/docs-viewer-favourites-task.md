---
doc_id: ui-request-docs-viewer-favourites-task
title: Docs Viewer Favourites Task
last_updated: 2026-04-19
parent_id: ui-requests
sort_order: 20
---

# Docs Viewer Favourites Task

Status:

- requested implementation task breakdown
- depends on [Docs Viewer Favourites Spec](/docs/?scope=studio&doc=ui-request-docs-viewer-favourites-spec)

## Goal

Implement a shared Docs Viewer favourites feature for:

- `/docs/`
- `/library/`

The work should add:

- a star action in the document header area
- a bookmark pill row above the document viewer area
- inline rename support for bookmark labels
- remove actions inside each pill
- browser-local persistence

This task is explicitly v1. It should use `localStorage` now and avoid prematurely introducing a server-side bookmark contract.

## Implementation Boundary

This should be implemented as a shared Docs Viewer feature.

Likely ownership:

- shared shell markup: `_includes/docs_viewer_shell.html`
- shared runtime: `assets/js/docs-viewer.js`
- shared docs-viewer styling in the site CSS layer used by both scopes
- route shell adjustments only if a small shared config hook is needed

Likely scope-owned routes to verify:

- `docs/index.md`
- `library/index.md`

## Work Items

### 1. Define the shared UI surface

- identify where the star action belongs in the existing document header/content area
- identify where the bookmark pill row should render above the document viewer area
- confirm that the layout does not displace the left docs tree or inline docs search unexpectedly

### 2. Add bookmark persistence

- add browser-local storage for docs-viewer bookmarks
- store bookmarks by at least `scope`, `doc_id`, `label`, and default title
- preserve insertion order unless a clearer ordering rule is adopted during implementation
- load bookmarks at viewer startup

### 3. Add favourite toggle behavior

- compute whether the active doc is already bookmarked
- render unfilled/filled star states
- toggle add/remove from the star action
- update the pill row immediately after toggle

### 4. Render the bookmark pill row

- filter bookmarks to the active viewer scope
- render the pills above the document viewer area
- allow the row to wrap onto multiple lines
- highlight the active bookmarked doc
- open the selected doc when a pill body is clicked

### 5. Implement inline rename

- add a separate rename mode for pill labels
- keep open and rename actions distinct
- save rename changes to local storage
- fall back to the default doc title when the edited value is empty

### 6. Implement removal

- add an `x` control inside each pill
- prevent remove clicks from also opening the doc
- update star state if the active doc is removed from bookmarks

### 7. Match the intended visual language

- use the compact pill direction from the Series Tag Editor as the styling reference
- make pill text smaller than normal body text
- keep the pill row readable when several items wrap
- make rename mode fit within the pill geometry rather than breaking the row

### 8. Accessibility and keyboard behavior

- make star, pill body, rename, and remove actions keyboard reachable
- provide accessible labels and pressed/selected state where appropriate
- support `Enter`, `Escape`, and blur behavior for rename mode

### 9. Verify both scopes

- verify add/open/rename/remove behavior in `/docs/`
- verify the same shared behavior in `/library/`
- verify reload persistence in both scopes
- verify that the row shows only same-scope bookmarks

## Manual Verification

- open `/docs/?scope=studio&doc=studio-ui-rules`
- add the doc to favourites from the star action
- confirm a bookmark pill appears above the viewer area
- rename the pill label and reload the page
- confirm the custom label persists
- click the pill and confirm it opens the same doc
- remove the pill with `x`
- repeat the same flow in `/library/?doc=library`
- confirm Studio and Library bookmarks do not mix in the same visible row

## Open Decisions

- whether rename mode is entered by double-click, keyboard shortcut, or a dedicated small edit affordance
- whether bookmark ordering should remain insertion order or move most-recently-added to the front
- whether the star action should remove an existing favourite directly or open a tiny confirm-free toggle flow

## Deferred Follow-Up

Out of scope for this task, but likely for a later phase:

- move bookmark persistence from `localStorage` to a server-backed model
- define whether bookmarks are scope-local only or user-global with scope filters
- define migration behavior from local-only bookmarks into any later server-side model

## Done Criteria

- the feature behaves the same way in `/docs/` and `/library/`
- the implementation stays within the shared Docs Viewer module
- bookmark pills match the intended compact visual pattern
- local persistence works without any server component
- the implementation is documented back into the stable Docs Viewer/UI docs when shipped

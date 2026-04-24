---
doc_id: ui-request-docs-viewer-favourites-spec
title: "Docs Viewer Favourites Spec"
added_date: 2026-04-19
last_updated: 2026-04-19
parent_id: ui-requests
sort_order: 10
---

# Docs Viewer Favourites Spec

Status:

- requested UI feature spec
- shared Docs Viewer module change

## Summary

Add browser-style favourites to the shared Docs Viewer used by:

- Studio docs at `/docs/`
- Library docs at `/library/`

The feature adds:

- a star action at the top of the active document
- a favourites row rendered as bookmark pills above the document viewer area
- editable pill labels
- one-click open behavior from the pill row
- inline removal from the pill row

This is a shared module feature, not a Studio-only enhancement.

## Shared Module Boundary

The feature should remain within the current shared Docs Viewer boundary documented in:

- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)

Expected implementation boundary:

- route shells may pass small configuration values if needed
- the shell structure remains shared
- the runtime remains shared

This feature should not trigger a Docs Viewer runtime fork.

## Scope

Included:

- shared Docs Viewer shell UI
- shared Docs Viewer runtime behavior
- Studio docs behavior at `/docs/`
- Library docs behavior at `/library/`
- browser-persisted favourites for docs-viewer documents
- editable bookmark labels

Excluded for this request:

- server-side persistence
- account-level sync
- drag-and-drop reordering
- nested bookmark folders
- import/export of bookmarks
- cross-scope mixed rendering in one pill row

## Product Goals

- let the user favourite frequently used docs from the current viewer
- keep the interaction as familiar as browser bookmarking
- keep the favourites surface visible without displacing the left docs tree
- make the feature work the same way in `/docs/` and `/library/`
- support lightweight personal labeling of saved docs

## Interaction Model

### Star action

The active document header should include a star icon action.

Behavior:

- outline star when the active doc is not favourited
- filled star when the active doc is already favourited
- clicking the star toggles the current doc in favourites
- when a doc is added, the default bookmark label should be the current doc title

### Bookmark pill row

A bookmark row should appear above the document viewer area.

Behavior:

- render only bookmarks for the current viewer scope
- allow the row to wrap across multiple lines
- keep the row outside the left navigation tree
- clicking a pill opens that doc in the current viewer
- the active pill should have a visible selected state

### Editable pill text

The bookmark label should be user-editable.

Default behavior:

- a new bookmark starts with the current doc title
- the saved label can be edited in place
- editing the label should not change the underlying doc title or generated docs data
- custom labels are stored only in browser persistence

Interaction contract:

- clicking the pill body opens the doc
- editing should use a separate inline rename mode rather than making every click ambiguous
- `Enter` saves a rename
- `Escape` cancels the current rename
- blur also saves unless the value is empty
- empty rename input falls back to the doc title

### Remove action

Each pill should include a small `x` remove action.

Behavior:

- clicking `x` removes the bookmark without opening the doc
- if the current active doc is removed, the viewer stays on the current doc and only the bookmark state changes

## Visual Contract

The bookmark pill style should follow the small-pill direction already used in the Series Tag Editor.

Reference route:

- `/studio/series-tag-editor/?series=036&works=00293%2C00294%2C00296`

Required visual traits:

- compact rounded pill treatment
- smaller-than-normal text
- wrap-friendly row layout
- distinct active state
- integrated `x` remove affordance
- editable label field that fits within the pill geometry

The star action should sit near the top of the active doc content area and feel like a viewer-level action, not a page-shell action.

## Persistence Model

Persistence should be browser-local.

For v1, `IndexedDB` should be used from the start.

Reasoning:

- it remains a native browser-side JavaScript solution
- it is persistent per user/browser profile
- it supports a richer bookmark record shape without forcing a server contract too early
- it gives the feature room to grow beyond a fragile key/value model

Server-side persistence may still become useful in a later phase for cross-device or account-level continuity, but it is not required for this feature to be considered permanent and acceptable.

Recommended storage:

- `IndexedDB`

Each bookmark record should carry at least:

- `scope`
- `doc_id`
- `label`
- `default_title`
- `created_at_utc`
- `updated_at_utc`

Behavior:

- bookmarks persist across page reloads
- Studio and Library bookmarks use the same storage model
- the current pill row filters to the current scope so `/docs/` and `/library/` each show their own saved items
- the storage layer should be isolated enough that a later sync/server-backed phase can migrate from the browser store without rewriting the UI behavior

## Accessibility

Required behavior:

- star action is keyboard reachable
- star action exposes favourited/not-favourited state to assistive tech
- pills are keyboard reachable
- rename mode is keyboard usable
- remove action has an explicit accessible label
- focus handling remains stable when opening, renaming, or deleting bookmarks

## Benefits

- faster return to frequently used docs
- personal organization without changing the shared docs corpus
- one shared improvement benefits both `/docs/` and `/library/`

## Risks

- header area may become visually busier
- rename interaction can conflict with open behavior if not kept explicit
- browser-local persistence still means bookmarks do not follow the user between browsers or machines

## Future Phase Note

If the feature proves useful and the interaction model stabilizes, a later phase should evaluate:

- server-side persistence
- cross-device continuity
- migration from `IndexedDB` into any future synced persistence model
- whether bookmark labels and ordering become part of a durable user profile model

## Acceptance Criteria

- the active document in `/docs/` can be favourited from a star action in the viewer
- the active document in `/library/` can be favourited through the same shared interaction
- favourited docs appear as pills above the document viewer area
- pill labels are smaller than normal body text
- the pill row wraps cleanly across lines
- clicking a pill opens that doc in the viewer
- pill labels can be renamed in place
- each pill can be removed with an `x`
- favourites persist across reload in the same browser
- the feature is implemented as a shared Docs Viewer addition rather than separate `/docs/` and `/library/` implementations

## Related References

- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [UI Framework](/docs/?scope=studio&doc=ui-framework)
- [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework)
- [Docs Viewer Favourites Task](/docs/?scope=studio&doc=ui-request-docs-viewer-favourites-task)

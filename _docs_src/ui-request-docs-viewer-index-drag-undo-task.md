---
doc_id: ui-request-docs-viewer-index-drag-undo-task
title: "Docs Viewer Index Drag Undo"
added_date: 2026-04-25
last_updated: 2026-04-25
parent_id: ui-requests
sort_order: 50
---

# Docs Viewer Index Drag Undo Task

Status:

- implemented first pass
- belongs to the shared Docs Viewer manage-mode surface

Implemented files:

- `_includes/docs_viewer_shell.html`
- `assets/js/docs-viewer.js`
- `assets/css/main.css`
- `assets/studio/data/studio_config.json`

## Goal

Refine manage-mode Docs Viewer tree editing so drag/drop can populate any node and one recent move can be undone from the index toolbar.

The feature applies to:

- `/docs/?mode=manage`
- `/library/?mode=manage`

## Requirements

### Move Undo

- add a one-history-step Undo action for the most recent docs-tree move
- cover moves that change `parent_id`, `sort_order`, or both
- make Undo available only after a successful move in the current viewer session
- clear or replace the undo history when another move succeeds
- disable or hide Undo when there is no move to undo
- keep Undo scoped to index/tree operations, not document content edits
- show local command feedback after undo succeeds or fails

The Undo action should restore the moved document's previous tree metadata through the docs-management write path, then rebuild/reload the same docs scope in the same way as other management writes.

### Toolbar Placement

The Undo control belongs in the index toolbar/header space because it reverses a tree/index operation.

Placement rules:

- use an icon button with an undo/curved-arrow visual
- place it in the left index toolbar space where the sidebar expand/collapse control currently lives
- align it to the left side of that toolbar area
- keep it visually connected to the index, not the document-content toolbar
- preserve the existing sidebar collapse control behavior

### Drag/Drop Tree Rule

All docs-viewer nodes can potentially contain children.

Required behavior:

- dropping onto any node may make that node the moved doc's parent
- a node does not need existing children before it can receive children
- no `folder` front matter field should be added
- no generated docs schema field should be added for folder state
- "folder" remains a viewer UI concept derived from tree behavior, not a source-data concept
- nodes remain loadable unless they are already special non-loadable nodes such as `_archive`

This replaces the current practical limitation where only a collapsed node with existing children behaves like an inside drop target.

Implemented v1 note:

- the upper/main part of a target row drops inside that node
- the lower edge of a target row drops after that node
- the Undo button stores one successful move in browser memory for the current viewer session
- Undo reuses the existing metadata update endpoint; no dedicated undo endpoint was added

## Implementation Notes

Likely ownership:

- shared shell markup in `_includes/docs_viewer_shell.html`
- shared runtime in `assets/js/docs-viewer.js`
- shared docs-viewer CSS in `assets/css/main.css`
- docs-management server only if a dedicated undo endpoint is preferred over reusing metadata/move writes
- follow-up docs under the Docs Viewer management/runtime docs after implementation

The implementation should preserve the current front-matter-only tree model:

- source files do not move on disk
- drag/drop writes `parent_id` and `sort_order`
- generated docs payloads are rebuilt after successful writes
- sparse `sort_order` values remain acceptable

## Benefits

- empty sections can be populated directly from the viewer
- Archive and any other empty grouping node can receive its first child through drag/drop
- users can turn an ordinary node into a parent through the same direct manipulation used elsewhere in the tree
- one-step Undo reduces the cost of accidental reparenting or ordering mistakes
- keeping "folder" out of source metadata avoids a new schema concept before it is necessary

## Risks

- if every node can accept children, accidental reparenting is easier unless the drop affordance is clear
- undo history can become stale if another management operation changes the same doc before undo is used
- an icon-only Undo control needs accessible labeling and disabled state feedback
- placing another control in the index toolbar may crowd the existing sidebar collapse affordance on narrow layouts

## Verification

Codex-run checks:

- syntax-check `assets/js/docs-viewer.js` after implementation
- run the relevant docs-management dry-run or direct endpoint check for move and undo behavior
- rebuild the affected docs scope after docs changes
- run a Jekyll build to catch template/CSS integration issues if shell or CSS changes are made

Manual checks:

- in `/library/?mode=manage`, drag a root doc onto empty Archive and confirm it becomes a child of Archive
- use Undo and confirm the doc returns to its prior parent and order
- drag a doc onto an ordinary node with no children and confirm that ordinary node becomes its parent
- confirm the target node remains openable as a document after gaining children
- confirm Undo is disabled or hidden before any move and after the one available undo is consumed
- confirm sidebar collapse still works on desktop and the toolbar does not overlap on mobile

## Related References

- [UI Requests](/docs/?scope=studio&doc=ui-requests)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Viewer Management](/docs/?scope=studio&doc=docs-viewer-management)
- [Docs Viewer Runtime Boundary](/docs/?scope=studio&doc=docs-viewer-runtime-boundary)
- [UI Framework](/docs/?scope=studio&doc=ui-framework)

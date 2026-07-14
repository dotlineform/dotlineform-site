---
doc_id: site-request-docs-viewer-index-multiple-selection
title: Docs Viewer Index Multiple Selection
added_date: 2026-07-14
last_updated: 2026-07-14
ui_status: draft
parent_id: change-requests
---
# Docs Viewer Index Multiple Selection

Status: proposed

## Summary

Add fast desktop multiple selection to the manage-mode Docs Viewer index tree, then let focused consumers use that selection.

The first consumer should extend the existing drag/drop reparent action so a selected group can be moved to a new parent in one operation. Later toolbar actions should be able to consume the same selection without introducing a second selection model.

The selection interaction must feel immediate. Selection changes remain entirely in browser state and update existing rows directly. Network activity, rebuild work, and busy projection begin only after an action such as drop is committed.

## Documentation Impact

This request owns the proposed behavior until it is implemented and absorbed into stable documentation.

Implementation should update:

- [JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) for the selection owner and any changed module responsibilities
- [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership) for the manage-only selection and move boundaries
- [Source Mutation Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-mutations) for the plural `/docs/move` contract
- [Docs Management Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints) if the endpoint summary changes
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview) only when the workflow is stable enough to describe as current behavior

The [View Capability Contract](/docs/?scope=studio&doc=docs-viewer-view-capability-contract) already reserves selection behavior as a possible future capability. V1 should not add a capability field unless more than the manage-mode `index-tree` view needs selection policy.

## Goals

- match familiar desktop Cmd/Ctrl-click and Shift-click selection behavior
- keep selection separate from the currently open document
- make selection changes local, synchronous, and visually immediate
- preserve the existing single-document open, edit, context-menu, and drag/drop behavior
- provide one selection contract that drag/drop and later toolbar actions can consume
- apply a group reparent as one validated mutation plan and one coordinated rebuild
- keep public and review routes free of manage-only selection behavior

## Non-Goals

- checkboxes or a separate selection mode
- lasso or rectangle selection
- touch drag/drop or mobile selection gestures
- cross-scope moves
- sibling reordering; drag/drop continues to change `parent_id` only
- implicit selection of every descendant when a parent is selected
- multiple selection in search, recently-added, review, public, or `index-graph` views
- adding batch delete or unrelated bulk actions in the first implementation
- replacing native HTML drag/drop with a custom pointer-drag system

## Interaction Contract

### Selection

- A normal click keeps the current open-document behavior and makes that row the sole selected row.
- Cmd-click on macOS and Ctrl-click elsewhere toggles one row without navigating.
- Shift-click selects a range from the selection anchor through the clicked row without navigating.
- The range is based on the currently rendered tree-row order. Collapsed descendants are not part of a visible range.
- The open document remains represented by `aria-current="page"` and the existing active style. Multiple selection uses a distinct visual state and must not overload `selectedDocId`.
- Selection changes update row state directly. They do not rebuild or rerender the index tree, load a document, or call the management service.
- Selection is pruned against the current index whenever the index is reloaded.
- Selection is cleared when the scope changes or when the active index view no longer exposes the tree.

### Dragging

- Dragging a selected row drags the current selection.
- Dragging an unselected row first replaces the selection with that row, then drags it.
- Every dragged row receives the dragging projection; the destination keeps the existing root/inside drop projection.
- Drop is rejected when the destination is a moved document or lies inside any moved document's subtree.
- A selected descendant whose ancestor is also selected remains selected visually, but is removed from the effective move roots. Moving the selected ancestor preserves the existing subtree instead of flattening the descendant.
- Selection and dragover remain local and synchronous. The management busy state begins only after a valid drop requests the move.
- A failed move retains the selection so the user can retry or choose another destination.

## State And Ownership

Multiple selection is browser UI state, not generated document state and not route state. It must remain separate from `selectedDocument.selectedDocId`, which identifies the document displayed by the route.

| Responsibility | Owner after the change |
| --- | --- |
| selected ids, anchor, toggle/range behavior, pruning, and row projection | new manage-only `docs-viewer-index-selection.js` |
| optional selected-row rendering after a normal sidebar render | shared `docs-viewer-sidebar.js`, through narrow management callbacks only |
| modifier-click interception, drag start/drop event routing, and context-menu coexistence | existing `docs-viewer-management-interactions.js` |
| plural drop eligibility, subtree-cycle checks, root-drop resolution, and effective move roots | existing `docs-viewer-drag-drop.js` |
| busy state, move request, result handling, and index reload | existing management action controller, using a plural move command |
| HTTP transport | existing `docs-viewer-management-client.js` |
| validated source-write and rebuild plan | existing `docs_management_mutations.py` move owner |

The interaction controller should delegate selection rules rather than absorb the selected-id set, range algorithm, and projection logic. The drag/drop helper should remain free of DOM event wiring beyond the existing drop-target inputs.

## Selection Model

The selection owner should expose a small contract such as:

- replace selection with one doc id
- toggle one doc id
- select a visible range from the anchor
- return selected ids in visible/index order
- prune missing ids
- clear selection
- project the current selection onto rendered rows

The owner may keep a `Set` for membership and a separate anchor id. Range resolution should use a supplied ordered list of currently rendered row ids rather than rebuilding the tree model.

The selection owner should preserve the exact user selection. Consumer-specific normalization, such as reducing selected ancestors and descendants to effective move roots, belongs to the move/drag boundary rather than selection state.

## Extending Drag/Drop

The existing native drag/drop implementation remains the basis for V1.

The current singular `dragDocId`, `onMoveDoc`, and `handleMoveDoc` flow should become plural internally:

- `dragDocIds`
- `onMoveDocs(docIds, parentId)`
- `handleMoveDocs(docIds, parentId)`
- `moveManagedDocs(docIds, parentId)`

Single-document dragging continues through the same path with a one-item array. Do not retain parallel singular compatibility callbacks after all internal callers and focused tests have moved to the plural contract.

Drop validation should operate on effective move roots:

1. normalize and de-duplicate the selected ids
2. reject unknown ids
3. remove a selected id from the effective roots when another selected id is its ancestor
4. validate the destination against every effective root and its descendants
5. skip roots already under the requested parent
6. submit the remaining changed roots as one move request

## Move Service Contract

Prefer generalizing the existing `POST /docs/move` request rather than adding a second bulk-only endpoint.

Proposed request:

```json
{
  "scope": "studio",
  "doc_ids": ["docs-viewer", "development-checklist"],
  "parent_id": "dev-home"
}
```

The current singular `doc_id` request shape should be replaced in the client, service planner, tests, and endpoint documentation in the same change. No dual-shape compatibility layer is required.

The mutation plan should:

- load and validate the scope documents once
- normalize and de-duplicate requested ids
- derive effective move roots using the same parent/descendant rules as the browser
- complete all request validation before writing any source file
- write only effective roots whose `parent_id` changes
- preserve each moved root's existing descendants and source filename
- produce one mutation plan with all required source writes
- run one coordinated docs rebuild and one search update
- update search for the union of each changed root and its descendants
- skip writes and rebuilds when every effective root already has the requested parent

The response should identify requested ids, effective move roots, changed ids, skipped/no-op ids, the requested parent, rebuild diagnostics, summary text, and `dry_run`.

## Implementation Slices

### Slice 1: Multiple Selection Foundation

- add the focused selection owner
- add distinct selected-row styling
- intercept Cmd/Ctrl-click and Shift-click before normal link navigation
- preserve normal click, double-click edit, context menu, expand/collapse, and public behavior
- project selection after ordinary sidebar renders and prune it after index reloads
- expose selected ids to manage-mode consumers

This slice should be usable on its own as a visible selection foundation. Group drag/drop begins in Slice 2.

### Slice 2: Multiple-Document Drag/Drop

- generalize the drag state and callbacks to plural ids
- normalize effective move roots
- validate plural drop destinations
- generalize `/docs/move` to `doc_ids`
- apply one move plan and coordinated rebuild
- reload the index while preserving a sensible open-document target
- retain selection on failure and apply the decided post-success selection behavior

### Slice 3: Optional Toolbar Consumers

Add focused toolbar actions only when a concrete action is requested. Each action should read the same selected-id contract and own its own normalization, confirmation, and service behavior.

Do not add a generic bulk-action framework in advance.

## Verification

Use focused checks rather than a full browser workflow test.

Selection checks should cover:

- normal replacement, Cmd/Ctrl toggle, Shift range, and anchor updates
- visible-order range behavior with collapsed branches
- pruning after index changes
- separation between open-document and multiple-selection state
- direct selected-row projection after render

Drag/drop checks should cover:

- dragging a selected row versus an unselected row
- multiple dragging projections
- parent-plus-descendant normalization
- rejection of every selected subtree as a destination
- unchanged-parent no-op behavior
- root drops and existing single-row behavior through a one-item selection

Mutation-plan checks should cover:

- id normalization and duplicate removal
- validation failure before source writes
- multiple changed roots in one plan
- parent-plus-descendant normalization
- mixed changed and unchanged roots
- search-target union for moved subtrees
- complete no-op requests

Manual UI review should confirm selection contrast, modifier-click interception, drag responsiveness, and coexistence with normal click, double-click edit, context menu, and expand/collapse.

## Open Questions

- Should Shift-click replace the current selection with the anchor range, or add the range to existing disjoint selections? Should Cmd/Ctrl+Shift-click explicitly provide the additive form?
- When Cmd/Ctrl-click removes the anchor row, which remaining row becomes the next Shift-click anchor?
- Should clicking empty index space clear selection?
- After a successful move, should moved roots remain selected, should the destination expand automatically, or should selection clear?
- If a moved selection contains the currently open document or one of its ancestors, which document should remain open after the index reload?
- Should the drag image or management status show the number of documents being moved, or are the selected-row projections sufficient for V1?
- Should right-clicking an unselected row replace the selection, while right-clicking a selected row preserves the group for future context-menu actions?
- When non-viewable documents are hidden after selection, should their ids be pruned immediately or retained until the index data itself changes?
- Is keyboard-only multiple selection needed in the first slice, or should it follow once the pointer interaction is proven?

## Risks To Watch

- modifier-click handling could leak into normal link navigation or new-tab behavior if event ordering is wrong
- active-document and selected-row styles could look indistinguishable
- rebuilding the full sidebar on every selection change would make the interaction feel slower than necessary
- moving selected parents and descendants independently could flatten an intended subtree
- sequential single-document move requests could leave partial results and trigger repeated rebuilds
- adding selection algorithms directly to the interaction controller could turn event routing into another state owner
- preserving stale selected ids across scope or index-view changes could expose incorrect toolbar actions later

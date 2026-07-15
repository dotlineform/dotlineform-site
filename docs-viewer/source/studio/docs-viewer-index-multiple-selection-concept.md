---
doc_id: docs-viewer-index-multiple-selection-concept
title: Index Multiple Selection Concept
added_date: 2026-07-14
last_updated: 2026-07-14
ui_status: proposed
summary: Product concept for fast manage-mode index selection that remains distinct from the open document.
parent_id: docs-viewer-index-multiple-selection
viewable: true
---
# Index Multiple Selection Concept

## Problem

The manage-mode index currently acts on one document at a time. Reparenting several related documents repeats the same interaction and rebuild work, while future multi-document actions would each be tempted to invent their own target rules.

The feature should make selection feel like ordinary desktop tree selection while keeping the open document, selected rows, and action target explicit.

The original drag/drop idea also exposed a wider need: controls in the toolbar, Actions menu, context menu, and selection surface should share a coherent understanding of what an action targets and which capability makes it available. That long-term direction is part of the feature concept even though it should not be implemented as one enormous drag/drop delivery.

## Desired Interaction

- Normal click keeps the current open-document behavior and replaces the selection with that row.
- Cmd-click on macOS or Ctrl-click elsewhere toggles a row without navigating.
- Shift-click selects one visible contiguous range from a stable anchor.
- The primary selection is explicit and remains distinct from both the open document and range anchor.
- Right-click preserves a selected group and makes the clicked row primary; right-clicking outside the group replaces it.
- Empty index space and Escape clear selection without changing the open document.
- Selection changes remain immediate browser state. Network, mutation, rebuild, and busy state begin only when an action is committed.

The first useful consumer is group drag/drop reparenting. Selected ancestors and descendants remain visibly selected, but the move treats only the highest selected ancestors as effective roots so existing subtrees are not flattened.

## Product Boundaries

- Manage-mode `index-tree` only; no public, review, search, recent, graph, or mobile selection contract.
- No checkboxes, lasso, touch drag/drop, cross-scope moves, or sibling reordering.
- No implicit selection of descendants.
- No general batch-action framework.
- Destructive or mutation actions stay single-document until their complete multi-document workflow is separately designed.
- Toolbar, Actions-menu, and context-menu controls may place an action differently, but the same action id must resolve the same targets.
- View placement, action targeting, route enablement, and backend authority remain distinct even when they participate in one coherent capability model.

Keyboard range extension, direct toggle shortcuts, batch delete, and other consumers wait for a demonstrated need.

## Delivery

The action-target prerequisite is already shipped and has its durable owner. Remaining complete outcomes live on the [Docs Viewer Roadmap](/docs/?scope=studio&doc=docs-viewer-roadmap), not as unfinished phases in this feature parent.

When pointer selection becomes current work, its delivery should provide the complete visible selection foundation without also changing drag/drop or backend mutation contracts. Group movement is a separate delivery after selection is proven.

## Questions To Resolve When Relevant

- Is pointer selection useful enough before group movement is available?
- Which selected row should a shared Info panel show when the open document is different?
- Should selection survive an index reload after unrelated changes?
- Which concrete action, if any, should follow group movement as the next multi-document consumer?

These questions belong to the roadmap outcome they can change. They do not keep a broad feature open.

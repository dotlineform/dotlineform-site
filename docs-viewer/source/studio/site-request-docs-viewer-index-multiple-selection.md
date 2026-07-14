---
doc_id: site-request-docs-viewer-index-multiple-selection
title: Docs Viewer Index Multiple Selection
added_date: 2026-07-14
last_updated: 2026-07-14
ui_status: draft
parent_id: change-requests
---
# Docs Viewer Index Multiple Selection

Status: in progress — Slice 0 complete

## Summary

Add fast desktop multiple selection to the manage-mode Docs Viewer index tree, then let focused consumers use that selection.

The first consumer should extend the existing drag/drop reparent action so a selected group can be moved to a new parent in one operation. Later toolbar actions should be able to consume the same selection without introducing a second selection model.

The selection interaction must feel immediate. Selection changes remain entirely in browser state and update existing rows directly. Network activity, rebuild work, and busy projection begin only after an action such as drop is committed.

Before multiple selection is exposed, the existing document-facing controls need one shared action-target contract. Each action should declare whether it operates on the scope, the active document, the primary selection, every selected document, or exactly one selected document. Toolbar, Actions-menu, and context-menu surfaces should resolve those definitions consistently.

## Documentation Impact

This request owns the proposed behavior until it is implemented and absorbed into stable documentation.

Implementation should update:

- [JavaScript Inventory](/docs/?scope=studio&doc=docs-viewer-javascript-inventory) for the selection owner and any changed module responsibilities
- [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership) for the action-definition, manage-only selection, and move boundaries
- [Source Mutation Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints-source-mutations) for the plural `/docs/move` contract
- [Docs Management Endpoints](/docs/?scope=studio&doc=scripts-docs-management-endpoints) if the endpoint summary changes
- [Docs Viewer Overview](/docs/?scope=studio&doc=docs-viewer-overview) only when the workflow is stable enough to describe as current behavior
- [Task Template](/docs/?scope=studio&doc=task-template) and [Task Batch Template](/docs/?scope=studio&doc=task-batch-template) to retain lightweight implementation guidance without requiring placeholder-heavy task prose
- [Development Checklist](/docs/?scope=studio&doc=development-checklist) and [Development Workflow](/docs/?scope=studio&doc=development-workflow) to make pressure-point, ownership, slice, and closeout guidance concise and non-duplicative

The [View Capability Contract](/docs/?scope=studio&doc=docs-viewer-view-capability-contract) already reserves selection behavior as a possible future capability. V1 should not add a capability field unless more than the manage-mode `index-tree` view needs selection policy.

The four general development-guidance documents should be reviewed at implementation closeout, using evidence from the completed slices. This request should not rewrite them abstractly before the work has shown which prompts and gates are genuinely useful.

## Goals

- match familiar desktop Cmd/Ctrl-click and Shift-click selection behavior
- keep selection separate from the currently open document
- make selection changes local, synchronous, and visually immediate
- preserve the existing single-document open, edit, context-menu, and drag/drop behavior
- give every document-facing action one explicit target and selection-cardinality rule
- project the same action behavior through toolbar, Actions-menu, and context-menu surfaces
- provide one selection contract that drag/drop and later toolbar actions can consume
- apply a group reparent as one validated mutation plan and one coordinated rebuild
- keep public and review routes free of manage-only selection behavior
- identify pressure on existing module responsibilities before adding each slice
- keep prerequisite refactors behavior-preserving and prevent them from vertically implementing later capabilities
- use the completed work to improve durable development guidance without adding more ceremony

## Non-Goals

- checkboxes or a separate selection mode
- lasso or rectangle selection
- touch drag/drop or mobile selection gestures
- cross-scope moves
- sibling reordering; drag/drop continues to change `parent_id` only
- implicit selection of every descendant when a parent is selected
- multiple selection in search, recently-added, review, public, or `index-graph` views
- adding batch delete or unrelated bulk actions in the first implementation
- Shift+Arrow, Cmd/Ctrl+Space, or other keyboard range/toggle gestures in the first selection slice
- replacing native HTML drag/drop with a custom pointer-drag system
- creating a dynamic action-registration or plugin framework
- moving handlers, DOM nodes, workflow state, or backend implementation into action definitions
- broad preventive refactoring based on hypothetical future pressure
- using the action-target prerequisite to implement selection gestures, group moves, or batch mutation behavior
- introducing another mandatory task format or treating template completion as evidence of implementation quality
- rewriting the general development workflow before this implementation provides concrete examples

## Interaction Contract

### Selection

- A normal click keeps the current open-document behavior and makes that row the sole selected row.
- Cmd-click on macOS and Ctrl-click elsewhere toggles one row without navigating.
- Shift-click replaces the current selection with one contiguous range from the selection anchor through the clicked row without navigating. Shift-click does not add disjoint ranges; Cmd/Ctrl-click may still create an arbitrary selection by toggling individual rows.
- The range is based on the currently rendered tree-row order. Collapsed descendants are not part of a visible range.
- When Cmd/Ctrl-click removes the range anchor, the first remaining selected row in visible/index order becomes the new anchor. The anchor clears when the selection becomes empty.
- The primary selection is the most recently focused or explicitly targeted selected row. It is distinct from both the open document and the Shift-range anchor.
- Right-clicking a selected row preserves the group and makes that row primary. Right-clicking an unselected row replaces the selection with that row and makes it primary.
- Clicking empty index space or pressing Escape clears the selection without changing the open document.
- The open document remains represented by `aria-current="page"` and the existing active style. Multiple selection uses a distinct visual state and must not overload `selectedDocId`.
- Selection changes update row state directly. They do not rebuild or rerender the index tree, load a document, or call the management service.
- Selection is pruned against the current index whenever the index is reloaded.
- A selected non-viewable document is pruned immediately when the Show non-viewable filter hides its row. Actions must not retain invisible filtered targets.
- Selection is cleared when the scope changes or when the active index view no longer exposes the tree.
- Escape is the only new keyboard selection command required in Slice 1. Shift+Arrow range extension and Cmd/Ctrl+Space toggling may follow after the pointer behavior is proven.

### Dragging

- Dragging a selected row drags the current selection.
- Dragging an unselected row first replaces the selection with that row, then drags it.
- Every dragged row receives the dragging projection; the destination keeps the existing root/inside drop projection.
- Drop is rejected when the destination is a moved document or lies inside any moved document's subtree.
- A selected descendant whose ancestor is also selected remains selected visually, but is removed from the effective move roots. Moving the selected ancestor preserves the existing subtree instead of flattening the descendant.
- Selection and dragover remain local and synchronous. The management busy state begins only after a valid drop requests the move.
- A failed move retains the selection so the user can retry or choose another destination.
- The drag preview should show the first selected document in visible order with a badge containing the total selected-document count.
- After a successful move, the moved documents remain selected and are re-projected after the index reload.
- A successful move does not change the currently open document, including when that document or one of its ancestors was moved. Existing Delete, New, and Import workflows retain ownership of any post-action document change.

## State And Ownership

Multiple selection is browser UI state, not generated document state and not route state. It must remain separate from `selectedDocument.selectedDocId`, which identifies the document displayed by the route. The selection model should expose a stable `primaryDocId` and a separate range-anchor id; visual tree order must not silently choose an action target.

| Responsibility | Owner after the change |
| --- | --- |
| action target/cardinality definitions, one-document adapter, and pure target resolution | manage-owned `docs-viewer/runtime/js/management/docs-viewer-action-definitions.js` |
| selected ids, primary id, range anchor, toggle/range behavior, pruning, and row projection | new manage-only `docs-viewer-index-selection.js` |
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
- set and return the primary selected doc id
- return the range-anchor doc id independently
- return selected ids in visible/index order
- prune missing ids
- clear selection
- project the current selection onto rendered rows

The owner may keep a `Set` for membership plus separate primary and range-anchor ids. Range resolution should use a supplied ordered list of currently rendered row ids rather than rebuilding the tree model.

The selection owner should preserve the exact user selection. Consumer-specific normalization, such as reducing selected ancestors and descendants to effective move roots, belongs to the move/drag boundary rather than selection state.

## Action Definitions

Do not add another extensible registry framework. Add one code-owned action-definitions module containing a small definitions object and a pure resolver.

In this request:

- an action definition describes one action
- the action definitions object contains the known definitions
- the resolver applies a definition to the current active document and selection

The module should expose a shape equivalent to:

```js
const ACTION_DEFINITIONS = {
  "edit-metadata": {
    target: "selection",
    selectionPolicy: "primary"
  },
  delete: {
    target: "selection",
    selectionPolicy: "exactly-one"
  },
  export: {
    target: "scope"
  }
};
```

Supported target values should remain small:

- `scope`: the action is independent of document selection
- `active-document`: the action uses the document currently open in the main view
- `selection`: the action resolves selected document ids through its `selectionPolicy`

Initial selection policies:

- `primary`: resolve only the explicit primary selection even when several docs are selected
- `all`: resolve all selected docs in stable index order
- `exactly-one`: enable only when one doc is selected

`primary` is suitable only when single-document behavior is clear and safe. Destructive actions must not silently fall back to the primary row while several rows remain highlighted. An action may change from `exactly-one` to `all` only when its handler and backend genuinely support the complete selection.

The resolver should receive a selection context containing at least:

- `activeDocId`
- `primaryDocId`
- `selectedDocIds`

It should return resolved target ids, enabled state, and a concise disabled reason. Rendering surfaces may use that projection to adapt labels or titles, but must not independently reinterpret cardinality.

The action definitions own targeting and cardinality only. They do not own command handlers, DOM elements, modal state, transport, mutation behavior, or hosted-view eligibility. Existing view/mode projection continues to decide where a control may appear, and backend capabilities continue to decide whether the service supports an operation.

Initial action classification:

| Action | Initial target rule | Multiple-selection behavior |
| --- | --- | --- |
| Info | selection / `primary` | show the primary selection |
| Edit metadata | selection / `primary` | edit the primary selection |
| Markdown source and Bookmark | `active-document` | continue to use the open document |
| Copy link, Open, Open in VS Code, New sibling, and New child | selection / `primary` | use the primary selection |
| Move | selection / `all` | move effective selected roots in Slice 2 |
| Show/make viewable | selection / `exactly-one` initially | broaden only with an explicit multi-doc workflow |
| Delete | selection / `exactly-one` initially | disable for multiple selection until batch delete is designed |
| Export | `scope` | ignore selection and present clearly as scope export |
| Publish, Rebuild, Settings, Import, and New | `scope` | remain independent of selection |

Toolbar, Actions-menu, and context-menu records should reference the same action id. They may own surface-specific placement, icon, and wording, but they must not create separate target rules for the same action.

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

## Pressure-Point Gate

Every implementation slice must begin with a short ownership and pressure review. The purpose is to notice when a new responsibility would overload an existing owner, while preventing a preparatory refactor from quietly becoming the feature itself.

Record only decisions that affect the slice:

- the complete responsibility being added or changed
- its current owner and the specific pressure already visible there
- whether the current owner can remain a coordinator and delegate the new responsibility
- any extraction required now, with the observed reason for it
- responsibilities deliberately deferred to later slices
- the slice's explicit negative scope

Extraction is justified when the current code provides evidence such as:

- the same policy already being interpreted by multiple UI surfaces
- a broad coordinator being asked to own another complete stateful responsibility
- the next approved slice naturally expanding the same already-pressured owner
- a public/manage or UI/service boundary becoming difficult to preserve
- focused verification being unable to isolate the new seam

Do not extract modules for hypothetical reuse, symmetry, or a possible future feature. A focused extraction should move one coherent responsibility behind a narrow contract while leaving the existing owner as coordinator where appropriate.

Known pressure points at the start of this request:

| Existing area | Visible pressure | Boundary for this request |
| --- | --- | --- |
| `docs-viewer-management.js` | broad management coordinator | compose the new owners; do not add selection rules or action-target policy directly |
| `docs-viewer-management-interactions.js` | already routes navigation, editing, context-menu, and drag/drop events | delegate selection state and range rules to the focused selection owner |
| view definitions, management menu records, and context-menu records | action availability and action targeting can be confused or duplicated | share action ids and target resolution only; do not merge renderers, placement, or lifecycle ownership |
| current `selectedDocId` consumers | many paths assume one open document | bridge existing behavior through the resolver; do not broadly rewrite route or selected-document state |
| singular move client, service, and mutation planner | plural movement crosses browser and backend boundaries | leave unchanged in Slices 0 and 1; generalize together only in Slice 2 |

At the end of every slice, record:

- which module, if any, is now under more pressure
- whether an extraction moved a complete responsibility or merely redistributed fragments
- whether the next slice would expand the same owner
- whether the pressure was observed in the code or only anticipated
- whether a prerequisite accidentally implemented behavior belonging to a later slice

A prerequisite slice must remain behavior-preserving across the stack. A feature slice may be vertical when that is the smallest complete way to deliver its named behavior; that does not authorize adjacent capability work.

## Implementation Slices

Each slice starts and ends with the pressure-point gate. The next slice should not begin until its ownership decision, negative scope, and verification result are recorded in this request or its implementation handoff.

### Slice 0: Action Target Prerequisite — Complete 2026-07-14

- add `docs-viewer-action-definitions.js` with the code-owned definitions object and pure resolver
- classify every current document-facing, scope-facing, toolbar, Actions-menu, and context-menu command
- define active document, primary selection, selected ids, and range anchor as distinct concepts
- make all action surfaces reference the same action ids and resolved targeting rules
- adapt current single-document state to a one-item selection context and preserve current visible behavior
- keep destructive single-document actions on `exactly-one` until a complete multi-document mutation exists
- clarify scope-wide actions such as Export so a document selection does not imply selected-doc export
- add focused resolver checks before multiple-selection behavior is introduced
- complete the pressure-point review before proceeding to the selection owner

This slice removes ambiguous action targeting before the UI can display more than one selected document. It is a prerequisite for Slice 1.

Slice 0 is behavior-preserving. It must not add a selected-id store, modifier-click behavior, selected-row styling, group drag state, plural service requests, batch delete, or other later-slice UI or mutation behavior. Definitions may name future policies such as `all`, but handlers and backend support must remain unchanged until the slice that owns them.

#### Slice 0 Outcome

- added the manage-owned pure action-definition module with 25 code-owned action ids, the three target kinds, the three selection policies, disabled reasons, stable target ordering, and explicit unknown-action rejection
- added a one-document action-context adapter that maps the active route document to active, primary, and selected ids without introducing a selection store
- classified every current main-view toolbar, management toolbar, Actions-menu, context-menu, scope-lifecycle, viewability, and filter action
- added passive `actionId` references to hosted-view control records and one canonical `data-docs-viewer-action` attribute across rendered controls
- routed Edit metadata, Markdown source, Show, Delete, Move, Copy link, Open, Open in VS Code, New sibling, and New child through resolved target ids while retaining their existing handlers and service behavior
- renamed manage-only `currentSelectedDoc` callbacks to `currentActiveDoc`; the shared selected-document route state itself is unchanged
- kept backend capability, hosted-view eligibility, placement, rendering, handlers, workflow state, transport, and mutation ownership outside the definitions module

Focused verification passed: the manage-route smoke now checks the complete action classification, pure resolver projections, canonical rendered action ids, and existing manage flows; the router/module smoke passed; the public-runtime boundary suite passed all six checks; syntax, Python compilation, and whitespace checks passed.

#### Slice 0 Pressure Review

- `docs-viewer-management.js` remains a coordinator. It gained only the one-document context composition and target lookup needed to connect the pure resolver to current state.
- `docs-viewer-management-actions.js` still owns command workflows. It now receives resolved ids rather than interpreting active/selection policy itself.
- `docs-viewer-management-interactions.js` gained no selection state or range rules; it only reads the canonical context-menu action attribute.
- `docs-viewer-view-registry.js` carries a passive `actionId` reference on control records. It does not import the manage-owned definitions or interpret target/cardinality rules.
- No further extraction was justified in Slice 0. The new definition module moved one complete responsibility, while the other changes were narrow connections to that owner.
- The negative scope held: no multiple-selection state, gestures, row projection, drag-group behavior, plural service request, or batch mutation was implemented.
- The next slice would overload the interaction controller and management coordinator if selection rules were added directly; the planned focused selection owner is therefore required before adding that behavior.

#### Slice 1 Handoff

Start Slice 1 from the implemented `docs-viewer-action-definitions.js` contract and add `docs-viewer-index-selection.js` as the complete manage-only owner of selected ids, primary id, range anchor, range/toggle rules, pruning, and row projection.

Implementation boundary:

- replace the one-document adapter inside the management coordinator with the selection owner's context snapshot; keep `selectedDocument.selectedDocId` as the independently active route document
- keep modifier-click, right-click, empty-space, and Escape event recognition in the interaction controller, but delegate every selection transition to the new owner
- project selected-row state through a narrow management callback after ordinary shared sidebar rendering; do not give the shared sidebar ownership of selection state
- re-resolve and re-project all visible actions whenever selection or primary changes; `exactly-one` actions must disable for multiple selection, while scope and active-document actions remain independent
- preserve the active-document behavior of Bookmark and Markdown source
- address the current Info-panel seam explicitly: its shared controller reads the active route document today, while the implemented action definition targets the primary selection. Supply the resolved primary document through a narrow manage-mode context/handoff without moving selection policy or manage-only state into the shared controller
- add empty-space and Escape clearing and immediate pruning of non-viewable rows hidden by the filter
- do not change drag state, move callbacks, `/docs/move`, mutation planning, or backend contracts; those remain Slice 2

Begin with a fresh pressure-point review of `docs-viewer-management-interactions.js`, the management coordinator, the shared Info-panel context seam, and sidebar post-render projection. Verify the selection model as pure behavior first, then use the focused manage route to confirm module wiring and current single-document behavior.

### Slice 1: Multiple Selection Foundation

- add the focused selection owner
- add distinct selected-row styling
- intercept Cmd/Ctrl-click and Shift-click before normal link navigation
- preserve normal click, double-click edit, context menu, expand/collapse, and public behavior
- project selection after ordinary sidebar renders and prune it after index reloads
- clear selection from empty-space clicks and Escape, and prune rows hidden by the Show non-viewable filter
- expose active, primary, selected, and anchor state to the action resolver and manage-mode consumers
- re-project every visible action when selection or primary state changes
- complete the pressure-point review before proceeding to group drag/drop

This slice should be usable on its own as a visible pointer-selection foundation. Group drag/drop begins in Slice 2. Extended keyboard range/toggle behavior remains deferred.

### Slice 2: Multiple-Document Drag/Drop

- generalize the drag state and callbacks to plural ids
- normalize effective move roots
- validate plural drop destinations
- generalize `/docs/move` to `doc_ids`
- apply one move plan and coordinated rebuild
- show the first selected document and total selection count in the drag preview
- reload the index without changing the open document
- retain selection on failure and keep the moved documents selected after success
- complete the pressure-point review before adding any further selection consumer

### Slice 3: Optional Toolbar Consumers

Add or broaden focused toolbar actions only when a concrete action is requested. Each action should update its existing definition, read the resolved target ids, and own its own normalization, confirmation, and service behavior.

Do not add a generic bulk-action framework in advance.

Each consumer is a separate feature slice and must pass the same pressure-point gate. The presence of multiple selection does not imply that every action should become a batch action.

### Slice 4: Durable Guidance Review

After the implementation slices provide real examples, review:

- [Task Template](/docs/?scope=studio&doc=task-template)
- [Task Batch Template](/docs/?scope=studio&doc=task-batch-template)
- [Development Checklist](/docs/?scope=studio&doc=development-checklist)
- [Development Workflow](/docs/?scope=studio&doc=development-workflow)

The outcome should be lightweight guidance and structure, not stricter template compliance. Preserve a small set of useful prompts:

- intended outcome and explicit negative scope
- responsibility and current owner
- observed pressure points and the extraction/defer decision
- bounded implementation slices and prerequisites
- verification evidence
- durable documentation impact and closeout state

Review the documents as one guidance system rather than appending the same rule to all four:

- remove formal placeholders that do not elicit a decision or useful handoff evidence
- distinguish required safety/ownership gates from optional planning prompts
- compress Development Checklist and Development Workflow into one short canonical development-guide document containing the key gates and route through the work; retire or reduce the other document to a clear pointer
- retain one lightweight Task structure and make Task Batch a short variant containing only genuinely batch-specific prompts
- keep long verification-script inventories out of task templates and user-facing handoffs; link to a canonical check/profile where useful and record the verification result
- identify which prompts in this request materially improved implementation or handoff, and preserve only those in durable guidance
- use examples from this implementation to express the pressure-point and post-build cohesion review concretely
- keep feature-specific decisions in this request and stable reusable guidance in the durable documents

This review is a closeout task, not a prerequisite for multiple selection. It must not expand into a general rewrite of the development corpus without a separately agreed scope.

## Verification

Use focused checks rather than a full browser workflow test.

Action-definition checks should cover:

- scope, active-document, primary, all, and exactly-one resolution
- primary selection remaining stable when tree order or expansion changes
- destructive exactly-one actions disabling for multiple selection
- consistent targeting from toolbar, Actions-menu, and context-menu surfaces
- separation between action targeting, hosted-view eligibility, and backend capability checks

Selection checks should cover:

- normal replacement, Cmd/Ctrl toggle, Shift range, and anchor updates
- replacement rather than additive Shift ranges, while retaining arbitrary Cmd/Ctrl toggles
- recalculation of the anchor when its row is toggled off
- visible-order range behavior with collapsed branches
- pruning after index changes
- immediate pruning when selected non-viewable rows are filtered out
- empty-space and Escape clearing without open-document changes
- separation between active document, primary selection, range anchor, and selected ids
- direct selected-row projection after render

Drag/drop checks should cover:

- dragging a selected row versus an unselected row
- multiple dragging projections
- parent-plus-descendant normalization
- rejection of every selected subtree as a destination
- unchanged-parent no-op behavior
- root drops and existing single-row behavior through a one-item selection
- drag preview using the first selected row and total selection count
- selected-row retention and unchanged open document after a successful move

Mutation-plan checks should cover:

- id normalization and duplicate removal
- validation failure before source writes
- multiple changed roots in one plan
- parent-plus-descendant normalization
- mixed changed and unchanged roots
- search-target union for moved subtrees
- complete no-op requests

Slice handoffs should also confirm:

- the pressure-point review identified an observed pressure, an explicit deferral, or no change needed
- any extraction moved a complete responsibility and preserved existing behavior outside the named slice
- the slice's negative scope remained unimplemented
- Slice 0 introduced no selection gestures, multi-row state, plural service behavior, or batch mutations

The durable-guidance review should confirm that the four documents have distinct jobs, do not duplicate or contradict the same gate, and retain practical prompts without making template completion the goal.

Manual UI review should confirm selection contrast, modifier-click interception, drag responsiveness, and coexistence with normal click, double-click edit, context menu, and expand/collapse.

## Risks To Watch

- modifier-click handling could leak into normal link navigation or new-tab behavior if event ordering is wrong
- active-document and selected-row styles could look indistinguishable
- rebuilding the full sidebar on every selection change would make the interaction feel slower than necessary
- moving selected parents and descendants independently could flatten an intended subtree
- sequential single-document move requests could leave partial results and trigger repeated rebuilds
- adding selection algorithms directly to the interaction controller could turn event routing into another state owner
- duplicating action-target rules across toolbar, Actions-menu, and context-menu renderers could make identical actions behave differently
- action definitions could become a second view/capability system if they absorb placement, handlers, workflow state, or backend implementation
- preserving stale selected ids across scope or index-view changes could expose incorrect toolbar actions later
- a prerequisite refactor could implement the later capability vertically and make slice boundaries impossible to verify
- the pressure-point gate could be misused to justify speculative refactoring instead of responding to observed responsibility pressure
- the general templates could remain formal but vague, or become even more ceremonial, if the review adds sections instead of sharpening decisions
- Development Checklist and Development Workflow could drift further if both try to own the same implementation guidance

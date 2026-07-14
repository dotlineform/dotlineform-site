---
doc_id: docs-viewer-index-multiple-selection-architecture
title: Index Multiple Selection Architecture
added_date: 2026-07-14
last_updated: 2026-07-14
ui_status: proposed
summary: Proposed manage-only selection, action-target, drag/drop, and group-mutation boundaries.
parent_id: site-request-docs-viewer-index-multiple-selection
viewable: true
---
# Index Multiple Selection Architecture

## Architectural Outcome

Multiple selection should be one manage-only state owner consumed by existing action and drag/drop boundaries. It must not overload the route's selected document or turn action definitions into a new view, workflow, or plugin system.

## Shipped Foundation

`docs-viewer/runtime/js/management/docs-viewer-action-definitions.js` already owns:

- code-owned action ids
- scope, active-document, and selection targets
- primary, all, and exactly-one selection policies
- pure target resolution and disabled reasons

Current runtime still supplies a one-document selection context, so this foundation preserves existing behavior. [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership) is the durable current-state authority.

## Long-Term Capability Direction

The drag/drop request exposed a Docs Viewer-wide concern larger than selection: an operation may be placed by the view registry, targeted by action definitions, enabled by route features, and authorized by live backend capabilities.

The long-term aim is a coherent model across toolbar, Actions-menu, context-menu, and selection consumers, with each decision still owned in the correct layer:

- the view registry owns known views, controls, placement, and eligibility
- action definitions own operation identity, target, and cardinality
- route features enable known frontend behavior
- live backend capabilities state real service authority
- focused controllers own workflow and state

That may justify further registry or diagnostic work when another concrete consumer proves the need. It is not a reason to fold a whole-application capability refactor into the pointer-selection or group-move request.

## Proposed Selection State

A focused manage-only owner should hold:

- selected ids
- primary id
- range-anchor id
- replace, toggle, visible-range, clear, and prune behavior
- stable selected-id projection in current visible tree order

`selectedDocument.selectedDocId` continues to identify the document rendered by the route. It is not repurposed as the selection store.

```text
index interaction
  -> focused selection owner updates local state
  -> row projection updates visible selection
  -> action resolver receives active, primary, and selected ids
  -> a committed action invokes its existing workflow owner
```

The interaction controller recognizes clicks, modifiers, context-menu targeting, empty-space clearing, and Escape. It delegates all selection transitions. The shared sidebar may accept a narrow post-render projection callback but does not own manage-only selection state.

## Group Move Boundary

Group drag/drop is a later complete delivery:

1. normalize and de-duplicate selected ids
2. reduce selected descendants beneath selected ancestors to effective move roots
3. reject a destination inside any moved subtree
4. validate every requested change before writing
5. apply one mutation plan
6. rebuild docs and search once
7. reload the index while keeping the open document unchanged

The existing move path should become plural directly rather than retain parallel singular and plural contracts. A one-item selection continues through the plural path.

Browser and service normalization must express the same domain rule, but server validation remains authoritative for writes.

## Ownership Map

| responsibility | owner |
| --- | --- |
| action targeting and cardinality | current `docs-viewer-action-definitions.js` |
| selection state and row projection | proposed focused manage-only selection module |
| DOM event recognition | current management interactions owner |
| effective move roots and destination checks | drag/drop domain helper |
| workflow, busy state, reload, and results | management action controller |
| transport | management client |
| validated source writes and coordinated rebuild | source mutation service |

## Extension Method

New consumers reference the existing action id and declare a complete target/cardinality rule. They keep their own normalization, confirmation, workflow, service, and result behavior.

Do not broaden an action to `all` merely because selection exists. Each multi-document consumer is a separate roadmap outcome when its complete behavior is known.

## Known Weak Spots

- The shared Info panel currently follows the active document; showing primary-selection information needs a narrow manage-mode handoff.
- Modifier-click event ordering can accidentally trigger normal link navigation.
- Re-rendering the full sidebar for local selection would make a simple interaction unnecessarily expensive.
- Parent-plus-descendant moves can flatten a subtree if effective roots are not normalized consistently.
- Duplicate targeting rules across toolbar, Actions-menu, and context-menu renderers would make identical actions disagree.

The [Docs Viewer Delivery Roadmap](/docs/?scope=studio&doc=docs-viewer-delivery-roadmap) owns delivery order. This proposed architecture is not an implementation checklist.

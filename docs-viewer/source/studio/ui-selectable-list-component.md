---
doc_id: ui-selectable-list-component
title: Selectable List Component
added_date: 2026-06-27
last_updated: 2026-06-27
parent_id: ui
---
# Selectable List Component

The selectable list component is a shared browser UI primitive for displaying a caller-provided list of records and reporting the selected records back to the owning route.

It is not document-specific. It must be able to render any normalized item set, including documents, tags, staged files, returned-package preview rows, or future adapter records.

## Files

- `shared/frontend/js/selectable-list.js`
- `shared/frontend/css/selectable-list.css`

Planned production consumers:

- `analytics-app/app/frontend/js/data-sharing-prepare.js`
- `analytics-app/app/frontend/js/data-sharing-review.js`

## Purpose

Use this component when a route needs a selectable list with consistent row rendering, selected-count behavior, keyboard/mouse selection, and selection callbacks.

The component owns the list interaction. The route owns the data workflow.

For hierarchical record sets, such as documents with parent/child relationships, the component owns generic tree behavior once the route supplies parent ids. That includes tree ordering, indentation, collapse/expand state, descendant cascade selection, and parent indeterminate checkbox state. The route should supply the data shape; it should not duplicate tree traversal or collapse state.

## Ownership Boundary

The owning route is responsible for:

- loading data from APIs or generated files
- resolving app, data domain, scope, profile, or adapter state
- handling request/loading errors
- deciding which records are visible to the component
- transforming domain records into the component item contract
- storing the selected ids or selected records in page state
- deciding which route actions are enabled from the selection

The component is responsible for:

- rendering rows from normalized item data
- maintaining focus and row interaction state
- applying current selected ids to the DOM
- supporting single-select or multi-select mode
- select all and clear selection behavior when enabled
- reporting selection changes through callbacks
- rendering empty, filtered-empty, and constructing-list states
- optional generic tree ordering, indentation, collapse/expand, descendant cascade selection, and parent indeterminate state

The component must not fetch data, inspect adapter config, know about Docs Viewer scope, parse staged files, call prepare/review/apply endpoints, or derive domain-specific labels.

## Loading States

Data-loading state stays outside the component.

The route should show route-level loading or error state while it is fetching or resolving data, such as "Loading documents", "Loading staged files", or "Data Sharing API unavailable".

The component may show only list-construction states after the route has supplied data, such as:

- empty list
- no rows match the current filter
- constructing list
- rendering rows

This keeps API/network state separate from DOM construction state.

## Item Contract

Routes should pass normalized items. The component should not require a fixed domain schema.

Minimum item shape:

```js
{
  id: "stable-id",
  label: "Visible row label"
}
```

Recommended item shape:

```js
{
  id: "stable-id",
  label: "Visible row label",
  parentId: "optional-parent-id",
  meta: ["secondary", "values"],
  searchText: "combined searchable text",
  disabled: false,
  data: { /* original domain record or normalized payload */ }
}
```

Rules:

- `id` must be stable within the current item set.
- `label` is the primary visible row text.
- `parentId` is optional and enables generic tree rendering when `tree` is true.
- `meta` is optional supporting display text.
- `searchText` is optional text for filtering if the component owns filtering.
- `disabled` prevents selection of that row.
- `data` is opaque to the component and is returned unchanged in callbacks when requested.

If a route cannot naturally produce this shape, it should provide accessor functions instead of forcing the source data to mutate.

## Component API

The implementation should support either normalized item fields or accessors:

```js
const list = createSelectableList(rootNode, {
  id: "dataSharingPrepareDocuments",
  items,
  selectedIds,
  selectionMode: "multiple",
  tree: false,
  cascadeSelection: false,
  getId,
  getLabel,
  getMeta,
  getSearchText,
  getParentId,
  isDisabled,
  selectAllButton,
  clearButton,
  emptyMessage,
  filteredEmptyMessage,
  constructingMessage,
  onSelectionChange
});
```

`onSelectionChange` receives the current selected ids and selected items:

```js
onSelectionChange({
  selectedIds,
  selectedItems
});
```

Generic extension hooks:

- `tree` enables component-owned hierarchy behavior.
- `getParentId` or `item.parentId` supplies the parent relationship for tree mode.
- `cascadeSelection` makes a selected parent select or clear all current descendant rows in multi-select mode.
- `selectAllButton` and `clearButton` let the component own existing external toolbar buttons without owning the whole route toolbar.

Advanced extension hooks are allowed only when a route has a generic UI need the component does not yet cover:

- `getIndent` can provide row indentation for non-tree lists.
- `renderLeading` can provide a leading route-owned marker or control.
- `resolveSelectionChange` can transform a row toggle into a custom selected-id set.
- `getSelectAllIds` can define what "select all" means when the default enabled item set is not right.

The component should also expose update methods so routes can reuse an instance after data or selection changes:

```js
list.update({ items, selectedIds, disabled });
list.destroy();
```

## Selection Model

The default `selectionMode` is `multiple`.

Selection rules:

- selecting a row toggles that row in multi-select mode
- selecting a row replaces the current selection in single-select mode
- disabled rows cannot be selected
- select all selects every enabled row in the current item set
- clear removes every selected id
- in tree mode, collapsed descendants remain part of the current item set and are included by select all
- in tree mode with `cascadeSelection`, selecting or clearing a parent applies to its descendants
- in tree mode, a parent checkbox becomes indeterminate when any descendant is selected and the parent is not selected
- callbacks fire only after selection state changes

The component returns selected ids as the canonical state. Routes may derive selected records from the returned selected items when convenient.

## Filtering

Filtering can be owned by the component only when the route passes `searchText` or `getSearchText`.

Domain-specific filtering stays in the route. For example, Docs Viewer scope filtering, profile filtering, staged-file validity filtering, and tag-domain filtering are route or workflow responsibilities.

## Accessibility

The component should render a real list or listbox structure with stable focus behavior.

Required behavior:

- rows are keyboard reachable
- focus remains inside the list after selection changes
- selected state is exposed through ARIA or native control state
- disabled rows are exposed as disabled
- selection count is announced or made available to the route summary

The component should not rely on presentation classes for behavior. Use stable ids or component-owned `data-*` hooks.

## Styling Contract

Shared styles live in `shared/frontend/css/selectable-list.css`.
Route adapters should avoid route-specific styling for component-owned row, selected, disabled, empty, and constructing states.

Current planned shared classes:

- `sharedSelectableList`
- `sharedSelectableList__status`
- `sharedSelectableList__rows`
- `sharedSelectableList__row`
- `sharedSelectableList__leading`
- `sharedSelectableList__toggle`
- `sharedSelectableList__toggleSpacer`
- `sharedSelectableList__label`
- `sharedSelectableList__checkbox`
- `sharedSelectableList__title`
- `sharedSelectableList__meta`
- `sharedSelectableList__empty`

Component-owned state should be expressed through stable attributes:

- `data-selection-mode`
- `data-selected`
- `data-disabled`
- `data-state`

Routes may wrap the component in route-owned layout containers, but should not restyle component internals except through documented CSS custom properties or layout constraints on the root node.

The component should use shared CSS variables with local fallbacks for spacing, border, focus, selected-row background, disabled text, and small/meta text. It must not depend on Analytics-only, Studio-only, Docs Viewer-only, or route-local class names.

Supported custom properties include:

- `--shared-selectable-list-width`
- `--shared-selectable-list-gap`
- `--shared-selectable-list-label-gap`
- `--shared-selectable-list-indent`
- `--shared-selectable-list-toggle-size`
- `--shared-selectable-list-checkbox-size`
- `--shared-selectable-list-row-padding-y`
- `--shared-selectable-list-font`
- `--shared-selectable-list-small-font`
- `--shared-selectable-list-accent`
- `--shared-selectable-list-muted`
- `--shared-selectable-list-disabled`

## Verification

Focused checks should cover:

- empty state rendering
- constructing-list state rendering
- row label rendering
- optional meta rendering
- disabled row rendering
- click selection
- keyboard focus and selection
- single-select replacement behavior
- multi-select toggle behavior
- select all selects enabled rows in the current item set
- clear removes all selected rows
- tree mode orders rows by parent/child relationships from the supplied item set
- tree mode expands and collapses branches without losing selected ids
- tree mode reports indeterminate parent checkbox state from selected descendants
- cascade selection selects and clears descendants when enabled
- callbacks include `selectedIds` and `selectedItems`
- update lifecycle replaces items without stale selection leakage
- destroy lifecycle removes listeners

## Prepare Usage

The Data Sharing Prepare route should keep ownership of:

- adapter registry loading
- app/domain/profile/scope selection
- selectable-records API calls
- route-level loading and unavailable states
- package preparation payload construction

Prepare should pass normalized selectable records to the component and store the returned selected ids in prepare page state.

Prepare should not own document tree traversal, branch collapse state, descendant selection logic, or parent indeterminate checkbox state. Those are reusable list behaviors once Prepare supplies `id`, `label`, and `parentId`.

## Review Usage

The Data Sharing Review route should keep ownership of:

- staged-file listing
- export metadata resolution
- selected staged file state
- review API calls
- preview result rows
- apply-action enablement

Review can reuse the component for any selectable result rows or future staged-record lists once the route has normalized them into the item contract.

## Non-goals

The component is not:

- a data loader
- a Data Sharing workflow owner
- a documents selector
- a tags selector
- a staged-file parser
- a modal system
- a table/grid replacement

If a route needs domain-specific columns, editing controls, or row actions beyond generic selection/tree behavior, define those outside this component or add a separate component spec.

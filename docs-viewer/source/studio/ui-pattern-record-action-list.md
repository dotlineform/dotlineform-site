---
doc_id: ui-pattern-record-action-list
title: Record List And Action Layer Working Spec
added_date: 2026-06-14
last_updated: 2026-06-14
parent_id: ui
viewable: true
---
# Record List And Action Layer Working Spec

This is a working spec for a shared list component that renders compact records with columns and optional selection state.
External actions and route-specific workflows should be layered on top of that base component.

The first proving use cases are the Catalogue Work editor downloads and links sections.
Both now use the shared record list with a route-owned action layer.

## Current Position

Implemented pieces:

- `shared/frontend/js/record-list.js`
- `shared/frontend/css/record-list.css`
- `createRecordList(...)`
- `createRecordListActions(...)`
- Catalogue Work editor downloads list integration
- Catalogue Work editor links list integration
- focused smoke coverage for the shared component and Work editor embedded-record actions

The current production use is intentionally narrow:

- downloads and links render through the shared `RecordList`
- rows have column headers
- one row can be selected
- selected-row state uses an outline by default, not a persistent fill
- `Edit` and `Delete` live in an external `RecordListActions` toolbar
- actions are disabled until a row is selected
- action callbacks include `action`, `actionKey`, `selection`, and `records`
- Edit opens the existing embedded entry modal
- Delete opens the existing embedded delete confirmation
- link URLs render as safe external-link cells, while link labels remain plain text

Selection clearing is boundary-based, not a delayed blur workaround.
For lists that set `clearSelectionOnBlur`, the list clears selection when a pointer or focus event lands outside the list and any registered action boundary.
`RecordListActions` registers its toolbar as a focus boundary, so clicking an action button does not clear the selected row before the callback reads it.

Delete confirmations should make Cancel the default action.
The Studio modal primitive now supports `defaultAction: "cancel"` for this purpose.
For destructive confirmations, Cancel should receive initial focus and the visual default-action style; Delete should require an explicit click, tab, or keyboard move.

## Framing

The base record list component should sit between the List Primitive and route-specific adapters.

It is not just CSS classes.
It should own enough behavior that consumers do not have to reimplement row selection, truncation, accessible selection wiring, empty states, and refresh mechanics.

It is also not a full route workflow.
The list can own which row is selected.
A generic action layer can own whether action buttons are currently available.
The adapter should own what those actions mean: opening a modal, applying a delete, updating draft state, and reporting status.

Do not repeat `Edit` and `Delete` buttons on every row for the downloads/links use case.
The v1 direction is selectable rows plus an action area outside the list.

This does not prohibit compact row-owned affordances.
The Analytics Tag Registry page is the model for a successful exception: the tag pill is both data display and control surface.
Its label identifies the row, its color communicates tag group, the pill body can act as the edit/select affordance, and the compact `x` can remove the row.
That is functionally similar to repeated edit/delete controls, but it is information-dense instead of four separate repeated cells/buttons.

## Relationship To Existing Pieces

Existing pieces:

- `ui-primitive-list`: visual and structural guidance for repeated row surfaces
- `file-picker` listbox: selectable ARIA listbox with keyboard movement and selected state
- `search-list`: popup option list with transient input and commit behavior

Record List is a different component:

- it renders persistent records on the page
- rows may contain multiple columns
- rows may contain links
- rows may be selectable

The action layer is optional:

- actions normally live outside the repeated rows
- action buttons can be disabled from selection state
- action events return structured payloads to the adapter
- compact row-owned controls are allowed when the control itself carries row data

## Architecture Layers

The implementation should split into three layers:

- `RecordList`: base shared component for records, columns, headers, truncation, links, empty state, selection, keyboard behavior, and test hooks
- `RecordListActions`: optional generic action layer for external buttons such as `View`, `Edit`, and `Delete`
- route adapter: workflow glue for route data, modals, confirmations, draft state, server calls, and status messages

Downloads may only need the first two layers if existing Work editor functions can handle add/edit/delete/view behavior cleanly.
A route adapter is still useful when workflow wiring starts to spread across the page.

## Implemented V1 Scope

The first production component supports the smallest useful subset for embedded Work editor records.

The base component currently supports:

- compact list shell
- empty state
- optional header row, enabled by default unless disabled by the caller
- fixed column definitions
- route-provided records
- text cells
- link cells
- single-row selection
- full-value hover text for truncated cells
- stable row re-render after records change
- `onSelectionChange({ selection, records })` callback
- `selection()` lookup method
- `subscribeSelectionChange(...)`
- `addFocusBoundary(...)` for adjacent controls that belong to the same interaction boundary
- `clearSelectionOnBlur` for transient action selection
- `selectedBackground` override, with transparent/no-fill selection as the default

The optional action layer currently supports:

- external action definitions
- disabled action state based on the current selection
- action click and keyboard event delegation
- custom disabled logic through `disabled(selection, records)`
- action title text through `title(selection, records)`
- `onAction({ action, actionKey, selection, records })` callback
- automatic refresh when list selection changes
- action toolbar registration as a list focus boundary

Do not include sorting, drag reorder, thumbnails, or async loading in the first version.
Those should be added only when a real consumer needs them.

Do not include multi-select in v1.
However, the base list should not paint itself into a corner: a leading checkbox selection mode should be a plausible v2 extension.

Do not include compact row-object actions in the first downloads/links implementation unless they are needed to avoid a worse interaction.
Start with selected row plus external actions, then promote compact row-object affordances when a consumer proves the shape.

Do not include in-row cell editing in v1.
For downloads, the label column is the obvious future candidate, but adding inline editing changes the component contract from an action list into a small editable grid.
The first implementation should keep label editing behind the existing `Edit` action while making the list structure ready for a narrower v2 inline-edit feature.

## Base Component Responsibilities

The shared base component should own:

- row/list DOM structure
- list and row ARIA where applicable
- consistent row density and alignment
- column layout
- truncation and tooltip/title behavior
- link cell markup and safe link attributes
- external-link attributes for link cells by default
- empty-state rendering
- selected-row state and selected-row styling
- row click and keyboard selection behavior
- predictable row-level `data-*` hooks for smoke tests
- refresh/update method

The component should not require consumers to decide how to ellipsize cells or where to put `title` attributes.
If a cell can truncate, the component should preserve the full text for hover and accessible name where practical.

## Action Layer Responsibilities

The optional action layer should own:

- external action button rendering, if the toolbar root is provided
- disabled action state based on the current selection
- action click and keyboard event delegation from the action area
- action payload shape
- action refresh when records or selection change

## Adapter Responsibilities

The adapter should own:

- mapping route records into list rows
- choosing columns
- choosing action labels
- deciding whether an action is enabled
- choosing whether the first version uses click-to-select rows or a visible radio/selection marker
- choosing whether a later adapter uses a compact row-object control instead of external actions
- opening route modals
- routing delete actions through a confirmation modal
- applying edits/deletes to route draft state
- save/dirty-state behavior
- route status messages
- server calls, if any

For the Work editor downloads and links action wiring, this currently means:

- records: `state.draft.downloads` or `state.draft.links`
- visible headers: yes
- columns: filename and label for downloads; plain label and linked URL for links
- selection: one selected row
- actions outside the list: `Edit`, `Delete`
- `Edit`: opens the existing embedded-entry modal for the selected record
- `Delete`: opens a confirmation modal with Cancel as the default action, then applies the existing delete flow for the selected record
- after action: adapter re-renders the list with the updated draft records

## Current API Shape

Base list API:

```js
const list = createRecordList(rootNode, {
  id: "catalogueWorkDownloads",
  emptyText: "No downloads.",
  selectionMode: "single",
  clearSelectionOnBlur: true,
  columns: [
    { key: "filename", label: "filename", truncate: true },
    { key: "label", label: "label", truncate: true }
  ],
  records,
  getRecordId: (_record, index) => `download-${index}`,
  onSelectionChange({ selection, records }) {
    // Adapter may update adjacent state if needed.
  }
});

list.update({ records });
list.destroy();
```

Optional action layer API:

```js
const actions = createRecordListActions(document.getElementById("catalogueWorkDownloadsActions"), {
  list,
  actions: [
    { key: "edit", label: "Edit", requiresSelection: true },
    { key: "delete", label: "Delete", tone: "danger", requiresSelection: true }
  ],
  onAction({ action, actionKey, selection, records }) {
    // Adapter opens modal or applies delete for selected record(s).
  }
});

actions.update();
actions.destroy();
```

Column options currently include:

- `key`: record key to read
- `label`: accessible/header label
- `type`: `text` or `link`
- `hrefKey`: optional href source for link cells
- `truncate`: whether to apply single-line truncation with full text available on hover
- `className`: optional adapter-owned cell class

Link cells should use safe external-link attributes by default.
An adapter can opt out only when the link is known to be internal and should behave like normal in-app navigation.

Action options currently include:

- `key`
- `label`
- `tone`
- `requiresSelection`: defaults to true; set false for actions such as `Add`
- `disabled(selection, records)`
- `title(selection, records)`

Actions that require a selected row should be disabled until a row is selected.
Do not use a "select a row" status message for the normal unselected state.

The action layer should subscribe to the list selection state and refresh disabled buttons automatically.
Action callbacks should include both the full action definition and the stable `actionKey` string:

```js
onAction({ action, actionKey, selection, records }) {}
```

Selection options currently include:

- `selectionMode`: `single` in v1
- `initialSelection`: optional selected index or record id
- `getRecordId(record, index)`: optional stable id for preserving selection across updates
- `clearSelectionOnBlur`: optional focus-like selection behavior for lists where selection is not persistent state
- `selectedBackground`: optional selected-row background override; default selected state should use a border/outline without a fill

Single selection should be row-click only in v1.
Do not add visible radio controls unless a later workflow proves they are needed.

Checkbox multi-select is a v2 extension.
It should be added when there is a real bulk action use case, such as multi-delete or multi-edit in the Series editor or a details list.

## Downloads/Links Use Case

Downloads are the first implementation because they need:

- compact rows
- columns
- one selected row
- edit/delete actions outside the list
- re-render after action
- clear empty state

The current downloads implementation does not need:

- sorting
- thumbnails
- in-row editing
- multi-select
- virtual scrolling
- server-side loading

That makes them a useful boundary test for the component.
If the component cannot improve downloads without route-specific markup leaking everywhere, the component boundary is wrong.

Links now use the same base list/action layer.
Their adapter keeps the label as plain text and renders the URL column as the safe external link.

## Design Notes

Rows should be denser than the current Work editor embedded item cards.
The simple list pattern from the UI Catalogue is the visual baseline, but production code should not copy demo classes.

Downloads and links should show column headers in v1.
The label often correctly matches the filename or URL, and without headers two repeated values look like accidental duplication.
Headers make the distinction between display label and target/path explicit.

Cells should not wrap by default.
Long URLs, filenames, and labels should truncate cleanly inside their column.
Full values should remain inspectable through hover text.

Action buttons should be predictable and consistently placed outside the repeated rows.
For downloads/links, the action layer should render or control an action area adjacent to the list, and those actions should operate on the current selection.
This avoids repeated `Edit` and `Delete` controls on every row.

Repeated controls are acceptable when they are also meaningful row content.
The Tag Registry pill is the reference case:

- label communicates the tag value
- color communicates tag group
- body affordance can select or edit the tag
- compact `x` affordance can delete/remove the tag

The success criterion for this component family is that a future `/analytics/tag-registry/` implementation can be reduced to a route adapter over the same list/component model, without custom row mechanics scattered through the page.

## Later Adapter Target: Tag Registry

The Analytics Tag Registry page is a larger target than downloads/links.
It includes:

- group filters
- inline search
- sortable columns
- compact row-owned tag controls
- paragraph-length description editing

This should not expand the first downloads/links implementation.
It does mean the component family should be designed so filtering, searching, sorting, and compact row-object controls can be added without replacing the core row/list model.

For Tag Registry, paragraph editing can remain modal-based.
That is a reasonable exception to the inline-editing goal because the edited value is long prose, not a short label.

## V2 Inline Editing Candidate

Inline editing may be useful for a narrow case such as the downloads `label` column.
Opening a modal to edit a single text value is heavier than the task deserves, so this should remain a candidate once the basic list/action component is stable.

The v2 shape should be deliberately small:

- add one column type such as `editableText`
- support one editable text cell per row initially
- expose `onCellEdit({ key, value, previousValue, record, index })`
- let the adapter validate, update draft state, and report dirty state
- keep `Edit` available for full-record editing when more than the label needs changing

Inline editing should not be added as a general grid system unless a real workflow requires it.
Before adding it, define:

- click/focus behavior for entering edit mode
- Enter commit behavior
- Escape cancel behavior
- blur behavior
- validation failure display
- keyboard traversal between the editable cell, row selection, and the external action toolbar
- how truncation changes when a cell enters edit mode

The component should not make route draft changes directly.
It should emit the proposed edit, then re-render from adapter-provided records after the adapter accepts the change.

## V2 Compact Row-Object Controls

Compact row-object controls need a separate API shape from generic row actions.
The design question is what row-control data the adapter provides and what event payload the component returns.

For a Tag Registry-style pill, the adapter would likely provide:

- display label
- group/type key
- group/type visual tone
- primary action key, such as `edit`
- optional remove action key, such as `delete`
- stable row id

The component would return callbacks with:

- action key
- row id
- record
- row index
- source affordance, such as `body` or `remove`

This keeps compact controls explicit without encouraging generic repeated `Edit`/`Delete` buttons in every row.

Support one compact row-object control per row.
Current use cases do not need more, and needing multiple compact controls in a row probably means the problem should be split into clearer rows, columns, or adapters.

## Open Questions

No open questions for v1.

## Verification Target

Current focused coverage should prove:

- empty state renders
- text and link columns render
- long cell values truncate without layout expansion
- full cell values are available through hover/title text
- row selection updates selected state
- external action buttons are generated by the action layer or controlled by list selection state
- `Edit` and `Delete` callbacks include action key, selection, and selected record(s)
- action toolbar focus/clicks do not clear selection before the action callback
- selection clears when focus or pointer moves outside the list/action boundary where `clearSelectionOnBlur` is enabled
- adapter re-renders the list after records change
- delete confirmations make Cancel the default focus and visual action

Potential v2 inline-edit coverage:

- editable text cell enters edit mode
- Enter emits `onCellEdit`
- Escape restores the previous value
- rejected edits leave the visible value unchanged
- accepted edits re-render from adapter state

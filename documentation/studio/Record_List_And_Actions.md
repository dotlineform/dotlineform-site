---
draft: false
doc_id: d-20260614-201632-79c9cb
title: Record List And Actions
added_date: 2026-06-14 20:16:32
last_updated: "2026-10-25"
parent_id: d-20260505-181739-bb5223

---
# Record List And Actions

Use `RecordList` for a compact row list with fixed columns and optional single-row selection. Use `RecordListActions` when buttons outside the list act on its current selection.

## Authority

- behaviour: `shared/frontend/js/record-list.js`
- styles: `shared/frontend/css/record-list.css`
- focused tests: search `tests/` for `record-list`

Current consumers are in the Catalogue Work and Series adapters. Find the exact set by searching for imports from `/shared/frontend/js/record-list.js`.

## Stable Structure

`createRecordList(root, options)` receives route-normalized records and column definitions. It owns:

- header, row, cell, empty, link, image and opt-in icon rendering
- safe URL handling for link and image cells
- optional single-row selection
- pointer and keyboard selection
- focus boundaries and optional clear-on-blur behaviour
- selection events and update/destroy lifecycle

`createRecordListActions(root, options)` receives a list controller and action definitions. It owns button rendering, selection-dependent disabled state, action events, and registration of the toolbar as a focus boundary.

The route owns:

- mapping domain records into rows and columns
- deciding which actions exist and when they are available
- modals, confirmation, validation, mutations, dirty state, saves, and server calls
- re-rendering from canonical route state after an action

The component never mutates a route record.

Columns that consume supplied text can define `formatText(value, {record, index, column})`; its result must be a string and supplies visible text and the default tooltip. Initial rendering and `updateCells` use the same formatter. The Work member Title/Gallery columns and resource Label column use literal text, without the component's default trimming/dash display convention. Optional absence is the owning column's decision; malformed formatter results fail. Link/image URL handling retains safety checks and requires string or absent targets, preserving accepted supplied URL strings rather than trimming them. This local shared component is outside the public code-projection inventory.

Text/link columns can supply `tooltipKey` to select caller-prepared native hover text independently of their visible value. The shared renderer assigns that plain text through the DOM `title` property, retaining line breaks without HTML interpolation. Initial rendering and text-cell updates use the same tooltip resolver; link controls receive the same text as their cell. Without an explicit tooltip value owner, truncated cells and links retain their visible-text tooltips. The Work Series adapter uses this option for its title, Year and Year display tooltip; domain formatting and saved-value selection remain in that adapter.

Icon rendering is opt-in. An icon column supplies `type: "icon"` and `iconClass` as a class string or record callback; the column value supplies its accessible type label. An action's `iconClass` creates decorative artwork and requires `ariaLabel` on the button. The caller owns the artwork classes and CSS, including asset location, tint and size. Text-only `updateCells` does not update icon columns. The Works editor resource list uses these options; existing text and image consumers retain their rendering.

## Extension Boundary

Add a shared column type or interaction only when more than one domain can use the same behaviour. Keep domain filtering, row ordering, edit forms, destructive previews, and save logic in route adapters.

For exact option names, callback payloads, supported cell types, and controller methods, read the exported factory functions. Copying that inventory into this page makes it drift without improving discovery.

## Method And Weak Spots

- Selection is deliberately single-row. Use [Selectable List](Selectable_List.md) for multi-selection or tree selection.
- The action toolbar is separate so list focus and workflow actions can evolve independently, but adapters must keep the toolbar and list lifecycle synchronized.
- Column definitions are flexible but untyped. A bad accessor or width is found at runtime.
- Record/action lists are display-and-command primitives, not inline editors. Add route-owned editing first; only generalize it after a second real use appears.

## Verification

Protect the durable boundaries:

- safe text, link, and image rendering
- empty and header modes
- click and keyboard selection
- selection event and action payloads
- disabled actions before selection
- focus-boundary behaviour
- update and destroy cleanup

Consumer tests should cover record mapping and resulting mutations. Visual fit, toolbar placement, and modal flow remain route-level manual checks.

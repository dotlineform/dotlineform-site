---
doc_id: ui-primitive-list
title: "List Primitive"
added_date: 2026-05-05
last_updated: "2026-05-05"
parent_id: ui-catalogue
sort_order: 30
---
# List Primitive

This doc is the durable implementation contract for shared list surfaces.

Live reference:

- [List primitive page](/studio/ui-catalogue/list/)

## Scope

The list primitive covers repeated row surfaces such as:

- simple lists
- sortable lists
- thumbnail lists
- selectable review lists

The primitive owns the outer list shell and common row rhythm.
Page-specific classes still own data-specific column templates, row actions, responsive labels, and feature-specific cells.

## Contract

The list primitive should:

- fill the available width by default
- allow explicit width constraints through `--studio-list-width`
- keep one stable row rhythm for related list types
- center one-line rows and top-align multiline rows
- keep sortable headers reachable when sorting is available
- expose stable hooks for JS behavior instead of relying on presentational selectors

## Direction

The list primitive currently defines three baseline versions:

- simple list: minimal row treatment, no column headers, suitable for short lists where the surrounding page already explains the row context
- sortable list: column headers become clickable buttons on sortable columns and show the active sort direction beside the label
- thumbnail list: the first column is a fixed media thumbnail; sorting may still exist, but it can be controlled by buttons or other controls outside the list

The shared `tagStudioList` layer owns the optional width wrapper, row rhythm, header treatment, row-alignment modifiers, common cell text, cell links, sort indicator, and thumbnail frame.
Page-specific classes still own column templates, row actions, chips, and responsive data labels.

## Implementation Notes

Current implementation lives in:

- `assets/studio/css/studio.css`

Primary classes:

- `tagStudioList`
- `tagStudioList__head`
- `tagStudioList__headLabel`
- `tagStudioList__sortBtn`
- `tagStudioList__sortIndicator`
- `tagStudioList__rows`
- `tagStudioList__row`
- `tagStudioList__row--center`
- `tagStudioList__row--start`
- `tagStudioList__cell`
- `tagStudioList__cellTitle`
- `tagStudioList__cellMeta`
- `tagStudioList__cellLink`
- `tagStudioList__thumb`

## Lifecycle Notes

List state should make the current data context clear:

- selection summaries should update from actual selected rows
- select-all behavior should match the currently visible list unless explicitly documented otherwise
- search controls should appear only when useful for the list size or workflow
- route-local result actions should not be embedded in rows unless the row itself is the result target

Stable list rules from [Studio UI Rules And Decision Log](/docs/?scope=studio&doc=studio-ui-rules) should move here as they are retired from the log.

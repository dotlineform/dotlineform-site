---
doc_id: ui-primitive-list
title: List Primitive
added_date: 2026-05-05
last_updated: 2026-05-29
parent_id: ui-catalogue
---
# List Primitive

This doc is the durable implementation contract for shared list surfaces.

Demo reference:

- [List primitive demo](http://127.0.0.1:8768/admin/ui-catalogue/demos/primitives/list/)

## Scope

The list primitive covers repeated row surfaces such as:

- simple lists
- sortable lists
- dense scan lists
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

The list primitive currently defines four baseline versions:

- simple list: minimal row treatment, no column headers, suitable for short lists where the surrounding page already explains the row context
- sortable list: column headers become clickable buttons on sortable columns and show the active sort direction beside the label
- dense list: works-index density for scan tables, using `tagStudioList--dense`, `--text-xs` type, no row dividers, sortable columns, and a bold title cell
- thumbnail list: the first column is a fixed media thumbnail; sorting may still exist, but it can be controlled by buttons or other controls outside the list

The shared `tagStudioList` layer owns the optional width wrapper, row rhythm, header treatment, row-alignment modifiers, common cell text, cell links, sort indicator, and thumbnail frame.
Page-specific classes still own column templates, row actions, chips, and responsive data labels.

## Implementation Notes

Current live implementation lives in:

- `assets/studio/css/studio.css`

Current demo implementation lives in:

- `admin-app/ui-catalogue/assets/css/ui-catalogue-demo.css`
- `admin-app/ui-catalogue/source/demos/primitives/list/index.md`

Primary classes:

- `tagStudioList`
- `tagStudioList--dense`
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

Dense list guidance:

- add `tagStudioList--dense` to the `tagStudioList` wrapper
- keep sortable columns as real `tagStudioList__sortBtn` buttons
- use page-specific header and row classes for the column template
- use `tagStudioList__cellTitle` on the title cell so the shared bold rule applies
- do not add row dividers back locally unless the page needs a different list variant

The UI Catalogue demo uses `uiCatalogueDemo*` classes. Use demo markup as the structural reference, then map it into the live list shell or a route-owned production variant.

## Lifecycle Notes

List state should make the current data context clear:

- selection summaries should update from actual selected rows
- select-all behavior should match the currently visible list unless explicitly documented otherwise
- search controls should appear only when useful for the list size or workflow
- route-local result actions should not be embedded in rows unless the row itself is the result target

Stable list rules belong here when they need to become permanent reference guidance.

### Primitive Scope

1. The list primitive covers repeated row collections where the user scans, compares, opens, or reviews records.
2. The shared layer owns the optional width wrapper, outer header, row reset, spacing, dividers, row alignment modifiers, sortable header-button treatment, common text cells, link treatment, and thumbnail geometry.
3. Page-specific classes still own grid columns, cell semantics, row actions, chips, links, and data-specific responsive behavior.
4. Do not use this primitive for free-form cards, dashboards, or grouped prose sections. Those belong to panels, panel links, or page-specific composition.

### Current Baseline

1. Use `tagStudioList` as the optional width wrapper. Without `--studio-list-width`, the list fills the available width.
2. Use `tagStudioList__rows` plus `tagStudioList__row` for every list version.
3. Use `tagStudioList__row--center` when every row cell is expected to stay one line.
4. Use `tagStudioList__row--start` when any cell may contain multiple lines, so secondary lines align consistently beneath the first line.
5. Use `tagStudioList__head` only when column labels improve scanning or when the list owns sortable columns.
6. Use `tagStudioList__headLabel` for static column labels.
7. Use `tagStudioList__sortBtn` for sortable header cells, and place the visible sort direction inside `tagStudioList__sortIndicator`.
8. Use `tagStudioList__cell`, `tagStudioList__cellTitle`, and `tagStudioList__cellMeta` for common stacked cell content before adding page-local text wrappers.
9. Use `tagStudioList__cellLink` when a cell value links to another page or opens a modal.
10. Use `tagStudioList__thumb` and `tagStudioList__thumbImage` for the first media column in thumbnail rows.

### Versions

1. Simple lists omit column headers. Use them for short collections where the surrounding page already explains the row meaning, such as small file lists.
2. Sortable lists use clickable column headers for sortable columns. The active header should show direction and expose active state through button state attributes.
3. Thumbnail lists reserve the first column for a fixed-size thumbnail. They may still be sorted, but sorting can be driven by nearby buttons or segmented controls outside the list rather than by the headers.

### Width And Columns

1. Lists fill the available width by default.
2. Constrain a list by setting `--studio-list-width` on the `tagStudioList` wrapper. The value can be an absolute measure such as `34rem` or a percentage such as `72%`.
3. The wrapper always keeps `max-width: 100%`, so constrained lists cannot overflow their parent.
4. Column widths belong to the paired page/demo header and row classes through `grid-template-columns`.
5. Size columns for the actual data. Short two- and three-column lists should not stretch wide just because the parent has room.
6. Keep header and row column templates paired so labels and row cells stay aligned.

### Type And Links

1. Studio UI primitives use the small type scale by default. In CSS this is `--font-small`, which maps to `--text-sm`.
2. Normal page prose outside primitives should continue to use `--font-body`, which maps to `--text-md`.
3. Any row item may be a link to another page or a button that opens a modal.
4. Do not make the whole row clickable by default. Use explicit links or buttons in the relevant cells unless a separate row-link variation has been defined.

### Sorting Guidance

1. If clicking a header changes order, render that header as a real button, not a static label with a click handler.
2. Static labels and sortable buttons can appear in the same header row when only some columns are sortable.
3. The sort arrow is a state indicator, not decorative page copy. Keep it adjacent to the active sort label.
4. If sorting is controlled outside the list, keep headers static and put the controls before the list so the interaction order is clear.

### Thumbnail Guidance

1. Thumbnails should use stable dimensions so image loading cannot shift the row.
2. Use empty `alt` text when the adjacent row title already identifies the item and the thumbnail is supporting context.
3. Missing media should preserve the same frame size with a neutral placeholder or page-specific fallback state.
4. Keep thumbnail rows aligned to the center of the media column when text stays one-line or compact. Use top alignment when the row is metadata-heavy.

### Current Mapping Notes

1. `catalogue-status`, `series-tags`, docs broken links, and activity reports already use the shared list shell with page-specific columns.
2. Work-detail and related-record rows currently use their own list-like composition; thumbnail behavior from this primitive can guide a later convergence pass.
3. Existing live routes still contain local row classes for their data model. This primitive does not require moving those classes into the shared layer unless the visual behavior repeats.

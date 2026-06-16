---
doc_id: ui-pattern-record-action-list
title: Record List And Action Layer Implementation Note
added_date: 2026-06-14
last_updated: 2026-06-15
parent_id: ui
viewable: true
---
# Record List And Action Layer Implementation Note

`RecordList` is a shared frontend component for compact persistent record lists.
It renders route-provided records as rows with fixed columns, optional links, and optional single-row selection.

`RecordListActions` is the companion action toolbar.
It renders external buttons that operate on the list selection or on the list as a whole.
Route adapters own the actual workflow behind each action.

## Files

- `shared/frontend/js/record-list.js`
- `shared/frontend/css/record-list.css`

Production consumer:

- `studio/app/frontend/js/catalogue-work-sections.js`
- `studio/app/frontend/js/catalogue-work-detail-browser.js`
- `studio/app/frontend/js/catalogue-work-shell.js`
- `studio/app/frontend/js/catalogue-work-editor-state.js`

## Component Boundary

`RecordList` owns:

- list, header, row, and cell DOM structure
- row and list ARIA for selectable and non-selectable lists
- column layout
- optional per-column grid widths
- text cells
- safe link cells
- single-line truncation and full-value hover text
- empty-state rendering
- single-row selection
- row click selection
- keyboard row selection and movement
- selection clearing outside the list/action boundary when configured
- stable `data-*` hooks for tests and adapters
- update and destroy lifecycle methods

`RecordListActions` owns:

- external action button rendering
- automatic refresh when list selection changes
- disabled state based on selection and adapter callbacks
- action click delegation
- action payload shape
- toolbar registration as a list focus boundary
- component-owned action appearances such as icon buttons

Route adapters own:

- mapping route records into list row objects
- choosing columns and widths
- choosing whether to show the header row
- choosing action definitions
- choosing when actions are present or disabled
- opening modals
- confirming destructive actions
- mutating draft/source state
- save, dirty-state, and server workflows
- route status and validation messages

The shared component must not mutate route data directly.
It emits selection and action events; the adapter updates state and re-renders from its canonical data.

## Base List API

```js
const list = createRecordList(rootNode, {
  id: "catalogueWorkResources",
  records,
  columns: [
    { key: "thumbnail", label: "thumbnail", width: "48px", type: "image", srcKey: "thumbSrc", srcsetKey: "thumbSrcset", sizesKey: "thumbSizes", widthKey: "thumbWidth", heightKey: "thumbHeight", altKey: "thumbAlt", fallbackTextKey: "thumbFallback", truncate: false },
    { key: "type", label: "type", width: "2rem", truncate: false },
    { key: "label", label: "label", width: "minmax(4.5rem, 0.7fr)", truncate: true },
    { key: "target", label: "file / URL", width: "minmax(9rem, 1.3fr)", type: "link", hrefKey: "targetHref", truncate: true }
  ],
  showHeader: false,
  emptyText: "",
  selectionMode: "single",
  clearSelectionOnBlur: true,
  getRecordId: (record) => `${record.kind}-${record.index}`,
  onSelectionChange({ selection, records }) {
    // Adapter-owned behavior.
  }
});

list.update({ records });
list.destroy();
```

Column options:

- `key`: record property to read
- `label`: header/accessibility label
- `width`: optional CSS grid track value; defaults to `minmax(0, 1fr)`
- `type`: omitted/`text`, `link`, or `image`
- `hrefKey`: optional record property for link hrefs
- `srcKey`: optional record property for image `src`
- `srcsetKey`: optional record property for image `srcset`
- `sizesKey`: optional record property for image `sizes`
- `altKey`: optional record property for image alt text
- `widthKey` / `heightKey`: optional record properties for image display dimensions
- `fallbackTextKey`: optional record property for image placeholder text when the image is missing or loading
- `truncate`: defaults to truncating text with hover title
- `className`: optional adapter-owned cell class

Link cells reject unsafe `javascript:` and `data:` hrefs.
Link cells use `target="_blank"` and `rel="noopener noreferrer"` unless `external: false` is supplied on the column.
Image cells reject unsafe `javascript:` and `data:` `src` and `srcset` URLs, use lazy loading by default, and expose loading, ready, and missing states for shared CSS.

Selection options:

- `selectionMode`: currently `single`
- `initialSelection`: optional row index or record id
- `getRecordId(record, index)`: stable row id provider
- `clearSelectionOnBlur`: clears selection when pointer/focus moves outside the list and registered boundaries
- `selectedBackground`: optional CSS value for selected-row background

## Action Layer API

```js
const actions = createRecordListActions(rootNode, {
  id: "catalogueWorkResourcesActions",
  list,
  actions: [
    { key: "edit", label: "✏️", ariaLabel: "Edit", appearance: "icon" },
    { key: "delete", label: "🗑️", ariaLabel: "Delete", appearance: "icon", tone: "danger" },
    { key: "new-download", label: "📄", ariaLabel: "Add file", appearance: "icon", requiresSelection: false },
    { key: "new-link", label: "🔗", ariaLabel: "Add link", appearance: "icon", requiresSelection: false }
  ],
  onAction({ action, actionKey, selection, records }) {
    // Adapter-owned behavior.
  }
});

actions.update();
actions.destroy();
```

Action options:

- `key`: stable action id
- `label`: button text/content
- `ariaLabel`: accessible button name
- `title`: static text or `title(selection, records)`
- `appearance`: optional shared visual variant, currently including `icon`
- `tone`: optional shared tone, currently used for `danger`
- `requiresSelection`: defaults to true
- `disabled(selection, records)`: optional adapter disabled callback
- `className`: optional adapter-owned button class

Actions that require selection are disabled when there is no selected row.
Actions with `requiresSelection: false` remain available unless their `disabled` callback returns true.

## Selection And Focus

Single-row selection is controlled by the list.
Clicking a row selects and focuses it.
Arrow keys move focus and selection together.
Enter and Space select the focused row.

When `clearSelectionOnBlur` is enabled, the list clears selection when pointer or focus events land outside:

- the list root
- boundaries registered through `list.addFocusBoundary(node)`

`RecordListActions` registers its toolbar as a focus boundary.
This prevents an action click from clearing selection before the action callback reads it.

## Work Editor Adapter

The Catalogue Work editor uses the shared list for the right-panel `links` section.
The section is visually part of the summary panel, below the preview/media actions, and does not have its own panel border.

The adapter presents two canonical source fields as one editor-facing list:

- `draft.downloads`
- `draft.links`

The canonical fields stay separate for source data and public rendering.
The adapter maps them into one row shape:

```js
{
  kind: "download" | "link",
  index: number,
  type: "📄" | "🔗",
  label: string,
  target: string,
  targetHref: string
}
```

Ordering:

- downloads first
- links second

Columns:

- icon-only type column, fixed at `2rem`
- label column
- linked file/URL target column

The Work editor hides the list header row.
The surrounding section label is `links`, using the normal Studio form-label style.

Download target behavior:

- new/draft records show the filename as plain text when no media URL can be constructed
- published records link to the configured media URL when runtime media config is available
- the stored source value remains the filename, not the absolute URL

Link target behavior:

- link labels are plain text
- URL targets render as safe external links

Actions:

- `Add file` opens the existing download modal without an index
- `Add link` opens the existing link modal without an index
- `Edit` opens the existing modal for the selected row's `kind` and `index`
- `Delete` opens the existing confirmation flow for the selected row's `kind` and `index`

Toolbar state:

- `Add file` and `Add link` are visible whenever the route can edit the current record
- `Edit` and `Delete` are only rendered when the list has rows
- `Edit` and `Delete` remain disabled until a row is selected
- when the last row is deleted, the adapter re-renders and removes `Edit` and `Delete`

## Work Detail Browser Adapter

The Catalogue Work editor uses the shared list for the work-detail browser that replaced the legacy grouped detail list.

The adapter renders:

- a section list from `currentLookup.detail_sections`
- a detail thumbnail list for the selected section
- a route-owned search field beside the action toolbar
- external actions for `Edit`, `Delete`, and `New`

The search field is outside `RecordList`.
The route adapter filters records before passing them to the shared list.
The current filter matches only the last three digits of `detail_id`, falling back to the suffix of `detail_uid` when needed.

Actions:

- `Edit` opens the selected detail in `/studio/catalogue-work-detail/`
- `Delete` currently opens the selected detail editor; destructive detail deletion remains owned by the dedicated detail route
- `New` opens the detail editor in new mode for the current work and is disabled until the parent work is published

## Styling Contract

Shared styles live in `shared/frontend/css/record-list.css`.
Adapters should avoid route-specific button styling for component-owned action appearances.

Current shared classes:

- `sharedRecordList`
- `sharedRecordList__header`
- `sharedRecordList__row`
- `sharedRecordList__cell`
- `sharedRecordList__imageFrame`
- `sharedRecordList__image`
- `sharedRecordList__imagePlaceholder`
- `sharedRecordList__link`
- `sharedRecordList__empty`
- `sharedRecordListActions`
- `sharedRecordListActions__button`

Icon action buttons use:

```html
<button class="sharedRecordListActions__button" data-appearance="icon">
```

The icon appearance is borderless and sized by shared CSS variables.

## Verification

Focused checks should cover:

- empty state rendering
- text cell rendering
- link cell rendering and unsafe URL rejection
- image cell rendering and unsafe `src` / `srcset` rejection
- per-column width rendering
- optional header rendering and hidden-header mode
- truncation without layout expansion
- full-value hover title for truncated cells
- click selection
- keyboard selection movement
- action disabled state before selection
- action refresh after selection changes
- list-level actions with `requiresSelection: false`
- action payload includes `action`, `actionKey`, `selection`, and `records`
- toolbar focus/click does not clear selection before callback execution
- selection clears outside list/action boundary when configured
- update and destroy lifecycle cleanup

Work editor adapter checks should cover:

- downloads and links map into one resources list
- downloads render before links
- file/link icons render in the type column
- label column is plain text
- target column renders links where hrefs exist
- `Add file` and `Add link` remain visible on an empty list
- `Edit` and `Delete` are hidden on an empty list
- deleting the last row hides `Edit` and `Delete`

## Remaining Work

Inline label editing is the main realistic next extension.
It should be added only for short text cells where modal editing is unnecessarily heavy.

Candidate shape:

- add an `editableText` column type
- support one editable text cell per row initially
- emit `onCellEdit({ key, value, previousValue, record, index })`
- let the adapter validate and update draft state
- re-render from adapter-provided records after accepted edits
- keep modal `Edit` available for full-record editing

Before implementing inline editing, define:

- how a cell enters edit mode
- Enter commit behavior
- Escape cancel behavior
- blur behavior
- validation failure display
- keyboard traversal between editable cells, row selection, and the action toolbar

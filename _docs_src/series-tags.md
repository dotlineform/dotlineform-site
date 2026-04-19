---
doc_id: series-tags
title: "Series Tags"
last_updated: 2026-03-31
parent_id: studio
sort_order: 210
---
# Series Tags

Route:

- `/studio/series-tags/`

Purpose:

- review tags assigned to series
- manage the cross-series offline assignment session, including export and local-server import

## Page / Template Structure

Primary template:

- `studio/series-tags/index.md`

Page controller:

- `assets/studio/js/series-tags.js`

Supporting modules:

- `assets/studio/js/studio-ui.js`

Top-level structure:

- `.seriesTagsPage`
  - page scope for Studio CSS variables
- `.seriesTagsActions`
  - plain right-aligned action row for modal-launch buttons
- `[data-role="series-tags-session-modal-host"]`
  - session modal host
- `[data-role="series-tags-import-modal-host"]`
  - import modal host
- `.tagStudio__panel`
  - shared Studio panel shell around the page
- `#series-tags[data-role="series-tags"]`
  - page root / render target

## Named UI Sections

### Action row

User-facing name:

- series tags actions

DOM / CSS:

- `[data-role="series-tags-actions"]`
- `[data-role="open-session-modal"]`
- `[data-role="open-import-modal"]`
- `.seriesTagsActions`

JS owner:

- `renderActionButtons(state)` in `assets/studio/js/series-tags.js`

Meaning:

- right-aligned launcher row below the page header and above the panel
- `Session` opens the offline-session modal and is enabled only when staged local data exists
- `Import` opens the assignment-import modal and is enabled only when the local server is available

### Session modal

User-facing name:

- offline session modal

DOM / CSS:

- `[data-role="series-tags-session-modal-host"]`
- `[data-role="series-tags-session-modal"]`
- `[data-role="series-tags-session-summary"]`
- `[data-role="series-tags-session-actions"]`
- `[data-role="series-tags-session-result"]`
- `.seriesTagsSession__*`

JS owner:

- `renderSessionModal(state)` in `assets/studio/js/series-tags.js`

Meaning:

- modal hub for staged offline assignment rows across series
- provides `Copy JSON`, `Download JSON`, `Clear session`, and `Close`

### Import modal

User-facing name:

- import assignments modal

DOM / CSS:

- `[data-role="series-tags-import-modal-host"]`
- `[data-role="series-tags-import-modal"]`
- `[data-role="series-tags-session-import"]`
- `[data-role="series-tags-session-review"]`
- `[data-role="series-tags-import-result"]`
- `.seriesTagsSession__*`

JS owner:

- `renderImportModal(state)` in `assets/studio/js/series-tags.js`

Meaning:

- modal flow for assignment import preview/apply
- includes per-series overwrite/skip review plus `Close`

### Table shell

User-facing name:

- series tags table

DOM / CSS:

- `.seriesTags`
- `.seriesTags__head`
- `.seriesTags__rows`
- `.seriesTags__row`

JS owner:

- `renderTable(state)` in `assets/studio/js/series-tags.js`

Meaning:

- the overall review table for series-level tag coverage

### Series column

User-facing name:

- series column

DOM / CSS:

- `.seriesTags__col--title`

Meaning:

- the left column containing the series link/title

### Status column

User-facing name:

- status column

DOM / CSS:

- `.seriesTags__col--count`
- `.tagStudioIndex__statusWrap`
- `.rag`

Meaning:

- the middle column showing the RAG completeness indicator

### Tags column

User-facing name:

- tags column

DOM / CSS:

- `.seriesTags__col--tags`
- `.seriesTags__chipList`

Meaning:

- the right column containing the filtered visible tags for each series
- local staged changes reuse the same chip-caption treatment as the editor:
  - `local` caption for locally added or modified assignments
  - bold struck chip text plus `delete` caption for staged deletions

### Filter controls

User-facing name:

- series tags filters

DOM / CSS:

- `.seriesTags__filters`
- `.tagStudioFilters__allBtn`
- `.tagStudioFilters__groupBtn`
- `.tagStudio__keyInfoBtn`

JS owner:

- `renderFilters(state)`

Meaning:

- the group filter controls rendered above the list head using the shared Studio filter-row layout

## UI Layout and Styling

Primary CSS:

- `assets/studio/css/studio.css`

Shared primitives used:

- `tagStudio__panel`
- `tagStudio__chip`
- `tagStudio__empty`
- `tagStudioFilters__allBtn`
- `tagStudioFilters__groupBtn`

Page-specific classes retained:

- `seriesTags__*` for the table/grid structure

Important note:

- this page keeps a page-specific column grid, but now uses the shared `tagStudioList__*` header-row shell and sort-button treatment

## DOM Rendering and Event Wiring

Page boot:

- `initSeriesTagsPage()`

Main render functions:

- `renderActionButtons(state)`
- `renderSessionModal(state)`
- `renderImportModal(state)`
- `renderTable(state)`
- `renderFilters(state)`
- `buildSeriesRows(state)`

Main event wiring:

- modal launch buttons on the action row
- session actions inside the session modal
- import actions and conflict-resolution controls inside the import modal
- a click handler on `#series-tags` listens for:
  - `button[data-group]`
  - `button[data-sort-key]`

## UI Contract

This page follows the Studio-specific shared UI boundary documented in [Studio UI Framework](/docs/?scope=studio&doc=studio-ui-framework):

- classes define presentation
- `data-role` defines JS selectors when the page needs them
- `data-state` defines active filter state

`assets/studio/js/studio-ui.js` holds the shared role/state/class tokens used by `series-tags.js`.

## State Handling

Primary state lives in:

- `state` object inside `initSeriesTagsPage()`

Key state areas:

- loaded series list
- assignments lookup
- registry lookup
- group descriptions
- offline session payload
- local-server import preview and per-series resolutions
- current `filterGroup`
- current `sortKey`
- current `sortDir`

## Data Access / Query Params / JSON Parsing

Query params:

- none required

Primary data access:

- series list from inline JSON or `series_index.json`, limited to `series_type = primary`
- assignments JSON
- registry JSON
- groups JSON

Loaded through:

- `assets/studio/js/studio-data.js`

## Business Logic

Primary business logic:

- derive assigned tag ids for each series
- compute tag metrics and RAG status
- overlay staged offline rows over repo rows for display
- export/copy/clear the offline session
- preview and apply assignment imports through the local server
- filter displayed tags by group
- sort by series, status, or visible tags

These responsibilities live mainly in:

- `assets/studio/js/series-tags.js`
- shared scoring/config helpers in `assets/studio/js/studio-config.js`

## Change Guidance

If a request refers to:

- “series tags table”
  - start with `.seriesTags`
- “status”
  - start with `.seriesTags__col--count` and `.rag`
- “tags column”
  - start with `.seriesTags__col--tags`
- “filters”
  - start with `.seriesTags__filters`

Clarify with the user when “status” could mean:

- the RAG dot
- the whole status column
- the completeness interpretation rather than just its visual treatment

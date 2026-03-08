# Series Tags

Route:

- `/studio/series-tags/`

Purpose:

- review tags assigned to series

## Page / Template Structure

Primary template:

- `studio/series-tags/index.md`

Page controller:

- `assets/studio/js/series-tags.js`

Top-level structure:

- `.seriesTagsPage`
  - page scope for Studio CSS variables
- `.tagStudio__panel`
  - shared Studio panel shell around the page
- `#series-tags`
  - page mount point

## Named UI Sections

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

- the group filter controls embedded in the table header

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

- this page intentionally keeps a page-specific row model rather than using the shared `tagStudioList__*` shell

## DOM Rendering and Event Wiring

Page boot:

- `initSeriesTagsPage()`

Main render functions:

- `renderTable(state)`
- `renderFilters(state)`

Main event wiring:

- a click handler on `#series-tags` listens for `button[data-group]`

## State Handling

Primary state lives in:

- `state` object inside `initSeriesTagsPage()`

Key state areas:

- loaded series list
- assignments lookup
- registry lookup
- group descriptions
- current `filterGroup`

## Data Access / Query Params / JSON Parsing

Query params:

- none required

Primary data access:

- series list from inline JSON or `series_index.json`
- assignments JSON
- registry JSON
- groups JSON

Loaded through:

- `assets/studio/js/studio-data.js`

## Business Logic

Primary business logic:

- derive assigned tag ids for each series
- compute tag metrics and RAG status
- filter displayed tags by group

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

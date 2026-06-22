---
doc_id: tag-registry
title: Tag Registry
added_date: 2026-03-31
last_updated: 2026-06-22
parent_id: analytics
---
# Tag Registry

Route:

- `/analytics/tag-registry/`

Purpose:

- review and edit canonical tags

## Route Ready State

The page root `#tag-registry` exposes the Analytics route-ready contract:

- `data-analytics-ready` is `false` while config, registry, aliases, assignment, series, and group data load, then `true` after the list or error state is rendered
- `data-analytics-busy` is `true` while import, edit, create, delete, demote, or delete-impact preview work is running
- `data-analytics-mode` is `list`, `import`, or `edit` depending on active modal state
- `data-analytics-service` reports whether the Local Analytics API is available for direct writes
- `data-analytics-record-loaded` is `true` when registry tags are loaded

Successful local-server registry writes send Analytics activity context and append unified activity rows with script purpose `save tag data`.
Covered write actions include registry import, create tag, edit tag, delete tag, and demote tag.

## Page / Template Structure

Static route template:

- `analytics-app/app/frontend/routes/tag-registry.html`

App shell:

- `analytics-app/app/frontend/analytics-shell.html`

Page controller:

- `analytics-app/app/frontend/js/tag-registry.js`

Supporting modules:

- `analytics-app/app/frontend/js/analytics-ui.js`
- `analytics-app/app/frontend/js/tag-registry-domain.js`
- `analytics-app/app/frontend/js/tag-registry-import-mode.js`
- `analytics-app/app/frontend/js/tag-registry-render.js`
- `analytics-app/app/frontend/js/tag-registry-save.js`
- `analytics-app/app/frontend/js/tag-registry-service.js`
- `analytics-app/app/frontend/js/tag-registry-workflow.js`

Top-level structure:

- `.tagRegistryPage`
  - page scope for Studio CSS variables
- `#tag-registry[data-role="tag-registry"]`
  - template-owned registry shell root
- `.seriesTagsActions`
  - top action row shell shared with Series Tags layout pattern
- `[data-role="filters"]`
  - search and key shell
- `[data-role="list"]`
  - list mount area
- `[data-role="modal-host"]`
  - modal mount point used by `tag-registry.js`

## Named UI Sections

### Action row

User-facing name:

- action row

DOM / CSS:

- `.seriesTagsActions`
- `[data-role="open-import-modal"]`
- `[data-role="open-new-tag"]`

JS owner:

- page template for shell markup
- `renderShell(state)` in `analytics-app/app/frontend/js/tag-registry.js` for dynamic labels, refs, and modal DOM

Meaning:

- the top right-aligned action row above the list panel, containing the `Import` modal trigger and the `New tag` action

### Import modal

User-facing name:

- import modal

DOM / CSS:

- `[data-role="open-import-modal"]`
- `[data-role="import-modal"]`
- `[data-role="import-file"]`
- `[data-role="import-mode"]`
- `[data-role="import-btn"]`
- `[data-role="selected-file"]`
- `[data-role="import-result"]`

JS owner:

- `renderShell(state)` in `analytics-app/app/frontend/js/tag-registry.js`
- import-mode availability helpers in `analytics-app/app/frontend/js/tag-registry-import-mode.js`
- import submission handlers in `wireEvents(state)`

Meaning:

- modal-owned import controls for file selection, import mode, submit, and import result text; the modal trigger is disabled when the local server is unavailable

### Search and filters

User-facing name:

- search and filters

DOM / CSS:

- `[data-role="filters"]`
- `.analyticsFilters`
- `[data-role="key"]`
- `[data-role="search"]`
- `.analyticsFilters__key`
- `.analyticsFilters__searchWrap`
- `.analyticsFilters__searchInput`
- `.analyticsFilters__allBtn`
- `.analyticsFilters__groupBtn`

JS owner:

- `renderTagRegistryControls(state)` in `analytics-app/app/frontend/js/tag-registry-render.js`
- search/filter handlers in `wireEvents(state)`

Meaning:

- the row used to filter tags by group and search text

### Registry list shell

User-facing name:

- registry list

DOM / CSS:

- `[data-role="list"]`
- `.analyticsList__head.tagRegistry__head`
- `.analyticsList__rows.tagRegistry__rows`
- `.analyticsList__row.tagRegistry__row`

JS owner:

- `renderTagRegistryList(state)` in `analytics-app/app/frontend/js/tag-registry-render.js`

Meaning:

- the outer list structure for visible registry entries

### Tag column

User-facing name:

- tag column

DOM / CSS:

- `.tagRegistry__tagCol`
- `.tagRegistry__tagActions`
- `.tagRegistry__tagChip`
- `.tagRegistry__tagInlineBtn`
- `.tagRegistry__demoteBtn`

Meaning:

- the left column containing the canonical tag chip and tag-level actions

### Description column

User-facing name:

- description column

DOM / CSS:

- `.tagRegistry__descCol`

Meaning:

- the right column containing the tag description text

### Patch preview modal

User-facing name:

- registry patch preview modal

DOM / CSS:

- `[data-role="patch-modal"]`
- `[data-role="patch-snippet"]`
- shared modal shell classes

### Edit tag modal

User-facing name:

- edit tag modal

DOM / CSS:

- `[data-role="edit-modal"]`
- `[data-role="edit-tag-id"]`
- `[data-role="edit-tag-name"]`
- `[data-role="edit-description"]`
- `[data-role="edit-status"]`

### New tag modal

User-facing name:

- new tag modal

DOM / CSS:

- `[data-role="new-modal"]`
- `[data-role="new-group-key"]`
- `[data-role="new-tag-slug"]`
- `[data-role="new-tag-warning"]`
- `[data-role="new-tag-description"]`
- `[data-role="new-tag-status"]`

### Demote modal

User-facing name:

- demote modal

DOM / CSS:

- `[data-role="demote-modal"]`
- `[data-role="demote-tag-meta"]`
- `[data-role="demote-tag-search"]`
- `[data-role="demote-tag-popup-wrap"]`
- `[data-role="demote-tag-list"]`
- `[data-role="demote-status"]`

### Delete modal

User-facing name:

- delete tag modal

DOM / CSS:

- `[data-role="delete-modal"]`
- `[data-role="delete-tag-meta"]`
- `[data-role="delete-impact"]`
- `[data-role="delete-status"]`
- `.tagRegistryDelete__metaTag`
- `.tagRegistryDelete__metaId`
- `.tagRegistryDelete__impactList`
- `.tagRegistryDelete__impactItem`
- `.tagRegistryDelete__impactValue`

Meaning:

- shows the selected canonical tag as a coloured group pill with its full `tag_id`
- shows affected series as linked titles opening the series tag editor in a new tab
- summarizes alias impact with `aliases updated` and `aliases deleted`

## UI Layout and Styling

Primary CSS:

- `analytics-app/app/assets/css/analytics.css`

Shared primitives used:

- `analyticsToolbar__*`
- `analyticsFilters__*`
- `analyticsList__*`
- `analyticsForm__*`
- `analyticsModal*`

Page-specific classes retained:

- `tagRegistry__*` for row internals, sort buttons, and tag action layout

## DOM Rendering and Event Wiring

Page boot:

- `initTagRegistryPage()`

Main render functions:

- `renderShell(state)`
- `renderTagRegistryControls(state)` in `analytics-app/app/frontend/js/tag-registry-render.js`
- `renderTagRegistryList(state)` in `analytics-app/app/frontend/js/tag-registry-render.js`

Import-mode helpers:

- `syncTagRegistryImportModeFromControl(state)` in `analytics-app/app/frontend/js/tag-registry-import-mode.js`
- `probeTagRegistryImportMode(state)` in `analytics-app/app/frontend/js/tag-registry-import-mode.js`
- `renderTagRegistryImportAvailability(state)` in `analytics-app/app/frontend/js/tag-registry-import-mode.js`

Main event wiring:

- `wireEvents(state)`

The page controller owns:

- shell rendering
- modal visibility
- search/filter/sort wiring
- user-facing mutation result handling

`analytics-app/app/frontend/js/tag-registry-render.js` owns the search/filter controls, group info control, list header, empty state, and registry row markup.
`analytics-app/app/frontend/js/tag-registry-import-mode.js` owns import mode selection state, local write-service availability probing, and import button availability.
`analytics-app/app/frontend/js/tag-registry-workflow.js` owns service-call orchestration, patch fallback result selection, and patch fallback state transitions.

## UI Contract

- classes define presentation
- `data-role` defines JS selectors
- `data-state` and ARIA define runtime state

`analytics-app/app/frontend/js/analytics-ui.js` holds the role selectors plus generated style class tokens used by `tag-registry.js`, `tag-registry-render.js`, `tag-registry-import-mode.js`, and the route-local modal module.

## State Handling

Primary state lives in:

- `state` object in `analytics-app/app/frontend/js/tag-registry.js`

Key state areas:

- loaded tags
- alias key set
- group descriptions
- current filter/sort/search
- import mode / save mode
- selected file
- active modal state for edit/new/demote/delete

Domain helpers live in:

- `analytics-app/app/frontend/js/tag-registry-domain.js`

## Data Access / Query Params / JSON Parsing

Query params:

- none required

Primary data access:

- registry JSON
- aliases JSON
- groups JSON

Loaded through:

- `analytics-app/app/frontend/js/analytics-data.js`

Mutation transport:

- `analytics-app/app/frontend/js/tag-registry-service.js`
- `analytics-app/app/frontend/js/analytics-transport.js`

## Business Logic

Domain logic:

- normalization
- sorting/filtering
- create/demote validation

Save/service logic:

- import parsing
- create/edit/delete/demote mutation flows
- preview generation
- patch fallback generation

These responsibilities are split across:

- `tag-registry-domain.js`
- `tag-registry-import-mode.js`
- `tag-registry-save.js`
- `tag-registry-service.js`
- `tag-registry-workflow.js`

## Change Guidance

If a request refers to:

- “toolbar”
  - start with `.analyticsToolbar` in `tag-registry.js`
- “search”
  - start with `.analyticsFilters` in `analytics-app/app/frontend/js/tag-registry-render.js`
- “list header”
  - start with `.analyticsList__head.tagRegistry__head` in `analytics-app/app/frontend/js/tag-registry-render.js`
- “tag row”
  - start with `.analyticsList__row.tagRegistry__row` in `analytics-app/app/frontend/js/tag-registry-render.js`
- “description column”
  - start with `.tagRegistry__descCol` in `analytics-app/app/frontend/js/tag-registry-render.js`
- “new tag modal”
  - start with `[data-role="new-modal"]`

Clarify with the user when “tag” could mean:

- the tag chip/action column
- the whole registry row
- the canonical tag create/edit/demote/delete workflow

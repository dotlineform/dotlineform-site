---
doc_id: tag-aliases
title: Tag Aliases
added_date: 2026-03-31
last_updated: 2026-05-30
parent_id: analytics
---
# Tag Aliases

Route:

- `/analytics/tag-aliases/`

Purpose:

- review and edit tag aliases

## Route Ready State

The page root `#tag-aliases` exposes the Analytics route-ready contract:

- `data-analytics-ready` is `false` while config, alias, registry, and group data load, then `true` after the list or error state is rendered
- `data-analytics-busy` is `true` while import, edit/create, delete, promote, or demote work is running
- `data-analytics-mode` is `list`, `import`, or `edit` depending on active modal state
- `data-analytics-service` reports whether the Local Analytics API is available for direct writes
- `data-analytics-record-loaded` is `true` when aliases are loaded

Successful local-server alias writes send Analytics activity context and append unified activity rows with script purpose `save tag data`.
Covered write actions include alias import, create alias, edit alias, delete alias, promote alias, and demote tag.

## Page / Template Structure

Primary shell:

- `analytics-app/app/server/analytics_app/analytics_app_views.py`

Page controller:

- `analytics-app/app/frontend/js/tag-aliases.js`

Supporting modules:

- `analytics-app/app/frontend/js/analytics-ui.js`
- `analytics-app/app/frontend/js/tag-aliases-domain.js`
- `analytics-app/app/frontend/js/tag-aliases-save.js`
- `analytics-app/app/frontend/js/tag-aliases-service.js`

Top-level structure:

- `.tagAliasesPage`
  - page scope for Studio CSS variables
- `#tag-aliases[data-role="tag-aliases"]`
  - template-owned aliases shell root
- `.seriesTagsActions`
  - top action row shell shared with Series Tags layout pattern
- `[data-role="filters"]`
  - search and key shell
- `[data-role="list"]`
  - list mount area
- `[data-role="modal-host"]`
  - modal mount point used by `tag-aliases.js`

## Named UI Sections

### Action row

User-facing name:

- action row

DOM / CSS:

- `.seriesTagsActions`
- `[data-role="open-import-modal"]`
- `[data-role="open-new-alias"]`

JS owner:

- page template for shell markup
- `renderShell(state)` in `analytics-app/app/frontend/js/tag-aliases.js` for dynamic labels, refs, and persistent modal DOM

Meaning:

- the top right-aligned action row above the list panel, containing the `Import` modal trigger and the `New alias` action

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

- `renderShell(state)` in `analytics-app/app/frontend/js/tag-aliases.js`
- import handlers in `wireEvents(state)`

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

- `renderControls(state)`
- search/filter handlers in `wireEvents(state)`

### Alias list shell

User-facing name:

- alias list

DOM / CSS:

- `[data-role="list"]`
- `.analyticsList__head.tagAliases__head`
- `.analyticsList__rows.tagAliases__rows`
- `.analyticsList__row.tagAliases__row`

JS owner:

- `renderList(state)`

Meaning:

- the outer list structure for visible alias rows

### Alias column

User-facing name:

- alias column

DOM / CSS:

- `.tagAliases__aliasCol`
- `.tagAliases__aliasBtn`

Meaning:

- the left column showing the alias chip and alias-level actions
- alias chips use the neutral Studio chip style; only the target tag chips carry group color

### Tags column

User-facing name:

- tags column

DOM / CSS:

- `.tagAliases__tagsCol`
- `.tagAliases__tagList`

Meaning:

- the right column showing the resolved target tags for the alias
- header sorting uses the visible target tag labels, with alias as the tie-breaker

### Patch preview modal

User-facing name:

- aliases patch preview modal

DOM / CSS:

- `[data-role="patch-modal"]`
- `[data-role="patch-snippet"]`

### Edit / new alias modal

User-facing name:

- edit alias modal
- new alias modal

DOM / CSS:

- `[data-role="edit-modal"]`
- `[data-role="edit-modal-title"]`
- `[data-role="edit-alias-name"]`
- `[data-role="edit-alias-warning"]`
- `[data-role="edit-alias-description"]`
- `[data-role="edit-tag-search"]`
- `[data-role="edit-tag-popup-wrap"]`
- `[data-role="edit-group-key"]`
- `[data-role="edit-tag-list"]`
- `[data-role="edit-status"]`

Meaning:

- one shared modal shell is used for both edit and create flows

### Promote alias modal

User-facing name:

- promote alias modal

DOM / CSS:

- `[data-role="promotion-modal"]`
- `[data-role="promotion-alias-meta"]`
- `[data-role="promotion-group-key"]`
- `[data-role="promotion-status"]`
- `[data-role="confirm-promotion"]`

Meaning:

- choose the canonical tag group for alias promotion using group chips, then apply the promotion directly after preview when the local server is available

### Demote tag modal

User-facing name:

- demote tag modal

DOM / CSS:

- `[data-role="demote-modal"]`
- `[data-role="demote-tag-meta"]`
- `[data-role="demote-group-key"]`
- `[data-role="demote-tag-search"]`
- `[data-role="demote-tag-popup-wrap"]`
- `[data-role="demote-tag-popup"]`
- `[data-role="demote-tag-list"]`
- `[data-role="demote-status"]`
- `[data-role="confirm-demote"]`

Meaning:

- page-owned modal for demoting a canonical tag to an alias
- target tags are chosen from canonical registry matches using a search popup and removable selected-tag chips
- the search results are tag-only; alias matches are not shown

- page-owned modal shell for choosing the promotion group via group chips before direct preview/apply

### Shared confirm modals

User-facing name:

- delete alias confirmation

DOM / CSS:

- rendered by `analytics-app/app/frontend/js/analytics-modal.js`
- mounted inside `.tagAliasesPage`

Meaning:

- these are transient shared confirm flows rather than persistent page-owned modal shells

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

- `tagAliases__*` for row internals and alias-specific layout
- `tagAliasesEdit__*` for a few edit-modal-specific details

Important note:

- this page uses the shared `analyticsList__*` row/header spacing and line treatment; `tagAliases__*` should stay focused on column grids and alias-specific cell content

## DOM Rendering and Event Wiring

Page boot:

- `initTagAliasesPage()`

Main render functions:

- `renderShell(state)`
- `renderControls(state)`
- `renderList(state)`

Main event wiring:

- `wireEvents(state)`

The page controller owns:

- dynamic inner rendering
- modal visibility for the persistent edit modal
- search/filter/sort wiring
- delegating mutations and preview flows

## UI Contract

This page follows the Analytics UI class boundary documented in [UI Framework Primitives](/docs/?scope=studio&doc=studio-ui-framework-primitives):

- classes define presentation
- `data-role` defines JS selectors
- `data-state` and ARIA define runtime state

`analytics-app/app/frontend/js/analytics-ui.js` holds the role selectors plus generated style class tokens used by `tag-aliases.js`.

## State Handling

Primary state lives in:

- `state` object in `analytics-app/app/frontend/js/tag-aliases.js`

Key state areas:

- loaded aliases
- registry lookup
- group descriptions
- current filter/sort/search
- import mode / save mode
- selected file
- edit-state for create/edit modal flow

Domain helpers live in:

- `analytics-app/app/frontend/js/tag-aliases-domain.js`

## Data Access / Query Params / JSON Parsing

Query params:

- none required

Primary data access:

- aliases JSON
- registry JSON
- groups JSON

Loaded through:

- `analytics-app/app/frontend/js/analytics-data.js`

Mutation transport:

- `analytics-app/app/frontend/js/tag-aliases-service.js`
- `analytics-app/app/frontend/js/analytics-transport.js`

## Business Logic

Domain logic:

- alias normalization
- alias edit validation
- target-tag parsing
- filter/sort behavior

Save/service logic:

- import parsing
- create/edit/delete/promote/demote flows
- preview generation
- patch fallback generation

These responsibilities are split across:

- `tag-aliases-domain.js`
- `tag-aliases-save.js`
- `tag-aliases-service.js`

## Change Guidance

If a request refers to:

- “toolbar”
  - start with `.analyticsToolbar`
- “search”
  - start with `.analyticsFilters`
- “alias list header”
  - start with `.analyticsList__head.tagAliases__head`
- “alias row”
  - start with `.analyticsList__row.tagAliases__row`
- “target tags”
  - start with `.tagAliases__tagsCol` / `.tagAliases__tagList`
- “new alias modal”
  - start with `[data-role="edit-modal"]` in create mode

Clarify with the user when “alias” could mean:

- the alias chip/button in the left column
- the full alias row
- the edit/create workflow
- the transient confirm modal flow for delete

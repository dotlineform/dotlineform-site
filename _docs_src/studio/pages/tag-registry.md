---
doc_id: tag-registry
title: Tag Registry
last_updated: 2026-03-28
parent_id: studio
sort_order: 50
---

# Tag Registry

Route:

- `/studio/tag-registry/`

Purpose:

- review and edit canonical tags

## Page / Template Structure

Primary template:

- `studio/tag-registry/index.md`

Page controller:

- `assets/studio/js/tag-registry.js`

Supporting modules:

- `assets/studio/js/studio-ui.js`
- `assets/studio/js/tag-registry-domain.js`
- `assets/studio/js/tag-registry-save.js`
- `assets/studio/js/tag-registry-service.js`

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
- `renderShell(state)` in `assets/studio/js/tag-registry.js` for dynamic labels, refs, and modal DOM

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

- `renderShell(state)` in `assets/studio/js/tag-registry.js`
- import handlers in `wireEvents(state)`

Meaning:

- modal-owned import controls for file selection, import mode, submit, and import result text; the modal trigger is disabled when the local server is unavailable

### Search and filters

User-facing name:

- search and filters

DOM / CSS:

- `[data-role="filters"]`
- `.tagStudioFilters`
- `[data-role="key"]`
- `[data-role="search"]`
- `.tagStudioFilters__key`
- `.tagStudioFilters__searchWrap`
- `.tagStudioFilters__searchInput`
- `.tagStudioFilters__allBtn`
- `.tagStudioFilters__groupBtn`

JS owner:

- `renderControls(state)`
- search/filter handlers in `wireEvents(state)`

Meaning:

- the row used to filter tags by group and search text

### Registry list shell

User-facing name:

- registry list

DOM / CSS:

- `[data-role="list"]`
- `.tagStudioList__head.tagRegistry__head`
- `.tagStudioList__rows.tagRegistry__rows`
- `.tagStudioList__row.tagRegistry__row`

JS owner:

- `renderList(state)`

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

- `assets/studio/css/studio.css`

Shared primitives used:

- `tagStudioToolbar__*`
- `tagStudioFilters__*`
- `tagStudioList__*`
- `tagStudioForm__*`
- `tagStudioModal*`

Page-specific classes retained:

- `tagRegistry__*` for row internals, sort buttons, and tag action layout

## DOM Rendering and Event Wiring

Page boot:

- `initTagRegistryPage()`

Main render functions:

- `renderShell(state)`
- `renderControls(state)`
- `renderList(state)`

Main event wiring:

- `wireEvents(state)`

The page controller owns:

- dynamic inner rendering
- modal visibility
- search/filter/sort wiring
- delegating mutations to service helpers

## UI Contract

This page follows the Studio-specific shared UI boundary documented in `docs/studio/ui-framework.md`:

- classes define presentation
- `data-role` defines JS selectors
- `data-state` and ARIA define runtime state

`assets/studio/js/studio-ui.js` holds the role selectors plus generated style class tokens used by `tag-registry.js`.

## State Handling

Primary state lives in:

- `state` object in `assets/studio/js/tag-registry.js`

Key state areas:

- loaded tags
- alias key set
- group descriptions
- current filter/sort/search
- import mode / save mode
- selected file
- active modal state for edit/new/demote/delete

Domain helpers live in:

- `assets/studio/js/tag-registry-domain.js`

## Data Access / Query Params / JSON Parsing

Query params:

- none required

Primary data access:

- registry JSON
- aliases JSON
- groups JSON

Loaded through:

- `assets/studio/js/studio-data.js`

Mutation transport:

- `assets/studio/js/tag-registry-service.js`
- `assets/studio/js/studio-transport.js`

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
- `tag-registry-save.js`
- `tag-registry-service.js`

## Change Guidance

If a request refers to:

- “toolbar”
  - start with `.tagStudioToolbar` in `tag-registry.js`
- “search”
  - start with `.tagStudioFilters`
- “list header”
  - start with `.tagStudioList__head.tagRegistry__head`
- “tag row”
  - start with `.tagStudioList__row.tagRegistry__row`
- “description column”
  - start with `.tagRegistry__descCol`
- “new tag modal”
  - start with `[data-role="new-modal"]`

Clarify with the user when “tag” could mean:

- the tag chip/action column
- the whole registry row
- the canonical tag create/edit/demote/delete workflow

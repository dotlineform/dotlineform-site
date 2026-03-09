# Tag Aliases

Route:

- `/studio/tag-aliases/`

Purpose:

- review and edit tag aliases

## Page / Template Structure

Primary template:

- `studio/tag-aliases/index.md`

Page controller:

- `assets/studio/js/tag-aliases.js`

Supporting modules:

- `assets/studio/js/studio-ui.js`
- `assets/studio/js/tag-aliases-domain.js`
- `assets/studio/js/tag-aliases-save.js`
- `assets/studio/js/tag-aliases-service.js`

Top-level structure:

- `.tagAliasesPage`
  - page scope for Studio CSS variables
- `#tag-aliases[data-role="tag-aliases"]`
  - template-owned aliases shell root
- `[data-role="toolbar"]`
  - import/action toolbar shell
- `[data-role="filters"]`
  - search and key shell
- `[data-role="list"]`
  - list mount area
- `[data-role="modal-host"]`
  - modal mount point used by `tag-aliases.js`

## Named UI Sections

### Toolbar

User-facing name:

- toolbar

DOM / CSS:

- `.tagStudioToolbar`
- `.tagStudioToolbar__row`
- `.tagStudioToolbar__field`
- `.tagStudioToolbar__mode`
- `.tagStudioToolbar__selected`
- `.tagStudioToolbar__result`

JS owner:

- page template for shell markup
- `renderShell(state)` in `assets/studio/js/tag-aliases.js` for dynamic labels, refs, and persistent modal DOM

Meaning:

- the top action area containing import controls, save mode, and the “New alias” action

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

### Alias list shell

User-facing name:

- alias list

DOM / CSS:

- `[data-role="list"]`
- `.tagStudioList__head.tagAliases__head`
- `.tagStudioList__rows.tagAliases__rows`
- `.tagStudioList__row.tagAliases__row`

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

### Group tags column

User-facing name:

- group tags column

DOM / CSS:

- `.tagAliases__tagsCol`
- `.tagAliases__tagList`

Meaning:

- the right column showing the resolved target tags for the alias

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

### Shared confirm/form modals

User-facing name:

- delete alias confirmation
- promote alias flow
- demote canonical tag flow

DOM / CSS:

- rendered by `assets/studio/js/studio-modal.js`
- mounted inside `.tagAliasesPage`

Meaning:

- these are transient shared modal-controller flows rather than persistent page-owned modal shells

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

- `tagAliases__*` for row internals and alias-specific layout
- `tagAliasesEdit__*` for a few edit-modal-specific details

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

This page follows the shared Studio UI boundary documented in `docs/studio/ui-framework.md`:

- classes define presentation
- `data-role` defines JS selectors
- `data-state` and ARIA define runtime state

`assets/studio/js/studio-ui.js` holds the role selectors plus generated style class tokens used by `tag-aliases.js`.

## State Handling

Primary state lives in:

- `state` object in `assets/studio/js/tag-aliases.js`

Key state areas:

- loaded aliases
- registry lookup
- group descriptions
- current filter/sort/search
- import mode / save mode
- selected file
- edit-state for create/edit modal flow

Domain helpers live in:

- `assets/studio/js/tag-aliases-domain.js`

## Data Access / Query Params / JSON Parsing

Query params:

- none required

Primary data access:

- aliases JSON
- registry JSON
- groups JSON

Loaded through:

- `assets/studio/js/studio-data.js`

Mutation transport:

- `assets/studio/js/tag-aliases-service.js`
- `assets/studio/js/studio-transport.js`

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
  - start with `.tagStudioToolbar`
- “search”
  - start with `.tagStudioFilters`
- “alias list header”
  - start with `.tagStudioList__head.tagAliases__head`
- “alias row”
  - start with `.tagStudioList__row.tagAliases__row`
- “target tags”
  - start with `.tagAliases__tagsCol` / `.tagAliases__tagList`
- “new alias modal”
  - start with `[data-role="edit-modal"]` in create mode

Clarify with the user when “alias” could mean:

- the alias chip/button in the left column
- the full alias row
- the edit/create workflow
- the transient confirm/form modal flows for delete/promote/demote

---
doc_id: tag-editor
title: Tag Editor
last_updated: 2026-03-28
parent_id: tagging
sort_order: 40
---

# Tag Editor

Route:

- `/studio/series-tag-editor/`
- required query param: `?series=<series_id>`
- example: `/studio/series-tag-editor/?series=curve-poems`

Purpose:

- review and edit series-level tag assignments plus per-work override tags for one series
- preserve optional historical alias metadata when a tag is added from an alias suggestion, without surfacing that metadata in the UI

## Page / Template Structure

Primary template:

- `studio/series-tag-editor/index.md`

Page boot module:

- `assets/studio/js/series-tag-editor-page.js`

Editor controller:

- `assets/studio/js/tag-studio.js`

Supporting modules:

- `assets/studio/js/studio-ui.js`
- `assets/studio/js/tag-studio-domain.js`
- `assets/studio/js/tag-assignments-offline.js`
- `assets/studio/js/tag-studio-save.js`

Top-level structure in the page template:

- `#seriesTagEditorRoot.tagStudioPage`
  - page shell and runtime data attributes
- `.tagStudioPage__header`
  - two-column series header area
- `.tagStudioPage__media`
  - primary image column
- `.tagStudioPage__context`
  - series metadata column
- `.tagStudioPage__editor`
  - container for the interactive tag editor shell
- `#tag-studio.tagStudio[data-role="series-tag-editor"]`
  - template-owned editor shell root
- `[data-role="editor-shell"]`
  - template-owned editor panel shell
- `[data-role="modal-host"]`
  - modal mount point used by `tag-studio.js`

## Named UI Sections

### Series header

User-facing name:

- series header

DOM / CSS:

- `.tagStudioPage__header`

JS owner:

- `assets/studio/js/series-tag-editor-page.js`

This section contains:

- primary image column
- series metadata column

### Primary image

User-facing name:

- primary image

DOM / CSS:

- `#seriesTagEditorMedia.tagStudioPage__media`
- `#seriesTagEditorMediaLink`
- `#seriesTagEditorMediaImg.tagStudioPage__mediaImg`
- `#seriesTagEditorMediaCaption.tagStudioPage__mediaCaption`

JS owner:

- `renderPrimaryMedia(...)`
- `syncHeaderMediaForWork(...)`
  in `assets/studio/js/series-tag-editor-page.js`

Meaning:

- the image area in column 1 of the series header
- shows the series primary work by default
- can switch to the currently selected work while editing
- shows a caption under the image as `work_id - title` and updates when the displayed work changes

### Series metadata

User-facing name:

- series metadata

DOM / CSS:

- `.tagStudioPage__context`
- `.tagStudioPage__context--meta`
- `.page__caption.page__metaList`
- `#seriesTagEditorTitle`
- `#seriesTagEditorCat`
- `#seriesTagEditorYear`
- `#seriesTagEditorYearDisplay`
- `#seriesTagEditorSortFields`
- `#seriesTagEditorPrimaryWork`
- `#seriesTagEditorFolders`
- `#seriesTagEditorNotes`

JS owner:

- `initSeriesTagEditorPage()`
  in `assets/studio/js/series-tag-editor-page.js`

Meaning:

- the field list in column 2 of the series header
- this now uses the shared unboxed metadata pattern from the main site rather than a Studio-specific boxed panel treatment

### Editor panel

User-facing name:

- tag editor

DOM / CSS:

- `.tagStudioPage__editor`
- `#tag-studio[data-role="series-tag-editor"]`
- `[data-role="editor-shell"]`

JS owner:

- page template for shell markup
- `renderShell(state)` in `assets/studio/js/tag-studio.js` for dynamic labels, refs, and modal DOM

Meaning:

- the interactive editing area with template-owned outer structure and JS-owned dynamic content

### Works

User-facing name:

- works

DOM / CSS:

- `[data-role="work-section"]`
- `[data-role="work-input"]`
- `[data-role="selected-work"]`
- `[data-role="work-popup"]`
- `[data-role="work-popup-list"]`

JS owner:

- `renderShell(state)`
- work-related handlers in `wireEvents(state)`
  in `assets/studio/js/tag-studio.js`

Meaning:

- the work search box and currently selected works area

### Context hint

User-facing name:

- context hint

DOM / CSS:

- `[data-role="message-section"]`
- `[data-role="context-hint"]`
- `.tagStudio__contextHint`
- `[data-role="status"]`
- `[data-role="save-warning"]`
- `[data-role="save-result"]`

JS owner:

- `renderContextHint(state)`
  in `assets/studio/js/tag-studio.js`

Meaning:

- the line explaining whether edits apply to the series or to selected works
- with no active work, this section should make it clear that the editor is in series-tag mode
- the editor now presents context, status, warning, and save-result lines inside one shared message container rather than as separate boxes

### Group rows

User-facing name:

- group rows

DOM / CSS:

- `[data-role="groups-section"]`
- `[data-role="groups"]`
- `.tagStudioGroups`
- `.tagStudioGroupRow`

JS owner:

- group rendering functions in `assets/studio/js/tag-studio.js`

Meaning:

- the visible rows of tag chips grouped by `subject`, `domain`, `form`, and `theme`
- the group-name anchor for each row now uses the same coloured pill treatment as other Studio group-name displays
- with no active work, these rows are editable series tags
- with an active work, inherited series tags become monochrome context chips and work override tags remain editable
- in offline mode, locally changed assignments show a caption below the chip and bold tag text
- pending deletions remain visible as bold struck chips with a `delete` caption and a `⤺` restore control

### Tag input row

User-facing name:

- tag input row

DOM / CSS:

- `[data-role="search-section"]`
- `[data-role="tag-input"]`
- `[data-role="add-tag"]`
- `[data-role="save"]`
- `[data-role="save-mode"]`

JS owner:

- `renderShell(state)`
- input/save handlers in `wireEvents(state)`

Meaning:

- the main row used to add tags and save changes
- with no active work, this row adds series tags
- with an active work, this row adds work-only overrides

### Suggestions popup

User-facing name:

- tag suggestions popup

DOM / CSS:

- `[data-role="popup"]`
- `[data-role="popup-list"]`
- `.tagStudio__popup`
- `.tagStudioSuggest__*`

JS owner:

- popup rendering functions in `assets/studio/js/tag-studio.js`

Meaning:

- the autocomplete area for canonical tags, aliases, and work suggestions

## UI Contract

This page follows the Studio-specific shared UI boundary documented in `docs/studio/ui-framework.md`:

- classes define presentation
- `data-role` defines JS selectors
- `data-state` and ARIA define runtime state

`assets/studio/js/studio-ui.js` holds the role selectors plus the generated style class tokens used by `tag-studio.js`.

### Status and save feedback

User-facing name:

- editor status
- save warning
- save result

DOM / CSS:

- `[data-role="status"]` / `.tagStudio__status`
- `[data-role="save-warning"]` / `.tagStudio__saveWarning`
- `[data-role="save-result"]` / `.tagStudio__saveResult`

JS owner:

- status rendering helpers in `assets/studio/js/tag-studio.js`

### Manual patch modal

User-facing name:

- patch preview modal

DOM / CSS:

- `[data-role="modal"]`
- `[data-role="modal-tags"]`
- `[data-role="modal-snippet"]`
- `[data-role="copy-snippet"]`
- shared shell from `tagStudioModal` / `tagStudioModal__*`

JS owner:

- modal shell in `renderShell(state)`
- open/close/copy handling in `assets/studio/js/tag-studio.js`

Meaning:

- fallback/manual inspection modal for resolved tag-assignment payloads and patch guidance
- not the primary offline-save workflow

## UI Layout and Styling

Primary CSS file:

- `assets/studio/css/studio.css`

Relevant shared classes:

- `.tagStudioPage__*`
- `.tagStudio__panel`
- `.tagStudio__inputRow`
- `.tagStudio__input`
- `.tagStudio__button`
- `.tagStudio__chip`
- `.tagStudio__popup`
- `.tagStudio__status`
- `.tagStudioModal*`

Layout model:

- the page header is a two-column layout on larger screens
- the editor is a panel rendered below the header
- the editor itself uses stacked sections rather than a table/list shell

## DOM Rendering and Event Wiring

Page boot:

- `initSeriesTagEditorPage()` in `assets/studio/js/series-tag-editor-page.js`

Editor boot:

- `initTagStudio()` in `assets/studio/js/tag-studio.js`

Main render functions:

- `renderShell(state)`
- `renderAll(state)`

Main event wiring:

- `wireEvents(state)`

Important event integration:

- `series-tag-editor:selected-work-change`
  - emitted by the editor state flow
  - consumed by `series-tag-editor-page.js` to update the primary image

## State Handling

Primary page state:

- series metadata and primary-image state live in `series-tag-editor-page.js`

Primary editor state:

- editor state object is created by `buildState(...)` in `tag-studio.js`

Key editor state areas:

- selected works
- active work
- resolved series entries
- per-work entries
- save mode
- offline session baseline and staged-series metadata
- modal snippet/status fields

Business/state helpers live in:

- `assets/studio/js/tag-studio-domain.js`

## Data Access / Query Params / JSON Parsing

Query params:

- `series`
  - required page input
- `works`
  - selected work ids persisted by the editor
- `active`
  - active work id persisted by the editor

Page data fetches:

- series index JSON in `series-tag-editor-page.js`
- work detail JSON for header media in `series-tag-editor-page.js`

Editor data fetches:

- registry
- aliases
- assignments
- series index
- works index

These are loaded through:

- `assets/studio/js/studio-data.js`

## Business Logic

Primary business logic modules:

- `assets/studio/js/tag-studio-domain.js`
- `assets/studio/js/tag-studio-save.js`

Business responsibilities include:

- tag normalization and resolution
- alias resolution
- work-state diffing
- persisted assignment shape conversion
- save/persist mode handling
- offline-session staging and baseline overlay
- local-server availability re-probe on page return/focus for staged-series notice
- patch snippet generation for fallback/manual inspection only

## Change Guidance

If a change request refers to:

- “primary image”
  - start with `#seriesTagEditorMedia` and `series-tag-editor-page.js`
- “series metadata”
  - start with `.tagStudioPage__context` and `series-tag-editor-page.js`
- “works”
  - start with `.tagStudio__inputRow--work` and selected-work rendering in `tag-studio.js`
- “tag suggestions”
  - start with `.tagStudio__popup` / `.tagStudioSuggest__*`
- “save modal”
  - start with the shared modal shell in `tag-studio.js` plus shared modal styles in `studio.css`

Clarify with the user when a request could mean:

- page header metadata vs editor panel metadata
- selected-work UI vs work-specific tag chips
- context hint vs save/status messages
